// static/js/paypay.js の内容

const API_BASE_URL = 'http://127.0.0.1:5010'; // FlaskバックエンドのURLに合わせて変更してください

// HTML要素の取得
// cart-related elements are not needed here if this is payment_selection.html
// const cakeListDiv = document.getElementById('cake-list'); // payment_selection.htmlには不要
// const cartItemsUl = document.getElementById('cart-items'); // payment_selection.htmlには不要
// const cartTotalSpan = document.getElementById('cart-total'); // payment_selection.htmlには不要

// payment_selection.htmlからPayPayボタンと関連要素を取得
const startPaypayButton = document.getElementById('start-paypay-button'); // ★修正: IDを'start-paypay-button'に
const displayTotalPriceSpan = document.getElementById('display-total-price'); // ★追加: 合計金額表示用

const qrModal = document.getElementById('qr-modal');
const closeModalButton = document.querySelector('.close-button');
const qrCodeContainer = document.getElementById('qr-code-container');
const paymentStatusMessage = document.getElementById('payment-status-message');
const deeplinkButton = document.getElementById('deeplink-button');
const qrInstruction = document.getElementById('qr-instruction');

let currentMerchantPaymentId = null; // ポーリングのために支払いIDを保存
let pollInterval = null; // ポーリングsetIntervalのIDを保持
let lastQrCodeUrl = ''; // 最後に生成されたQRコードURLを保存する変数

// ★ payment_selection.html でケーキリストやカート操作は行わないので、
// fetchCakes, displayCakes, addToCart, removeFromCart, updateCartDisplay はこのファイルからは削除します。
// これらの関数は、もし別のページ (例: index.html や cakes.html) で使われるのであれば、
// そのページのJavaScriptに記述してください。

