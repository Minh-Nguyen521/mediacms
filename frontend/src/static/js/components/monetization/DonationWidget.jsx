import React, { useState } from 'react';
import { usePopup } from '../../utils/hooks/';
import { MemberContext } from '../../utils/contexts/';
import { CircleIconButton, PopupMain } from '../_shared';
import { postRequest, csrfToken } from '../../utils/helpers/';

const AMOUNT_PRESETS = [10000, 50000, 100000, 200000];

export function DonationWidget({ creatorUsername }) {
    const [popupContentRef, PopupContent, PopupTrigger] = usePopup();
    const [amount, setAmount] = useState('');
    const [message, setMessage] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    function selectPreset(val) {
        setAmount(String(val));
        setError(null);
    }

    function onAmountChange(e) {
        setAmount(e.target.value);
        setError(null);
    }

    function onSubmit() {
        const amountInt = parseInt(amount, 10);

        if (!amountInt || amountInt < 10000) {
            setError('Minimum donation is 10,000 ₫');
            return;
        }
        if (amountInt > 10000000) {
            setError('Maximum donation is 10,000,000 ₫');
            return;
        }

        setSubmitting(true);
        setError(null);

        postRequest(
            '/donations/to/' + creatorUsername + '/',
            { amount: amountInt, message },
            { headers: { 'X-CSRFToken': csrfToken() } },
            false,
            function (resp) {
                window.location.href = resp.data.payUrl;
            },
            function () {
                setSubmitting(false);
                setError('Payment initiation failed. Please try again.');
            }
        );
    }

    return (
        <li className="donate-widget-wrap">
            <PopupTrigger contentRef={popupContentRef}>
                <span className="donate-trigger" title={'Donate to ' + creatorUsername}>
                    <CircleIconButton buttonShadow={false}>
                        <i className="material-icons">volunteer_activism</i>
                    </CircleIconButton>
                </span>
            </PopupTrigger>

            <PopupContent contentRef={popupContentRef} className="donation-popup">
                <PopupMain>
                    <div className="donation-popup-inner">
                        <div className="donation-popup-title">
                            <i className="material-icons">volunteer_activism</i>
                            Support <strong>{creatorUsername}</strong>
                        </div>

                        <div className="donation-section">
                            <label className="donation-label">Amount (VND)</label>
                            <div className="donation-presets">
                                {AMOUNT_PRESETS.map((p) => (
                                    <button
                                        key={p}
                                        type="button"
                                        className={'donation-preset-btn' + (amount === String(p) ? ' active' : '')}
                                        onClick={() => selectPreset(p)}
                                    >
                                        {Number(p).toLocaleString('vi-VN')} ₫
                                    </button>
                                ))}
                            </div>
                            <input
                                type="number"
                                placeholder="Custom amount"
                                min="10000"
                                max="10000000"
                                step="1000"
                                value={amount}
                                onChange={onAmountChange}
                                className="donation-amount-input"
                            />
                        </div>

                        <div className="donation-section">
                            <label className="donation-label">Message (optional)</label>
                            <textarea
                                placeholder="Leave an encouraging message..."
                                maxLength="500"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                className="donation-message-input"
                                rows="3"
                            />
                        </div>

                        {error ? <div className="donation-error">{error}</div> : null}

                        <button
                            type="button"
                            className="donation-submit-btn"
                            onClick={onSubmit}
                            disabled={submitting || !amount}
                        >
                            {submitting ? (
                                <>
                                    <i className="material-icons rotating">refresh</i>
                                    Redirecting to MoMo...
                                </>
                            ) : (
                                <>
                                    <i className="material-icons">volunteer_activism</i>
                                    Donate via MoMo
                                </>
                            )}
                        </button>

                        <div className="donation-momo-note">
                            Payments processed securely via MoMo e-wallet
                        </div>
                    </div>
                </PopupMain>
            </PopupContent>
        </li>
    );
}
