document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    const locationData = mapElement.getAttribute('data-locations');
    const locations = JSON.parse(locationData);

    const map = L.map('map').setView([35.6769, 139.7661], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const markers = [];

    locations.forEach(loc => {
        const detailUrl = `/store/${loc.store_id}`;

        const popupContent = `
            <div>
                <a href="${detailUrl}" style="font-weight:bold; color:blue;">
                    ${loc.store_name || '店舗名未登録'}
                </a><br>
                メール: ${loc.email || '未登録'}<br>
                担当者: ${loc.representative || '不明'}<br>
                説明: ${loc.description || 'なし'}<br>
                <small>クリックで店舗詳細ページへ</small>
            </div>
        `;

        const marker = L.marker([loc.lat, loc.lng])
            .addTo(map)
            .bindPopup(popupContent);

        marker.on('mouseover', function () {
            this.openPopup();
        });
        marker.on('mouseout', function () {
            this.closePopup();
        });

        marker.on('click', function () {
            window.location.href = detailUrl;
        });

        markers.push(marker);
    });
});
