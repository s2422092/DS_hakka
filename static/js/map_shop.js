document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    const locationData = mapElement.getAttribute('data-locations');
    const locations = JSON.parse(locationData);

    const map = L.map('map').setView([35.6769, 139.7661], 10);

    // タイルレイヤー
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const markers = [];

    locations.forEach(loc => {
        const menuUrl = `/menu/${loc.id}`;

        // ポップアップの内容（装飾と絵文字付き）
        const popupContent = `
            <div style="font-size: 1em; line-height: 1.5; max-width: 220px;">
                <div style="font-size: 1.5em;">📍</div>
                <a href="${menuUrl}" style="font-weight:bold; color:#007bff; text-decoration: none;">
                    ${loc.store_name || '店舗名未登録'}
                </a><br>
                <span style="color:#444;">メール: ${loc.email || '未登録'}</span><br>
                <span style="color:#444;">担当者: ${loc.representative || '不明'}</span><br>
                <span style="color:#444;">説明: ${loc.description || 'なし'}</span><br>
                <span style="font-size: 0.8em; color: gray;">※クリックでメニュー画面へ</span>
            </div>
        `;

        const marker = L.marker([loc.lat, loc.lng])
            .addTo(map)
            .bindPopup(popupContent);

        // ホバーで開く
        marker.on('mouseover', function () {
            this.openPopup();
        });

        // ホバー外れると閉じる
        marker.on('mouseout', function () {
            this.closePopup();
        });

        // クリックでメニュー画面へ
        marker.on('click', function () {
            window.location.href = menuUrl;
        });

        markers.push(marker);
    });
});
