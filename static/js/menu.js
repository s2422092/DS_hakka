// static/js/menu.js

document.addEventListener('DOMContentLoaded', function() {
    
    // APIのURLをHTMLの属性から取得（ハードコーディングを避けるため）
    // この方法はHTMLに <div id="api-urls" data-add-cart-url="..."> のような要素を置く必要がありますが、
    // 今回は簡単のため、直接URLを記述します。
    const addCartUrl = '/users_order/add_to_cart';

    // 全てのメニューカードにイベントリスナーを設定
    document.querySelectorAll('.menu-card').forEach(card => {
        const menuId = card.dataset.menuId;
        const qtyInput = card.querySelector('.qty-input');
        
        // 数量を増やすボタン
        card.querySelector('.qty-up-btn').addEventListener('click', () => {
            qtyInput.value = parseInt(qtyInput.value) + 1;
        });

        // 数量を減らすボタン
        card.querySelector('.qty-down-btn').addEventListener('click', () => {
            let currentQty = parseInt(qtyInput.value);
            if (currentQty > 1) {
                qtyInput.value = currentQty - 1;
            }
        });

        // カートに追加ボタン
        card.querySelector('.add-to-cart-btn').addEventListener('click', () => {
            const quantity = parseInt(qtyInput.value);
            
            // バックエンドAPIを呼び出す
            fetch(addCartUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    menu_id: menuId,
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    displayFlashMessage(data.error, 'error');
                } else {
                    displayFlashMessage(data.message, 'success');
                    // ヘッダーのカート数を更新
                    document.getElementById('cart-count').textContent = data.cart_count;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                displayFlashMessage('通信エラーが発生しました。', 'error');
            });
        });
    });

    // メッセージを画面に表示するためのヘルパー関数
    function displayFlashMessage(message, category) {
        const container = document.getElementById('flash-message-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = `flash ${category}`;
        messageDiv.textContent = message;
        container.appendChild(messageDiv);

        // 3秒後にメッセージを消す
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                messageDiv.remove();
            }, 500);
        }, 3000);
    }
});