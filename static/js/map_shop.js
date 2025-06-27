document.addEventListener('DOMContentLoaded', function () {
    // 初期表示：東京（緯度経度）を中心にズーム10で表示
    const map = L.map('map').setView([35.6769, 139.7661], 10);

    // OpenStreetMap タイルレイヤーを読み込み
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
});
