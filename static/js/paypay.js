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
        // CSSでdisplay: none; が初期設定されているので、モーダルを表示させる
        qrModal.style.display = 'flex'; // 中央寄せのためflexにする
        paymentStatusMessage.textContent = "PayPayアプリからのリダイレクトを確認中...";
        pollPaymentStatus(currentMerchantPaymentId);
    }
    // Flaskからのflashメッセージを表示（あれば）は、JavaScriptファイル内では直接扱えません。
    // HTML側でJinja2を使って表示するか、別途APIエンドポイントを設けてJSから取得する必要があります。
});

// 「PayPayで支払う」ボタンのクリックイベント
startPaypayButton.addEventListener('click', async (event) => {
    // フォームのデフォルト送信を防止
    event.preventDefault();

    // カートデータまたは合計金額が不正な場合のチェック
    if (cartData.length === 0 || totalAmount === 0) {
        alert('カートに商品がないか、合計金額が0円です。');
        return;
    }

    // モーダルの表示と初期メッセージの設定
    paymentStatusMessage.textContent = "PayPay支払い情報を準備中...";
    paymentStatusMessage.className = ''; // クラスをリセット
    qrCodeContainer.innerHTML = ''; // QRコードコンテナをクリア
    deeplinkButton.style.display = 'none'; // ディープリンクボタンを非表示
    qrInstruction.style.display = 'none'; // QRコード説明文を非表示
    qrModal.style.display = 'flex'; // モーダルを表示 (CSSで中央寄せに設定するため 'flex')

    // カートデータをPayPay APIの要求形式に変換
    const orderItems = cartData.map(item => ({
        name: item.name,
        quantity: item.quantity,
        unitPrice: {
            amount: item.price,
            currency: 'JPY'
        }
    }));
    
    try {
        // PayPay QRコード生成APIへのリクエスト
        const response = await fetch(`${API_BASE_URL}/users_order/paypay/create-qr`, { // Flaskのブループリントパスを含む
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

        // HTTPエラーハンドリング
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`QRコード生成エラー: ${errorData.details || response.statusText}`);
        }

        const data = await response.json();
        console.log("QR Creation Response:", data);

        // PayPay APIレスポンスの成功判定とデータ処理
        if (data.resultInfo && data.resultInfo.code === 'SUCCESS' && data.data) {
            currentMerchantPaymentId = data.data.merchantPaymentId; // 支払いIDを保存
            lastQrCodeUrl = data.data.url; // 最後に生成されたQRコードURLを保存

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
                 // QRコードもディープリンクも取得できなかった場合
                 paymentStatusMessage.textContent = "支払い情報の取得に失敗しました。";
                 console.error("No valid QR or Deeplink URL found:", data);
                 return; // 処理を中断
            }

            qrCodeContainer.innerHTML = qrCodeHtml; // 生成したHTMLをコンテナに挿入

            // QRコード画像内の<a>タグにクリックイベントリスナーを追加（ディープリンクがある場合のみ）
            // これは、QRコード画像自体がディープリンクとして機能するようにするため
            if (data.data.deeplink) {
                const qrLink = qrCodeContainer.querySelector('a:first-child'); // 最初の<a>タグを選択
                if (qrLink) {
                    qrLink.addEventListener('click', (e) => {
                        e.preventDefault(); // デフォルトのリンク動作を停止
                        window.location.href = deeplinkButton.dataset.deeplink; // ディープリンクへ遷移
                        paymentStatusMessage.textContent = "PayPayアプリに移動しました。アプリで支払いを完了してください。";
                    });
                }
            }

            // 支払いステータスのポーリングを開始
            pollPaymentStatus(currentMerchantPaymentId);

        } else {
            // PayPay APIがSUCCESSを返さなかった場合
            paymentStatusMessage.textContent = "QRコードの生成に失敗しました。";
            console.error("Failed to get QR code or Deeplink URL:", data);
        }

    } catch (error) {
        // fetchまたはJSONパース中のエラー
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

    const pollStep = 5000; // ポーリング間隔 (5秒)
    const maxPollingTime = 240000; // 最大ポーリング時間 (4分)
    const maxAttempts = maxPollingTime / pollStep; // 最大試行回数
    let attempts = 0;

    // 既存のポーリングがあればクリア
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    // ポーリング開始
    pollInterval = setInterval(async () => {
        attempts++;
        // タイムアウト判定
        if (attempts > maxAttempts) {
            clearInterval(pollInterval);
            paymentStatusMessage.textContent = "タイムアウト: 支払いステータスを確認できませんでした。";
            paymentStatusMessage.classList.add('status-timeout');
            // 必要に応じて、ここで支払いキャンセルや再試行のオプションを提示できます
            return;
        }

        try {
            // PayPay支払いステータス取得APIへのリクエスト
            const response = await fetch(`${API_BASE_URL}/users_order/paypay/order-status/${merchantPaymentId}`);
            
            // レート制限の場合
            if (response.status === 429) {
                paymentStatusMessage.textContent = "PayPay APIのレート制限中。しばらくお待ちください...";
                console.warn("PayPay API RATE_LIMIT encountered.");
                return;
            }
            // その他のHTTPエラー
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Polling Status Response:", data);

            // ステータス判定
            if (data.data && data.data.status) {
                const status = data.data.status;
                if (status === 'COMPLETED') {
                    clearInterval(pollInterval); // ポーリング停止
                    paymentStatusMessage.textContent = "支払い完了！ありがとうございます！";
                    paymentStatusMessage.classList.add('status-completed');
                    
                    // 支払い完了後、注文完了ページへリダイレクト
                    // Flaskのブループリントパスに合わせて修正
                    window.location.href = `/users_order/reservation_number`; 

                } else if (status === 'CANCELED' || status === 'FAILED') {
                    clearInterval(pollInterval); // ポーリング停止
                    paymentStatusMessage.textContent = "支払い失敗。もう一度お試しください。";
                    paymentStatusMessage.classList.add('status-failed');
                    qrInstruction.style.display = 'none'; // 説明文を非表示
                    deeplinkButton.style.display = 'none'; // ディープリンクボタンを非表示
                } else {
                    // その他のステータスの場合、メッセージを更新してポーリング継続
                    paymentStatusMessage.textContent = `支払いステータス: ${status}...`;
                }
            } else if (data.error) {
                // APIからのエラーレスポンスの場合
                clearInterval(pollInterval);
                paymentStatusMessage.textContent = `エラー: ${data.message || data.error}`;
                paymentStatusMessage.classList.add('status-failed');
                qrInstruction.style.display = 'none';
                deeplinkButton.style.display = 'none';
            }
        } catch (error) {
            // ポーリング中のネットワークエラーなど
            console.error("Polling error:", error);
            clearInterval(pollInterval);
            paymentStatusMessage.textContent = `ポーリング中にエラーが発生しました: ${error.message}`;
            paymentStatusMessage.classList.add('status-failed');
            qrInstruction.style.display = 'none';
            deeplinkButton.style.display = 'none';
        }
    }, pollStep);
}

// モーダルを閉じるイベント (Xボタン)
closeModalButton.addEventListener('click', () => {
    qrModal.style.display = 'none'; // モーダルを非表示にする
    // ポーリングが実行中の場合は停止
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
});

// モーダル外をクリックして閉じるイベント
window.addEventListener('click', (event) => {
    if (event.target === qrModal) {
        qrModal.style.display = 'none'; // モーダルを非表示にする
        // ポーリングが実行中の場合は停止
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
});