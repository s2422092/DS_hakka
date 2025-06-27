document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".menu-card");

    cards.forEach(card => {
        const upBtn = card.querySelector(".quantity-selector button:first-child");
        const downBtn = card.querySelector(".quantity-selector button:last-child");
        const quantityInput = card.querySelector(".quantity-selector input");

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

        // ✅ item-statusをクリックで色変更
        const statusDiv = card.querySelector(".item-status");
        statusDiv.addEventListener("click", () => {
            statusDiv.classList.toggle("active");
        });

    });
});