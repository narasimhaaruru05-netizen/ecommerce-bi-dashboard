USE ecommerce_bi;

INSERT INTO products (product_name, category) VALUES
('Wireless Mouse','Electronics'), ('Bluetooth Headphones','Electronics'),
('Cotton T-Shirt','Clothing'),    ('Denim Jeans','Clothing'),
('Notebook Pack','Stationery'),   ('Ball Pen Set','Stationery'),
('Water Bottle','Home'),          ('Desk Lamp','Home');

INSERT INTO orders (order_date, order_status, region) VALUES
('2026-01-05','Completed','North'), ('2026-01-18','Completed','South'),
('2026-02-02','Completed','East'),  ('2026-02-14','Cancelled','West'),
('2026-02-20','Completed','North'), ('2026-03-03','Completed','South'),
('2026-03-15','Returned','East'),   ('2026-03-28','Completed','West'),
('2026-04-04','Completed','North'), ('2026-04-19','Completed','South'),
('2026-05-07','Completed','East'),  ('2026-05-22','Completed','West');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, return_amount) VALUES
(1,1,2,599.00,50.00,0),   (1,5,5,60.00,0,0),
(2,3,3,450.00,0,0),       (2,7,2,350.00,25.00,0),
(3,2,1,1999.00,100.00,0), (3,6,4,40.00,0,0),
(4,4,2,1200.00,0,0),
(5,8,1,899.00,0,0),       (5,1,1,599.00,0,0),
(6,3,2,450.00,0,0),       (6,5,10,60.00,30.00,0),
(7,2,1,1999.00,0,1999.00),
(8,4,1,1200.00,100.00,0), (8,7,3,350.00,0,0),
(9,1,3,599.00,0,0),       (9,6,6,40.00,0,0),
(10,8,2,899.00,80.00,0),
(11,2,2,1999.00,200.00,0),(11,3,4,450.00,0,0),
(12,4,2,1200.00,0,0),     (12,5,8,60.00,0,0);