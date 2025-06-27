document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".menu-card");

    cards.forEach(card => {
        const upBtn = card.querySelector(".qty-up-btn");
        const downBtn = card.querySelector(".qty-down-btn");
        const quantityInput = card.querySelector(".qty-input");
        const addToCartBtn = card.querySelector(".add-to-cart-btn");

        upBtn.addEventListener("click", () => {
            let value = parseInt(quantityInput.value);
            quantityInput.value = value + 1;
        });

        downBtn.addEventListener("click", () => {
            let value = parseInt(quantityInput.value);
            if (value > 1) {
                quantityInput.value = value - 1;
            }
        });

        addToCartBtn.addEventListener("click", () => {
            const menuId = card.dataset.menuId;
            const name = card.dataset.name;
            const category = card.dataset.category;
            const price = parseInt(card.dataset.price);
            const quantity = parseInt(quantityInput.value);

            fetch('/add_to_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrf_token')  // CSRF対策があるなら
                },
                body: JSON.stringify({ menu_id: parseInt(menuId), name, category, price, quantity })
            })
            .then(res => res.json())
            .then(data => {
                if(data.error){
                    alert('カート追加に失敗しました');
                } else {
                    alert('カートに追加しました！');
                    // ここでカート数表示更新などがあれば行う
                }
            })
            .catch(() => alert('通信エラーが発生しました'));
        });
    });

    // CSRFトークンをCookieから取得する補助関数（Flask-WTF使っている場合）
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
