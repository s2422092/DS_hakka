// static/js/paypay.js

// HTML要素の取得
const startPaypayButton = document.getElementById('start-paypay-button');
const confirmOrderForm = document.getElementById('confirm-order-form'); // このフォーム自体は直接使わないが、セレクタは残す
const qrModal = document.getElementById('qr-modal');
const closeModalButton = document.querySelector('.close-button');
const qrCodeContainer = document.getElementById('qr-code-container');
const paymentStatusMessage = document.getElementById('payment-status-message');
const deeplinkButton = document.getElementById('deeplink-button');
const qrInstruction = document.getElementById('qr-instruction');

// データ属性から値を取得
const API_BASE_URL = startPaypayButton.dataset.apiBaseUrl;
const cartData = JSON.parse(startPaypayButton.dataset.cartData); // JSON文字列をパース
const totalAmount = parseFloat(startPaypayButton.dataset.totalAmount); // 数値に変換
const initialMerchantId = startPaypayButton.dataset.callbackMerchantId; // 初期コールバックID

let currentMerchantPaymentId = null;
let pollInterval = null;
let lastQrCodeUrl = '';

// ページ読み込み時に、PayPayからのリダイレクトがあったか確認し、ポーリングを再開
window.addEventListener('load', () => {
    if (initialMerchantId) {
        currentMerchantPaymentId = initialMerchantId;
        qrModal.style.display = 'flex';
        paymentStatusMessage.textContent = "PayPayアプリからのリダイレクトを確認中...";
        pollPaymentStatus(currentMerchantPaymentId);
    }
    // Flaskからのflashメッセージを表示（あれば）
    // JavaScriptファイル内ではJinja2のget_flashed_messages()は使えません。
    // そのため、flashメッセージはHTML側で処理する必要があります。
    // あるいは、別途JSから取得するAPIエンドポイントを設ける必要があります。
});

