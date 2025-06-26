CREATE TABLE store (
    store_id SERIAL PRIMARY KEY,
    store_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    location TEXT,
    representative TEXT,
    description TEXT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
