CREATE TABLE CORE_PART_INFO (
    part_number TEXT PRIMARY KEY, --manufacture number--
    part_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1 CHECK (quantity >= 0),
    category TEXT CHECK (category IN (
        'Aero', 'Suspension', 'Brakes', 'Steering', 'Powertrain', 
        'Chassis', 'Safety', 'Wheels & Tires', 'Cooling', 'Electronics'
    )),
    description TEXT,
    manufacturer TEXT --who MADE the part--
);

CREATE TABLE SUPPLIER_INFO (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT CHECK (email LIKE '%@%'),
    phone_number TEXT,
    website TEXT,
    governorate TEXT
);

CREATE TABLE PART (
    part_id TEXT PRIMARY KEY, -- unique number for the part--
    part_number TEXT NOT NULL,
    car_position TEXT,
    compatible_with TEXT,
    FOREIGN KEY (part_number) REFERENCES CORE_PART_INFO(part_number) ON DELETE CASCADE
);

CREATE TABLE PHYSICAL_SPECS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT NOT NULL,
    weight_kg REAL CHECK (weight_kg >= 0),
    material TEXT,
    dimensions TEXT,
    color TEXT,
    FOREIGN KEY (part_number) REFERENCES CORE_PART_INFO(part_number) ON DELETE CASCADE
);

CREATE TABLE ORDERS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT NOT NULL,
    supplier_id INTEGER,
    quantity INTEGER CHECK (quantity >= 0),
    total_cost REAL CHECK (total_cost >= 0),
    order_date DATE,
    category TEXT CHECK (category IN (
        'Sponsorship', 'Club Budget', 'Competition', 
        'R&D', 'Maintenance', 'Donation'
    )),
    status TEXT CHECK (status IN (
        'Pending', 'Ordered', 'Delivered', 'Cancelled'
    )),
    FOREIGN KEY (part_number) REFERENCES CORE_PART_INFO(part_number),
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIER_INFO(id)
);

CREATE TABLE PART_SUPPLIER (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT NOT NULL,
    supplier_id INTEGER,
    lead_time_days INTEGER CHECK (lead_time_days >= 0),
    unit_cost REAL CHECK (unit_cost >= 0),
    preferred BOOLEAN,
    FOREIGN KEY (part_number) REFERENCES CORE_PART_INFO(part_number) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIER_INFO(id) ON DELETE CASCADE
);

CREATE TABLE LIFECYCLE_TRACKING (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id TEXT,
    date_acquired DATE,
    last_inspection_date DATE,
    next_inspection_due DATE,
    usage_cycles INTEGER CHECK (usage_cycles >= 0),
    max_usage_cycles INTEGER CHECK (max_usage_cycles >= 0),
    critical_part BOOLEAN,
    FOREIGN KEY (part_id) REFERENCES PART(part_id) ON DELETE CASCADE
);

CREATE TABLE STATUS_CONDITION (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id TEXT,
    condition TEXT CHECK (condition IN (
        'New', 'Used', 'Damaged', 'Under Repair'
    )),
    status TEXT CHECK (status IN (
        'Available', 'In Use', 'Reserved', 'Scrapped'
    )),
    location TEXT,
    assigned_to TEXT,
    FOREIGN KEY (part_id) REFERENCES PART(part_id) ON DELETE CASCADE
);
CREATE TRIGGER update_quantity_on_insert
AFTER INSERT ON PART
FOR EACH ROW
BEGIN
    UPDATE CORE_PART_INFO
    SET quantity = (
    SELECT COUNT(*) FROM PART
    WHERE PART.part_number = CORE_PART_INFO.part_number
    );
END;

CREATE TRIGGER update_quantity_on_delete
AFTER DELETE ON PART
FOR EACH ROW
BEGIN
    UPDATE CORE_PART_INFO
    SET quantity = (
    SELECT COUNT(*) FROM PART
    WHERE PART.part_number = CORE_PART_INFO.part_number
    );
END;