// 「PayPayで支払う」ボタンのクリックイベント
// payment_selection.html の「PayPayで支払う」ボタンにイベントリスナーを設定
if (startPaypayButton) { // ボタンが存在するか確認
    startPaypayButton.addEventListener('click', async () => {
        // data属性から直接値を取得
        const cartDataJson = startPaypayButton.dataset.cartData;
        const totalAmount = parseInt(startPaypayButton.dataset.totalAmount);
        
        if (!cartDataJson || totalAmount <= 0) {
            alert('カート情報が不正です。');
            return;
        }

        let cart = [];
        try {
            cart = JSON.parse(cartDataJson);
        } catch (e) {
            console.error("Failed to parse cart data:", e);
            alert("カートデータの読み込みに失敗しました。");
            return;
        }
        
        if (cart.length === 0) {
            alert('カートに商品がありません。');
            return;
        }

        // PayPay APIのorderItems形式に合わせるため、Flaskから渡された unitPrice を使用
        // Flask側で既に適切な形式に変換されていることを前提とします。
        const orderItems = cart.map(item => ({
            name: item.name, 
            quantity: item.quantity,
            unitPrice: item.unitPrice // Flaskで変換済みの unitPrice オブジェクトをそのまま使用
        }));

        // モーダルとメッセージを初期化
        paymentStatusMessage.textContent = "PayPay支払い情報を準備中...";
        paymentStatusMessage.className = '';
        qrCodeContainer.innerHTML = '';
        deeplinkButton.style.display = 'none'; // ディープリンクボタンを非表示に
        qrInstruction.style.display = 'none'; // QRコード説明文を非表示に
        qrModal.style.display = 'flex'; // ★重要: CSSのflexbox中央寄せを有効にするため 'flex' を指定

        // QRコード生成のためのバックエンド呼び出し
        try {
            // Flaskの /users_order/paypay/create-qr エンドポイントを呼び出す
            const response = await fetch(`${API_BASE_URL}/users_order/paypay/create-qr`, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    orderItems: orderItems, // 変換済みの orderItems を送信
                    amount: {
                        amount: totalAmount,
                        currency: 'JPY'
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`QRコード生成エラー: ${errorData.details || response.statusText}`);
            }

            const data = await response.json();
            console.log("QR Creation Response:", data);

            if (data.resultInfo && data.resultInfo.code === 'SUCCESS' && data.data) {
                currentMerchantPaymentId = data.data.merchantPaymentId; // 支払いIDを保存
                lastQrCodeUrl = data.data.url; // QRコードURLを保存

                let qrCodeHtml = ''; // QRコード関連のHTMLを格納する変数

                // ディープリンクURLが存在する場合
                if (data.data.deeplink) {
                    // データ属性にディープリンクURLを保存し、ボタンを表示
                    deeplinkButton.dataset.deeplink = data.data.deeplink;
                    deeplinkButton.style.display = 'block';

                    // QRコード画像とテキストリンクを両方表示
                    qrCodeHtml = `
                        <a href="${data.data.deeplink}" target="_blank" rel="noopener noreferrer" style="display: inline-block; cursor: pointer;">
                            <img src="${data.data.url}" alt="PayPay QR Code" style="max-width: 200px; height: auto; margin: 20px auto; border: 1px solid #ddd;">
                        </a>
                        <p style="word-break: break-all; font-size: 0.9em; margin-top: 10px;">
                            または直接リンク: <a href="${data.data.url}" target="_blank" rel="noopener noreferrer">${data.data.url}</a>
                        </p>
                    `;
                    qrInstruction.textContent = "スマホでPayPayアプリから開くか、QRコードをスキャンして支払いを完了してください。";
                    qrInstruction.style.display = 'block';
                    paymentStatusMessage.textContent = "PayPayアプリで支払い中...";

                } else if (data.data.url) { // ディープリンクがない場合 (通常はQRコードのURLがある)
                    // QRコード画像とテキストリンクを両方表示
                    qrCodeHtml = `
                        <img src="${data.data.url}" alt="PayPay QR Code" style="max-width: 200px; height: auto; margin: 20px auto; border: 1px solid #ddd;">
                        <p style="word-break: break-all; font-size: 0.9em; margin-top: 10px;">
                            または直接リンク: <a href="${data.data.url}" target="_blank" rel="noopener noreferrer">${data.data.url}</a>
                        </p>
                    `;
                    qrInstruction.textContent = "QRコードをスキャンして支払いを完了してください。";
                    qrInstruction.style.display = 'block';
                    paymentStatusMessage.textContent = "QRコードをスキャンして支払い中...";
                } else {
                     paymentStatusMessage.textContent = "支払い情報の取得に失敗しました。";
                     console.error("No valid QR or Deeplink URL found:", data);
                     return; // 処理を中断
                }

                qrCodeContainer.innerHTML = qrCodeHtml; // 生成したHTMLを設定

                // QRコード画像内の<a>タグにクリックイベントリスナーを追加（ディープリンクがある場合のみ）
                if (data.data.deeplink) {
                    const qrLink = qrCodeContainer.querySelector('a:first-child'); 
                    if (qrLink) {
                        qrLink.addEventListener('click', (e) => {
                            e.preventDefault(); 
                            window.location.href = deeplinkButton.dataset.deeplink; 
                            paymentStatusMessage.textContent = "PayPayアプリに移動しました。アプリで支払いを完了してください。";
                        });
                    }
                }

                // 支払いステータスをポーリング
                pollPaymentStatus(currentMerchantPaymentId);

            } else {
                paymentStatusMessage.textContent = "QRコードの生成に失敗しました。";
                console.error("Failed to get QR code or Deeplink URL:", data);
            }

        } catch (error) {
            console.error("Checkout error:", error);
            paymentStatusMessage.textContent = `エラー: ${error.message}`;
        }
    });
}


// ディープリンクボタンのクリックイベント
if (deeplinkButton) { // ボタンが存在するか確認
    deeplinkButton.addEventListener('click', () => {
        const deeplinkUrl = deeplinkButton.dataset.deeplink; 
        if (deeplinkUrl) {
            window.location.href = deeplinkUrl;
            paymentStatusMessage.textContent = "PayPayアプリに移動しました。アプリで支払いを完了してください。";
        }
    });
}


