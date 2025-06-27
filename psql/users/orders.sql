CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    store_id INT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'completed', 'canceled')),
    datetime DATETIME NOT NULL,
    payment_method TEXT CHECK (payment_method IN ('PayPay')),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);
