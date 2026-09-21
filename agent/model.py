import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langgraph.prebuilt import create_react_agent

load_dotenv()


# ============================================================
# API KEYS
# ============================================================

# agent/model.py:16-18 add
Mistral_API_key = os.getenv("Mistral_API_key")
Mistral_API_key2 = os.getenv("Mistral_API_key2")

# agent/model.py:24-35 replace MODELS
MODELS = [
    {
        "name": "open-mistral-nemo",
        "base_url": "https://api.mistral.ai/v1",
        "api_key": Mistral_API_key
    },
    {
        "name": "mistral-tiny",
        "base_url": "https://api.mistral.ai/v1",
        "api_key": Mistral_API_key2
    }
]


_current_index = 0


# ============================================================
# RATE LIMIT DETECTION
# ============================================================

def _is_rate_limit(e):
    msg = str(e).lower()

    return (
        "rate limit" in msg
        or "reached limit" in msg
        or "quota" in msg
        or "429" in msg
        or "too many" in msg
        or "1300" in msg
        or "connection" in msg
        or "getaddrinfo" in msg
        or "timed out" in msg
    )


# ============================================================
# GET INITIAL MODEL
# ============================================================

def get_model():

    global _current_index

    for i in range(len(MODELS)):

        idx = (i + _current_index) % len(MODELS)

        m = MODELS[idx]

        if not m["api_key"]:
            print(
                f"Skipping {m['name']} — no API key set"
            )
            continue

        try:

            model = ChatOpenAI(
                model=m["name"],
                base_url=m["base_url"],
                api_key=m["api_key"],
                model_kwargs={"parallel_tool_calls": False},
                temperature=0,
            )

            print(
                f"Using model: {m['name']} "
                f"(key #{idx + 1})"
            )

            _current_index = (idx + 1) % len(MODELS)

            return model

        except Exception as e:

            print(
                f"Model {m['name']} init failed: {e}"
            )

    raise Exception("All models failed!")


# ============================================================
# ROTATE MODEL
# ============================================================

def get_model_rotated():

    global _current_index

    for i in range(len(MODELS)):

        idx = (i + _current_index) % len(MODELS)

        m = MODELS[idx]

        if not m["api_key"]:
            continue

        try:

            model = ChatOpenAI(
                model=m["name"],
                base_url=m["base_url"],
                api_key=m["api_key"],
                model_kwargs={"parallel_tool_calls": False},
                temperature=0,
            )

            print(
                f"Using model: {m['name']} "
                f"(key #{idx + 1})"
            )

            _current_index = (idx + 1) % len(MODELS)

            return model

        except Exception as e:

            print(
                f"Model {m['name']} failed: {e}"
            )
            continue

    raise Exception("All models failed!")


# Initial model
model = get_model()


# ============================================================
# OUTPUT SCHEMA
# ============================================================

class ANSWER(BaseModel):

    answer: str = Field(
        description="One clear concise response line for simple answers"
    )

    items: list[str] = Field(
        default=[],
        description=(
            "List of items when returning multiple results, "
            "max 10 items. Each item on one line."
        )
    )

    status: str = Field(
        default="success",
        description="success, error, or not_found"
    )

    @classmethod
    def format_instructions(cls) -> str:

        return """
Return only raw JSON with no markdown, no backticks, no code fences.

Schema:

{
    "answer": "string — one clear response line",
    "items": ["list of strings — only when returning multiple results"],
    "status": "string — success, error, or not_found"
}

Example:

{"answer": "We have 2 Brake Calipers in stock", "items": [], "status": "success"}
"""


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are CURT's inventory manager assistant for the Cairo University
Racing Team (CURT), a Formula Student team that designs and builds
a race car every year.

Your job is to help team members manage and query the parts inventory.

## Rules

1. ALWAYS call the appropriate database tool before answering.
   Never answer inventory questions from memory or from this prompt.