INSERT INTO CORE_PART_INFO (part_number, part_name, quantity, category, description, manufacturer)
VALUES
('WNG-F-001', 'Front Wing Assembly', 2, 'Aero', 'Carbon fiber front wing', 'In-house'),
('WNG-R-001', 'Rear Wing',           2, 'Aero', 'Adjustable rear wing with DRS', 'In-house'),
('BRK-C-001', 'Brake Caliper',       2, 'Brakes', 'Four-piston caliper', 'Brembo'),
('BRK-D-001', 'Brake Disc',          2, 'Brakes', 'Ventilated steel disc', 'Brembo'),
('SUS-A-001', 'Suspension Arm',      2, 'Suspension', 'Double wishbone upper arm', 'In-house'),
('STR-R-001', 'Steering Rack',       1, 'Steering', 'Rack and pinion assembly', 'Woodward'),
('PWR-E-001', 'Engine',              1, 'Powertrain', 'Honda CBR600RR engine', 'Honda'),
('CHS-M-001', 'Monocoque',           1, 'Chassis', 'Carbon fiber monocoque chassis', 'In-house'),
('ELC-E-001', 'ECU',                 1, 'Electronics', 'Engine control unit', 'MoTeC'),
('WHL-R-001', 'Rim Set',             2, 'Wheels & Tires', '13 inch aluminum rims set of 4', 'OZ Racing');

INSERT INTO SUPPLIER_INFO (name, contact_name, email, phone_number, website, governorate)
VALUES
('Brembo', 'Marco Rossi', 'marco@brembo.com', '+39-035-6061', 'www.brembo.com', 'Cairo'),
('Honda Egypt', 'Ahmed Samir', 'ahmed@honda-eg.com', '+20-100-1234567', 'www.honda.com.eg', 'Cairo'),
('MoTeC', 'James Carter', 'james@motec.com.au', '+61-3-9761-5050', 'www.motec.com.au', 'Giza'),
('OZ Racing', 'Luca Bianchi', 'luca@ozracing.com', '+39-0423-669100', 'www.ozracing.com', 'Alexandria'),
('Woodward', 'Sarah Mills', 'sarah@woodward.com', '+1-970-482-5811', 'www.woodward.com', 'Cairo');

INSERT INTO PART (part_id, part_number, car_position, compatible_with)
VALUES
('PRT-001', 'WNG-F-001', 'Front', '2024 CURT-01'),
('PRT-002', 'WNG-R-001', 'Rear', '2024 CURT-01'),
('PRT-003', 'BRK-C-001', 'Front Left', '2024 CURT-01'),
('PRT-004', 'BRK-C-001', 'Front Right', '2024 CURT-01'),
('PRT-005', 'BRK-D-001', 'Front Left', '2024 CURT-01'),
('PRT-006', 'BRK-D-001', 'Front Right', '2024 CURT-01'),
('PRT-007', 'SUS-A-001', 'Front Left', '2024 CURT-01'),
('PRT-008', 'SUS-A-001', 'Front Right', '2024 CURT-01'),
('PRT-009', 'STR-R-001', 'Center', '2024 CURT-01'),
('PRT-010', 'PWR-E-001', 'Center Rear', '2024 CURT-01'),
('PRT-011', 'CHS-M-001', 'Full Car', '2024 CURT-01'),
('PRT-012', 'ELC-E-001', 'Cockpit', '2024 CURT-01'),
('PRT-013', 'WHL-R-001', 'All Corners', '2024 CURT-01');

INSERT INTO PART_SUPPLIER (part_number, supplier_id, lead_time_days, unit_cost, preferred)
VALUES
('WNG-F-001', 1, 7,  250.00, 1),
('WNG-R-001', 1, 7,  300.00, 1),
('BRK-C-001', 1, 14, 420.00, 1),
('BRK-D-001', 1, 14, 180.00, 1),
('SUS-A-001', 2, 10, 95.00,  1),
('STR-R-001', 5, 21, 530.00, 1),
('PWR-E-001', 2, 30, 2200.00,1),
('CHS-M-001', 3, 45, 4500.00,1),
('ELC-E-001', 3, 20, 1800.00,1),
('WHL-R-001', 4, 10, 320.00, 1);

