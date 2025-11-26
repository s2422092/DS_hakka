# 開発環境のセットアップ手順

## 初回セットアップ（チームメンバー向け）

### 1. リポジトリをクローン
```bash
git clone <リポジトリURL>
cd ds_hakka
```

### 2. 仮想環境を作成
```bash
python3 -m venv .venv
```

### 3. 仮想環境を有効化
```bash
source .venv/bin/activate  # Mac/Linux
# または
.venv\Scripts\activate     # Windows
```

### 4. パッケージをインストール
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. アプリを起動
```bash
python app.py
```

ブラウザで `http://localhost:5003/general/explamation` にアクセス

## VS Codeでの設定

1. `Cmd + Shift + P` (Mac) / `Ctrl + Shift + P` (Windows)
2. "Python: Select Interpreter" を選択
3. `.venv` (Python 3.10.x) を選択

## トラブルシューティング

### モジュールエラーが出る場合
```bash
# キャッシュをクリア
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 仮想環境を作り直す
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### `.venv`について
- `.venv`はgitで管理されていません（各自がローカルで作成）
- チームメンバーは上記の手順で各自の環境で`.venv`を作成してください
