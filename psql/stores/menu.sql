CREATE TABLE menus (
    store_id  INT NOT NULL,
    menu_id   INT NOT NULL,
    menu_name TEXT NOT NULL,
    category  TEXT,
    price     INT NOT NULL,
    soldout   INT NOT NULL DEFAULT 0, -- 在庫ありを0、売り切れを1とします。デフォルトは在庫あり(0)。
    PRIMARY KEY (menu_id), -- menu_idを主キーに設定
    FOREIGN KEY (store_id) REFERENCES stores(store_id) -- store_idを外部キーとして、storesテーブルのstore_idに関連付け
);