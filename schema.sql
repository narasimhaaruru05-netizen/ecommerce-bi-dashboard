CREATE DATABASE IF NOT EXISTS ecommerce_bi;
USE ecommerce_bi;

CREATE TABLE products (
    product_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category     VARCHAR(50)  NOT NULL
);

CREATE TABLE orders (
    order_id     INT AUTO_INCREMENT PRIMARY KEY,
    order_date   DATE NOT NULL,
    order_status ENUM('Completed','Cancelled','Returned') NOT NULL,
    region       VARCHAR(50) NOT NULL
);

CREATE TABLE order_items (
    item_id       INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT NOT NULL,
    product_id    INT NOT NULL,
    quantity      INT NOT NULL CHECK (quantity > 0),
    unit_price    DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    discount      DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
    return_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (return_amount >= 0),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);