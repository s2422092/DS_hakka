// API_BASE_URL はブループリントのURLプレフィックスを含めない
        // Flaskが提供するurl_forを使って絶対パスを生成するのが最も確実
        const API_BASE_URL = '{{ url_for("users_order.paypay_create_qr").split("/paypay/create-qr")[0] }}';

        // HTML要素の取得
        const startPaypayButton = document.getElementById('start-paypay-button');
        const confirmOrderForm = document.getElementById('confirm-order-form');
        const qrModal = document.getElementById('qr-modal');
        const closeModalButton = document.querySelector('.close-button');
        const qrCodeContainer = document.getElementById('qr-code-container');
        const paymentStatusMessage = document.getElementById('payment-status-message');
        const deeplinkButton = document.getElementById('deeplink-button');
        const qrInstruction = document.getElementById('qr-instruction');

        // カート情報と合計金額をJinja2から直接取得
        const cartData = {{ cart | tojson }};
        const totalAmount = {{ total_price }};

        let currentMerchantPaymentId = null;
        let pollInterval = null;
        let lastQrCodeUrl = '';

        // ページ読み込み時に、PayPayからのリダイレクトがあったか確認し、ポーリングを再開
        window.addEventListener('load', () => {
            const storedMerchantId = "{{ session.pop('paypay_callback_merchant_id', '') }}";
            if (storedMerchantId) {
                currentMerchantPaymentId = storedMerchantId;
                qrModal.style.display = 'flex';
                paymentStatusMessage.textContent = "PayPayアプリからのリダイレクトを確認中...";
                pollPaymentStatus(currentMerchantPaymentId);
            }

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
                const response = await fetch(`${API_BASE_URL}/paypay/create-qr`, {
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
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE_URL}/paypay/order-status/${merchantPaymentId}`);
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
                            window.location.href = "{{ url_for('users_order.reservation_number') }}";

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