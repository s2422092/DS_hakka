CREATE TABLE users_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    u_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,           -- 平文パスワード用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
