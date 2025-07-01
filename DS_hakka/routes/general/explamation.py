# DS_hakka/routes/general/explamation.py

# 必要なモジュールをまとめてインポートします
from flask import Blueprint, render_template, session

# ブループリントの定義（変更なし）
# /general というURLでアクセスできるようになります
general_bp = Blueprint('general', __name__, url_prefix='/general')

#【追加】ログアウト処理を行うための新しいルート
@general_bp.route('/logout')
def logout():
    """
    セッションをクリアしてログアウトさせ、案内ページを表示する関数
    """
    session.clear() # ★ここでセッション情報をすべて削除します
    return render_template('general/explamation.html')

#【変更なし】元々あった案内ページ表示用のルート
# /general/explamation というURLで直接アクセスした場合に表示されます
@general_bp.route('/explamation')##ここでリンクの指定ただしhttp://localhost:5003/general/explamationこのリンクの/explamationここを指定
##そしてgeneral_bp = Blueprint('general', __name__, url_prefix='/general')ここのurl_prefix='/general'ここで/generalこれをしてしている
def explamation():
    """
    案内ページを単に表示する関数
    """
    return render_template('general/explamation.html')
