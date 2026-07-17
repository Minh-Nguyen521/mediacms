import React from 'react';
import { Page } from './_Page';
import { getRequest, postRequest, csrfToken } from '../utils/helpers/';
import '../components/monetization/monetization.scss';

export class SubscriptionsPage extends Page {
    constructor(props) {
        super(props, 'subscriptions');

        this.state = {
            plans: [],
            currentSub: null,
            loadingPlans: true,
            loadingStatus: true,
            initiating: null, // plan ID being initiated
        };

        this.onPlansLoad = this.onPlansLoad.bind(this);
        this.onStatusLoad = this.onStatusLoad.bind(this);
        this.onSubscribe = this.onSubscribe.bind(this);
        this.onSubscribeSuccess = this.onSubscribeSuccess.bind(this);
        this.onSubscribeError = this.onSubscribeError.bind(this);
    }

    componentDidMount() {
        getRequest('/subscriptions/plans/', false, this.onPlansLoad);
        getRequest('/subscriptions/status/', false, this.onStatusLoad);
    }

    onPlansLoad(resp) {
        this.setState({ plans: resp.data.plans || [], loadingPlans: false });
    }

    onStatusLoad(resp) {
        this.setState({ currentSub: resp.data, loadingStatus: false });
    }

    onSubscribe(planId) {
        this.setState({ initiating: planId });
        postRequest(
            '/subscriptions/initiate/' + planId + '/',
            {},
            { headers: { 'X-CSRFToken': csrfToken() } },
            false,
            this.onSubscribeSuccess,
            this.onSubscribeError
        );
    }

    onSubscribeSuccess(resp) {
        window.location.href = resp.data.payUrl;
    }

    onSubscribeError() {
        this.setState({ initiating: null });
        alert('Failed to initiate payment. Please try again.');
    }

    pageContent() {
        const { plans, currentSub, loadingPlans, loadingStatus, initiating } = this.state;
        const isLoading = loadingPlans || loadingStatus;

        return (
            <div className="subscriptions-page">
                <div className="subscriptions-header">
                    <i className="material-icons subscriptions-header-icon">workspace_premium</i>
                    <h1>Premium Membership</h1>
                    <p>Subscribe to unlock exclusive content and support the platform</p>
                </div>

                {!loadingStatus && currentSub && currentSub.active ? (
                    <div className="subscription-status-banner">
                        <i className="material-icons">verified</i>
                        <span>
                            Your <strong>{currentSub.plan}</strong> subscription is active until{' '}
                            <strong>{new Date(currentSub.end_date).toLocaleDateString('vi-VN')}</strong>
                        </span>
                    </div>
                ) : null}

                {isLoading ? (
                    <div className="subscriptions-loading">
                        <i className="material-icons rotating">refresh</i>
                        <span>Loading plans...</span>
                    </div>
                ) : plans.length === 0 ? (
                    <div className="subscriptions-empty">No subscription plans are available at this time.</div>
                ) : (
                    <div className="subscription-plans">
                        {plans.map((plan) => (
                            <div key={plan.id} className={'subscription-plan-card' + (currentSub && currentSub.active && currentSub.plan === plan.name ? ' current-plan' : '')}>
                                {currentSub && currentSub.active && currentSub.plan === plan.name ? (
                                    <div className="plan-badge">Current Plan</div>
                                ) : null}
                                <div className="plan-icon">
                                    <i className="material-icons">workspace_premium</i>
                                </div>
                                <div className="plan-name">{plan.name}</div>
                                {plan.description ? <div className="plan-description">{plan.description}</div> : null}
                                <div className="plan-price">
                                    {Number(plan.price).toLocaleString('vi-VN')}
                                    <span className="plan-currency"> ₫</span>
                                </div>
                                <div className="plan-duration">{plan.duration_days} days</div>
                                <button
                                    className="subscribe-btn"
                                    onClick={() => this.onSubscribe(plan.id)}
                                    disabled={!!initiating}
                                >
                                    {initiating === plan.id ? (
                                        <>
                                            <i className="material-icons rotating">refresh</i>
                                            Redirecting to MoMo...
                                        </>
                                    ) : (
                                        'Subscribe'
                                    )}
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                <div className="subscriptions-momo-note">
                    <img
                        src="https://upload.wikimedia.org/wikipedia/vi/f/fe/MoMo_Logo.png"
                        alt="MoMo"
                        className="momo-logo"
                        onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    <span>Payments are processed securely via MoMo e-wallet</span>
                </div>
            </div>
        );
    }
}
