document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".menu-card");

    // ページロード時にlocalStorageから状態を復元
    cards.forEach((card, index) => {
        const upBtn = card.querySelector(".quantity-selector button:first-child");
        const downBtn = card.querySelector(".quantity-selector button:last-child");
        const quantityInput = card.querySelector(".quantity-selector input");
        const statusDiv = card.querySelector(".item-status");

        // menu_idをdata属性等で取得するのが望ましいがここではindexをkeyとして使う例
        const key = "cart_item_" + index;

        // 保存されている情報があれば復元
        const savedDataJSON = localStorage.getItem(key);
        if (savedDataJSON) {
            try {
                const savedData = JSON.parse(savedDataJSON);
                if (savedData.selected) {
                    statusDiv.classList.add("active");
                }
                quantityInput.value = savedData.quantity || 1;
            } catch {
                // JSON parse失敗時は無視
            }
        }

        upBtn.addEventListener("click", () => {
            let value = parseInt(quantityInput.value);
            quantityInput.value = value + 1;
            saveState();
        });

        downBtn.addEventListener("click", () => {
            let value = parseInt(quantityInput.value);
            if (value > 1) {
                quantityInput.value = value - 1;
                saveState();
            }
        });

        statusDiv.addEventListener("click", () => {
            statusDiv.classList.toggle("active");
            saveState();
        });

        function saveState() {
            const data = {
                selected: statusDiv.classList.contains("active"),
                quantity: parseInt(quantityInput.value)
            };
            localStorage.setItem(key, JSON.stringify(data));
        }
    });
});