2. Even if you think you know the answer, call the database tool first
   and answer from its result only.

3. If a tool returns no results, say clearly:
   "I couldn't find [item] in the inventory."

4. To list categories, call get_all_categories() which returns the
   unique categories directly.

5. NEVER use placeholders like [Engine Location] or [Car Name].
   Only use exact values returned by the tool.

6. For DELETE operations, always confirm with the user before executing.

7. You only manage CURT's inventory.
   Do not answer unrelated questions.

8. If the user asks something outside your scope, say:
   "I can only help with CURT's inventory management."

9. Call exactly ONE database tool per turn. Do not chain multiple tool calls in the same turn. After the first tool result, answer immediately.

## Tool Routing

- "where is" / location -> get_part_status
- "how many" / quantity -> get_part_info
- "list all items in <category>" -> get_by_category
- "show all parts" -> get_all_parts
- categories list -> get_all_categories
- orders/supplier -> get_orders_by_* / get_supplier_by_*

## Response Style

- Be concise and clear.
- Use structured output when listing multiple items.
- Always include relevant details like quantity, location,
  condition, or status when available.
- If an operation succeeds, confirm it clearly:
  "Part updated successfully" or "Order added successfully".
- If an operation fails, explain why clearly.

## Output Format

{format_instructions}
"""


# ============================================================
# CHATBOT
# ============================================================

MAX_HISTORY = 5


async def Chatbot(
    user_input: str,
    conversation_history: list
):

    # --------------------------------------------------------
    # MCP DATABASE CLIENT
    # --------------------------------------------------------

    client = MultiServerMCPClient({

        "DATABASE_TOOLS": {

            "command": "python",

            "args": [
                os.path.abspath(
                    "agent/tools/databaseserver/databasetools.py"
                )
            ],

            "transport": "stdio"
        }
    })


    # Get database tools
    tools = await client.get_tools()


    # --------------------------------------------------------
    # OUTPUT PARSER
    # --------------------------------------------------------

    parser = JsonOutputParser(
        pydantic_object=ANSWER
    )

    format_instructions = ANSWER.format_instructions()


    # --------------------------------------------------------
    # TRY MODELS - fresh model per request to match backend global loop
    # --------------------------------------------------------

    current_model = get_model()

    for attempt in range(len(MODELS)):

        # Create agent using current model
        agent = create_react_agent(

            model=current_model,

            tools=tools,

            prompt=SYSTEM_PROMPT.format(
                format_instructions=format_instructions
            )
        )


        try:

            # ------------------------------------------------
            # BUILD MESSAGES
            # ------------------------------------------------

            messages = conversation_history[-MAX_HISTORY:]

            messages.append({
                "role": "user",
                "content": user_input
            })


            # ------------------------------------------------
            # RUN AGENT
            # ------------------------------------------------

            response = await agent.ainvoke(
                {"messages": messages},
                config={"recursion_limit": 8},
            )


            # ------------------------------------------------
            # GET ASSISTANT RESPONSE
            # ------------------------------------------------

            assistant_message = (
                response["messages"][-1].content
            )


            # ------------------------------------------------
            # SAVE HISTORY
            # ------------------------------------------------

            conversation_history.append({
                "role": "user",
                "content": user_input
            })

            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })


            # ------------------------------------------------
            # RETURN
            # ------------------------------------------------

            return (
                assistant_message,
                conversation_history
            )


        except Exception as e:

            # ------------------------------------------------
            # RATE LIMIT → ROTATE MODEL
            # ------------------------------------------------

            if _is_rate_limit(e):

                print(
                    f"Rate limit hit. "
                    f"Rotating model "
                    f"({attempt + 1}/{len(MODELS)})..."
                )

                current_model = get_model_rotated()

            else:

                # Other errors should not silently
                # switch models.
                raise


    # --------------------------------------------------------
    # ALL MODELS FAILED
    # --------------------------------------------------------

    raise Exception("All models exhausted!")