INSERT INTO PHYSICAL_SPECS (part_number, weight_kg, material, dimensions, color)
VALUES
('WNG-F-001', 3.2,  'Carbon Fiber',  '1200x300x150mm', 'Black'),
('WNG-R-001', 4.1,  'Carbon Fiber',  '900x400x200mm',  'Black'),
('BRK-C-001', 1.8,  'Aluminum',      '180x120x80mm',   'Red'),
('BRK-D-001', 2.5,  'Steel',         '280x28mm',       'Silver'),
('SUS-A-001', 0.9,  'Steel',         '450x40x30mm',    'Black'),
('STR-R-001', 2.1,  'Aluminum',      '350x80x60mm',    'Silver'),
('PWR-E-001', 64.0, 'Steel/Aluminum','530x380x450mm',  'Black'),
('CHS-M-001', 38.0, 'Carbon Fiber',  '2800x600x500mm', 'Black'),
('ELC-E-001', 0.6,  'PCB/Aluminum',  '180x120x40mm',   'Black'),
('WHL-R-001', 3.8,  'Aluminum',      '330x178mm',      'Silver');

INSERT INTO ORDERS (part_number, supplier_id, quantity, total_cost, order_date, category, status)
VALUES
('WNG-F-001', 1, 2, 500.00,  '2024-01-10', 'Sponsorship',  'Delivered'),
('WNG-R-001', 1, 2, 600.00,  '2024-01-10', 'Sponsorship',  'Delivered'),
('BRK-C-001', 1, 4, 1680.00, '2024-02-05', 'Club Budget',  'Delivered'),
('BRK-D-001', 1, 4, 720.00,  '2024-02-05', 'Club Budget',  'Delivered'),
('SUS-A-001', 2, 4, 380.00,  '2024-02-20', 'Club Budget',  'Delivered'),
('STR-R-001', 5, 1, 530.00,  '2024-03-01', 'Competition',  'Delivered'),
('PWR-E-001', 2, 1, 2200.00, '2024-03-15', 'Sponsorship',  'Delivered'),
('CHS-M-001', 3, 1, 4500.00, '2024-04-01', 'Sponsorship',  'Delivered'),
('ELC-E-001', 3, 1, 1800.00, '2024-04-10', 'Club Budget',  'Delivered'),
('WHL-R-001', 4, 2, 640.00,  '2024-05-01', 'Maintenance',  'Delivered');

INSERT INTO STATUS_CONDITION (part_id, condition, status, location, assigned_to)
VALUES
('PRT-001', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-002', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-003', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-004', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-005', 'Used',       'In Use',    'Car',        '2024 CURT-01'),
('PRT-006', 'Used',       'In Use',    'Car',        '2024 CURT-01'),
('PRT-007', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-008', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-009', 'Used',       'In Use',    'Car',        '2024 CURT-01'),
('PRT-010', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-011', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-012', 'New',        'In Use',    'Car',        '2024 CURT-01'),
('PRT-013', 'New',        'In Use',    'Car',        '2024 CURT-01');

INSERT INTO LIFECYCLE_TRACKING (part_id, date_acquired, last_inspection_date, next_inspection_due, usage_cycles, max_usage_cycles, critical_part)
VALUES
('PRT-001', '2024-01-15', '2024-06-01', '2024-09-01', 12,  50,  0),
('PRT-002', '2024-01-15', '2024-06-01', '2024-09-01', 12,  50,  0),
('PRT-003', '2024-02-10', '2024-06-01', '2024-09-01', 20,  100, 1),
('PRT-004', '2024-02-10', '2024-06-01', '2024-09-01', 20,  100, 1),
('PRT-005', '2024-02-10', '2024-06-01', '2024-09-01', 20,  80,  1),
('PRT-006', '2024-02-10', '2024-06-01', '2024-09-01', 20,  80,  1),
('PRT-007', '2024-02-25', '2024-06-01', '2024-09-01', 15,  200, 0),
('PRT-008', '2024-02-25', '2024-06-01', '2024-09-01', 15,  200, 0),
('PRT-009', '2024-03-05', '2024-06-01', '2024-09-01', 18,  150, 1),
('PRT-010', '2024-03-20', '2024-06-01', '2024-09-01', 10,  500, 1),
('PRT-011', '2024-04-05', '2024-06-01', '2024-09-01', 10,  100, 1),
('PRT-012', '2024-04-15', '2024-06-01', '2024-09-01', 10,  300, 1),
('PRT-013', '2024-05-05', '2024-06-01', '2024-09-01', 8,   200, 0);