// 支払いステータスをポーリングする関数
async function pollPaymentStatus(merchantPaymentId) {
    paymentStatusMessage.textContent = "支払いステータスを確認中...";
    paymentStatusMessage.className = ''; 

    const maxAttempts = 120; // 240秒 / 2秒 = 120回
    let attempts = 0;

    // 既存のポーリングがあればクリア
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    pollInterval = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(pollInterval);
            paymentStatusMessage.textContent = "タイムアウト: 支払いステータスを確認できませんでした。";
            paymentStatusMessage.classList.add('status-timeout');
            return;
        }

        try {
            // Flaskの /users_order/paypay/order-status エンドポイントを呼び出す
            const response = await fetch(`${API_BASE_URL}/users_order/paypay/order-status/${merchantPaymentId}`); 
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 429) { 
                     paymentStatusMessage.textContent = "PayPay APIのレート制限中。しばらくお待ちください...";
                     console.warn("PayPay API RATE_LIMIT encountered.");
                     return; 
                }
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
            }
            const data = await response.json();
            console.log("Polling Status Response:", data);

            if (data.data && data.data.status) {
                const status = data.data.status;
                if (status === 'COMPLETED') {
                    clearInterval(pollInterval); 
                    paymentStatusMessage.textContent = "支払い完了！ありがとうございます！";
                    paymentStatusMessage.classList.add('status-completed');
                    
                    // カートデータのクリアと更新は、支払い完了後のリダイレクト先で行うか、
                    // または、この payment_selection.html が再読み込みされるときにリセットされます。
                    // payment_selection.html にはカート表示ロジックがないため、ここでは不要。
                    
                    // 支払い完了後にQRコードURLをテキストとして表示
                    if (lastQrCodeUrl) {
                        const qrLinkText = document.createElement('p');
                        qrLinkText.innerHTML = `決済に使用したQRコード: <a href="${lastQrCodeUrl}" target="_blank" rel="noopener noreferrer">${lastQrCodeUrl}</a>`;
                        qrCodeContainer.appendChild(qrLinkText); 
                    }
                    qrInstruction.style.display = 'none'; 
                    deeplinkButton.style.display = 'none'; 

                    // 支払い完了後のページへリダイレクト
                    // Flaskのreservation_numberルートへリダイレクト
                    // 適切なURLを指定してください (例: /users_order/reservation_number)
                    window.location.href = `${API_BASE_URL}/users_order/reservation_number`; 

                } else if (status === 'CANCELED' || status === 'FAILED') {
                    clearInterval(pollInterval);
                    paymentStatusMessage.textContent = "支払い失敗。もう一度お試しください。";
                    paymentStatusMessage.classList.add('status-failed');
                    qrInstruction.style.display = 'none';
                    deeplinkButton.style.display = 'none';
                } else {
                    paymentStatusMessage.textContent = `支払いステータス: ${status}...`;
                }
            } else if (data.status === 'TIMEOUT') { 
                clearInterval(pollInterval);
                paymentStatusMessage.textContent = "タイムアウト: 支払いステータスを確認できませんでした。";
                paymentStatusMessage.classList.add('status-timeout');
                qrInstruction.style.display = 'none';
                deeplinkButton.style.display = 'none';
            } else if (data.error) {
                clearInterval(pollInterval);
                paymentStatusMessage.textContent = `エラー: ${data.message || data.error}`;
                paymentStatusMessage.classList.add('status-failed');
                qrInstruction.style.display = 'none';
                deeplinkButton.style.display = 'none';
            }
        } catch (error) {
            console.error("Polling error:", error);
            clearInterval(pollInterval);
            paymentStatusMessage.textContent = `ポーリング中にエラーが発生しました: ${error.message}`;
            paymentStatusMessage.classList.add('status-failed');
            qrInstruction.style.display = 'none';
            deeplinkButton.style.display = 'none';
        }
    }, 2000); 
}


// モーダルを閉じるイベント
closeModalButton.addEventListener('click', () => {
    qrModal.style.display = 'none';
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
});

// モーダル外をクリックして閉じる
window.addEventListener('click', (event) => {
    if (event.target === qrModal) {
        qrModal.style.display = 'none';
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
});

// payment_selection.html にはカートの追加・削除機能がないため、
// ページ読み込み時の fetchCakes() や updateCartDisplay() は不要。
// ただし、もし payment_selection.html にカートの中身が動的に表示される要素があるなら
// それらの更新ロジックをここに移植する必要があるかもしれません。
// 今のHTMLではJinja2で表示されているため、JavaScriptでの動的なカート更新は不要です。