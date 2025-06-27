CREATE TABLE menus (
    store_id  INT NOT NULL,
    menu_id   INT NOT NULL,
    menu_name TEXT NOT NULL,
    category  TEXT,
    price     INT NOT NULL,
    soldout   INT NOT NULL DEFAULT 0, 
    PRIMARY KEY (menu_id), 
    FOREIGN KEY (store_id) REFERENCES stores(store_id) 
);

menu_idを主キーに設定
-- store_idを外部キーとして、storesテーブルのstore_idに関連付け