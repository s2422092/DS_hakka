document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".menu-card");

    cards.forEach(card => {
        const upBtn = card.querySelector(".qty-up-btn");
        const downBtn = card.querySelector(".qty-down-btn");
        const quantityInput = card.querySelector(".qty-input");
        const addToCartBtn = card.querySelector(".add-to-cart-btn");

        // ▲ ボタンで数量を増やす
        upBtn.addEventListener("click", () => {
            let value = parseInt(quantityInput.value);
            quantityInput.value = value + 1;
        });

        // ▼ ボタンで数量を減らす
        downBtn.addEventListener("click", () => {
            let value = parseInt(quantityInput.value);
            if (value > 1) {
                quantityInput.value = value - 1;
            }
        });

        // カートに追加ボタン
        addToCartBtn.addEventListener("click", () => {
            const menuId = parseInt(card.dataset.menuId);
            const name = card.dataset.name;
            const category = card.dataset.category;
            const price = parseInt(card.dataset.price);
            const quantity = parseInt(quantityInput.value);

            const payload = {
                menu_id: menuId,
                name: name,
                category: category,
                price: price,
                quantity: quantity
            };

            fetch('/add_to_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert("エラー: " + data.error);
                } else {
                    addToCartBtn.classList.add("added");
                    addToCartBtn.textContent = "追加済み";
                    addToCartBtn.disabled = true;
                }
            })
            .catch((error) => {
                console.error("通信エラー:", error);
                alert('通信エラーが発生しました');
            });
        });
    });
});