// 「PayPayで支払う」ボタンのクリックイベント
startPaypayButton.addEventListener('click', async (event) => {
    event.preventDefault();

    if (cartData.length === 0 || totalAmount === 0) {
        alert('カートに商品がないか、合計金額が0円です。');
        return;
    }

    paymentStatusMessage.textContent = "PayPay支払い情報を準備中...";
    paymentStatusMessage.className = '';
    qrCodeContainer.innerHTML = '';
    deeplinkButton.style.display = 'none';
    qrInstruction.style.display = 'none';
    qrModal.style.display = 'flex';

    const orderItems = cartData.map(item => ({
        name: item.name,
        quantity: item.quantity,
        unitPrice: {
            amount: item.price,
            currency: 'JPY'
        }
    }));
    
    try {
        const response = await fetch(`${API_BASE_URL}/users_order/paypay/create-qr`, { // ブループリントのパスを追加
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                orderItems: orderItems,
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
            currentMerchantPaymentId = data.data.merchantPaymentId;
            lastQrCodeUrl = data.data.url;

            let qrCodeHtml = '';

            if (data.data.deeplink) {
                deeplinkButton.dataset.deeplink = data.data.deeplink;
                deeplinkButton.style.display = 'block';

                qrCodeHtml = `
                    <a href="${data.data.deeplink}" target="_blank" rel="noopener noreferrer" style="display: inline-block; cursor: pointer;">
                        <img src="${data.data.url}" alt="PayPay QR Code">
                    </a>
                    <p>または直接リンク: <a href="${data.data.url}" target="_blank" rel="noopener noreferrer">${data.data.url}</a></p>
                `;
                qrInstruction.textContent = "スマホでPayPayアプリから開くか、QRコードをスキャンして支払いを完了してください。";
                qrInstruction.style.display = 'block';
                paymentStatusMessage.textContent = "PayPayアプリで支払い中...";

            } else if (data.data.url) {
                qrCodeHtml = `
                    <img src="${data.data.url}" alt="PayPay QR Code">
                    <p>または直接リンク: <a href="${data.data.url}" target="_blank" rel="noopener noreferrer">${data.data.url}</a></p>
                `;
                qrInstruction.textContent = "QRコードをスキャンして支払いを完了してください。";
                qrInstruction.style.display = 'block';
                paymentStatusMessage.textContent = "QRコードをスキャンして支払い中...";
            } else {
                 paymentStatusMessage.textContent = "支払い情報の取得に失敗しました。";
                 console.error("No valid QR or Deeplink URL found:", data);
                 return;
            }

            qrCodeContainer.innerHTML = qrCodeHtml;

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

// ディープリンクボタンのクリックイベント
deeplinkButton.addEventListener('click', () => {
    const deeplinkUrl = deeplinkButton.dataset.deeplink;
    if (deeplinkUrl) {
        window.location.href = deeplinkUrl;
        paymentStatusMessage.textContent = "PayPayアプリに移動しました。アプリで支払いを完了してください。";
    }
});

// 支払いステータスをポーリングする関数
async function pollPaymentStatus(merchantPaymentId) {
    paymentStatusMessage.textContent = "支払いステータスを確認中...";
    paymentStatusMessage.className = '';

    const pollStep = 5000;
    const maxPollingTime = 240000;
    const maxAttempts = maxPollingTime / pollStep; 
    let attempts = 0;

    if (pollInterval) {
        clearInterval(pollInterval);
    }

    pollInterval = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(pollInterval);
            paymentStatusMessage.textContent = "タイムアウト: 支払いステータスを確認できませんでした。";
            paymentStatusMessage.classList.add('status-timeout');
            // 必要に応じて、ここで支払いキャンセルや再試行のオプションを提示
            return;
        }

        try {
            // ブループリントのパスを追加
            const response = await fetch(`${API_BASE_URL}/users_order/paypay/order-status/${merchantPaymentId}`);
            if (response.status === 429) {
                paymentStatusMessage.textContent = "PayPay APIのレート制限中。しばらくお待ちください...";
                console.warn("PayPay API RATE_LIMIT encountered.");
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
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
                    // 注文完了ページへのリダイレクトは、サーバーサイドでセッションを使って行うのが確実
                    // クライアントサイドのリダイレクトも可能だが、二重処理にならないよう注意
                    window.location.href = `{{ url_for('users_order.reservation_number') }}`; // Jinja2は外部JSでは使えない
                    // この行はHTML内に直接スクリプトブロックを書くか、
                    // サーバーからのレスポンスにリダイレクト先を含める必要があります。
                    // 現状はHTMLに直接埋め込まれたスクリプトのままなので、この行は生きています。
                    // 外部JSファイルにした場合、この行はエラーになります。
                    // 外部JSにする場合は、以下のように修正する必要があります。
                    // 例: window.location.href = `${API_BASE_URL}/users_order/reservation_number`;
                    // ただし、order_idを渡す必要があるため、サーバーサイドのリダイレクトが理想的。
                    // → 支払い完了時にサーバーがDBを更新し、session['last_order_id']を設定し、
                    //   /paypay/order-status が成功レスポンスを返したら、
                    //   JS側で /users_order/reservation_number へリダイレクトする。
                    //   ただし、reservation_numberはsession.pop()を使うので、
                    //   ポーリングが完了してリダイレクトする前にPayPayのcallbackが
                    //   先に呼ばれてしまうとsession['last_order_id']が消えてしまう可能性があるので注意が必要。
                    //   現状のusers_order.pyでは、get_payment_details成功時にsession['last_order_id']を設定しているので、
                    //   そのタイミングでリダイレクトするのが良いでしょう。
                    //   最も堅牢なのは、order-status APIがステータス更新後に直接リダイレクトURLを返すことです。
                    //   しかし、現在 polling は status を返すだけなので、
                    //   フロントエンドでリダイレクトをトリガーします。
                    //   session['last_order_id'] が N/A になるのを防ぐため、
                    //   サーバー側で payment_status が COMPLETED になった際に
                    //   DBの status を更新し、フロントには成功を示す。
                    //   そして、フロントは payment_selection から reservation_number にリダイレクト。
                    //   その際、reservation_number は DB から merchant_payment_id をキーに order_id を取得するように変更するか、
                    //   PayPayコールバック/ポーリング成功時にセッションに order_id を直接セットし直すか、検討が必要です。
                    //   => 現状のusers_order.pyではpoll時にsession['last_order_id']を設定しているので、それを信頼してリダイレクトします。
                    window.location.href = `/users_order/reservation_number`; // ブループリントのルートパスに修正

                } else if (status === 'CANCELED' || status === 'FAILED') {
                    clearInterval(pollInterval);
                    paymentStatusMessage.textContent = "支払い失敗。もう一度お試しください。";
                    paymentStatusMessage.classList.add('status-failed');
                    qrInstruction.style.display = 'none';
                    deeplinkButton.style.display = 'none';
                } else {
                    paymentStatusMessage.textContent = `支払いステータス: ${status}...`;
                }
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
    }, pollStep);
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