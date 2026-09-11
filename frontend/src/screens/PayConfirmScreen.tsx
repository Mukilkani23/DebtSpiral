import { useState } from 'react';
import { useSession } from '../store/session';
import { api, ApiError } from '../api/client';
import BackHeader from '../components/BackHeader';
import PayNowButton from '../components/PayNowButton';
import TierBadge from '../components/TierBadge';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function PayConfirmScreen() {
  const payContact = useSession((s) => s.payContact);
  const payAmount = useSession((s) => s.payAmount);
  const payCategory = useSession((s) => s.payCategory);
  const payTier = useSession((s) => s.payTier);
  const personaId = useSession((s) => s.personaId);
  const riskScore = useSession((s) => s.riskScore);
  const expenses = useSession((s) => s.expenses);
  const setScreen = useSession((s) => s.setScreen);
  const addTransaction = useSession((s) => s.addTransaction);
  const updateRisk = useSession((s) => s.updateRisk);
  const setPayResult = useSession((s) => s.setPayResult);
  const setPayError = useSession((s) => s.setPayError);
  const setPayFailureReason = useSession((s) => s.setPayFailureReason);
  const setBankBalance = useSession((s) => s.setBankBalance);
  const setLoading = useSession((s) => s.setLoading);
  const setPayButtonState = useSession((s) => s.setPayButtonState);
  const apiConnected = useSession((s) => s.apiConnected);
  const loading = useSession((s) => s.loading);

  const [buttonState, setLocalButtonState] = useState<'safe' | 'warning' | 'flagged'>('safe');
  const [submitted, setSubmitted] = useState(false);

  const expense = expenses.find((e) => e.id === payCategory);
  const budgetAfter = (expense?.currentSpend || 0) + payAmount;
  const budgetExceeded = expense ? budgetAfter > expense.monthlyBudget : false;
  const budgetNearlyExceeded = expense ? budgetAfter > expense.monthlyBudget * 0.8 : false;

  const computedState = budgetExceeded && payTier === 3 ? 'flagged' : budgetNearlyExceeded ? 'warning' : 'safe';
  const displayState = submitted ? buttonState : computedState;

  const apiCategory = (() => {
    const catMap: Record<string, string> = {
      'friends': 'entertainment', 'chatgpt': 'subscription', 'entertainment': 'entertainment',
      'groceries': 'food_delivery', 'petrol': 'travel', 'medical': 'other',
      'wifi': 'subscription', 'recharge': 'subscription', 'insurance': 'other',
      'family': 'other', 'food_delivery': 'food_delivery',
    };
    return catMap[payCategory] || 'other';
  })();

  const handlePay = async () => {
    setSubmitted(true);
    setLoading('txn', true);
    setPayError(null);
    setPayFailureReason(null);

    if (!apiConnected) {
      // Server is authoritative for affordability — without it reachable,
      // we cannot approve a payment, and we must NOT claim the balance was
      // insufficient (that would be fabricating a decision we can't back
      // with a real number). This is a distinct, explicit failure reason.
      setPayError(null);
      setPayFailureReason('unreachable');
      setLoading('txn', false);
      setScreen('pay-failed');
      return;
    }

    try {
      const result = await api.transaction({
        persona_id: personaId, category: apiCategory, amount_inr: payAmount,
      });

      const flagged = result.flagged ?? false;
      const newRisk = result.risk_after ?? result.risk_score ?? riskScore;
      const reasonCodes = result.reason_codes || [];
      const nudge = result.nudge || null;

      if (result.shap) useSession.setState({ shap: result.shap });
      if (result.spiral_detected !== undefined) useSession.setState({ spiralDetected: result.spiral_detected });

      const finalState = flagged ? 'flagged' : 'safe';
      setLocalButtonState(finalState);
      setPayButtonState(finalState);

      const newBand = newRisk >= 70 ? 'HIGH' : newRisk >= 50 ? 'ELEVATED' : newRisk >= 30 ? 'MODERATE' : 'LOW';
      updateRisk(newRisk, newBand, reasonCodes, nudge);

      addTransaction({
        id: `tx_${Date.now()}`, label: payContact?.name || payCategory, amount: payAmount,
        category: payCategory, tier: payTier, timestamp: Date.now(), flagged,
        riskBefore: riskScore, riskAfter: newRisk,
      });

      // Refresh the real balance from the backend — never derive it locally.
      try {
        const account = await api.getAccount(personaId);
        setBankBalance(account.balance_inr);
      } catch { /* balance display will just be stale until next refresh */ }

      setPayResult({ flagged, riskBefore: riskScore, riskAfter: newRisk, reasonCodes });
      setLoading('txn', false);
      setScreen('pay-success');
    } catch (err) {
      setLoading('txn', false);
      if (err instanceof ApiError && err.status === 400 && err.body?.error_code === 'INSUFFICIENT_BALANCE') {
        setPayError({
          requested_amount_inr: err.body.requested_amount_inr,
          available_balance_inr: err.body.available_balance_inr,
          shortfall_inr: err.body.shortfall_inr,
        });
        setPayFailureReason('insufficient_balance');
      } else {
        // Any other failure (network error, unexpected 4xx/5xx, timeout) is
        // NOT insufficient balance — we have no verified balance/shortfall
        // to show, so don't invent one.
        setPayError(null);
        setPayFailureReason('unreachable');
      }
      setScreen('pay-failed');
    }
  };

  return (
    <div className="pb-4 bg-white">
      <BackHeader title="Confirm Payment" to="pay" />
      <div className="px-5">
        <div className="flex flex-col items-center mb-6">
          <div className="w-16 h-16 bg-accent-light rounded-full flex items-center justify-center text-accent font-bold text-[24px] mb-2">
            {payContact?.avatar || '?'}
          </div>
          <p className="text-[16px] font-semibold text-text-primary">Pay {payContact?.name}</p>
          <p className="text-[28px] font-bold text-text-primary mt-1 tabular-nums">{'₹'}{fmt(payAmount)}</p>
        </div>

        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4 space-y-2">
          <div className="flex justify-between text-[12px]">
            <span className="text-text-secondary">Tier</span>
            <TierBadge tier={payTier} />
          </div>
          <div className="flex justify-between text-[12px]">
            <span className="text-text-secondary">Category</span>
            <span className="text-text-primary">{expense?.name || payCategory}</span>
          </div>
          <div className="flex justify-between text-[12px]">
            <span className="text-text-secondary">From</span>
            <span className="text-text-primary">Demo Bank Account</span>
          </div>
          {expense && (
            <>
              <div className="border-t border-border my-2" />
              <div className="flex justify-between text-[12px]">
                <span className="text-text-secondary">Monthly budget</span>
                <span className="text-text-primary">{'₹'}{fmt(expense.monthlyBudget)}</span>
              </div>
              <div className="flex justify-between text-[12px]">
                <span className="text-text-secondary">Current spending</span>
                <span className="text-text-primary">{'₹'}{fmt(expense.currentSpend)}</span>
              </div>
              <div className="flex justify-between text-[12px]">
                <span className="text-text-secondary">After payment</span>
                <span className={budgetExceeded ? 'text-risk-high font-bold' : 'text-text-primary'}>
                  {'₹'}{fmt(budgetAfter)}
                </span>
              </div>
              {budgetExceeded && (
                <div className="flex justify-between text-[12px]">
                  <span className="text-risk-high font-semibold">Budget exceeded</span>
                  <span className="text-risk-high font-bold">{'₹'}{fmt(budgetAfter - expense.monthlyBudget)}</span>
                </div>
              )}
            </>
          )}
          {payTier === 3 && budgetExceeded && (
            <>
              <div className="border-t border-border my-2" />
              <div className="flex justify-between text-[12px]">
                <span className="text-text-secondary">DebtSpiral impact</span>
                <span className="text-risk-high font-bold">HIGH</span>
              </div>
            </>
          )}
        </div>

        <p className="text-[9px] text-text-tertiary text-center mb-4">Simulated payment · No real bank debit occurs</p>

        <PayNowButton state={displayState} amount={payAmount} onClick={handlePay} disabled={loading.txn} />
      </div>
    </div>
  );
}
