-- Drop tables if they exist (clean start)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS customers;

-- Create customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

-- Create books table
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    price NUMERIC(6,2) NOT NULL
);

-- Create orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id) ON DELETE CASCADE,
    order_date DATE NOT NULL
);

-- Create order_items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
    book_id INTEGER REFERENCES books(book_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

-- Insert dummy customers
INSERT INTO customers (name, email) VALUES
('Alice Johnson', 'alice@example.com'),
('Bob Smith', 'bob@example.com'),
('Charlie Brown', 'charlie@example.com');

-- Insert dummy books
INSERT INTO books (title, author, price) VALUES
('The Great Gatsby', 'F. Scott Fitzgerald', 10.99),
('1984', 'George Orwell', 8.99),
('To Kill a Mockingbird', 'Harper Lee', 9.99),
('The Hobbit', 'J.R.R. Tolkien', 12.50),
('Sapiens', 'Yuval Noah Harari', 15.00);

-- Insert dummy orders
INSERT INTO orders (customer_id, order_date) VALUES
(1, '2023-10-01'),
(2, '2023-10-02'),
(1, '2023-10-05'),
(3, '2023-10-07');

-- Insert dummy order_items
INSERT INTO order_items (order_id, book_id, quantity) VALUES
(1, 1, 1),
(1, 2, 2),
(2, 3, 1),
(3, 4, 3),
(4, 5, 1),
(4, 2, 2);
