CREATE TABLE menus (
    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    menu_name TEXT NOT NULL,
    category TEXT,
    price INTEGER NOT NULL,
    soldout INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (store_id) REFERENCES store(store_id)
);


menu_idを主キーに設定
-- store_idを外部キーとして、storesテーブルのstore_idに関連付け