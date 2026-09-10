import { useState } from 'react';
import { useSession } from '../store/session';
import { api } from '../api/client';
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

  const handlePay = async () => {
    setSubmitted(true);
    setLoading('txn', true);

    let result: any = null;
    let newRisk = riskScore;
    let reasonCodes: any[] = [];
    let nudge: any = null;
    let flagged = false;

    const apiCategory = (() => {
      const catMap: Record<string, string> = {
        'friends': 'entertainment', 'chatgpt': 'subscription', 'entertainment': 'entertainment',
        'groceries': 'food_delivery', 'petrol': 'travel', 'medical': 'other',
        'wifi': 'subscription', 'recharge': 'subscription', 'insurance': 'other',
        'family': 'other', 'food_delivery': 'food_delivery',
      };
      return catMap[payCategory] || 'other';
    })();

    try {
      if (apiConnected) {
        result = await api.transaction({ persona_id: personaId, category: apiCategory, amount_inr: payAmount });
        flagged = result.flagged ?? false;
        newRisk = result.risk_after ?? result.risk_score ?? riskScore + (payTier === 3 ? 4 : 1);
        reasonCodes = result.reason_codes || [];
        nudge = result.nudge || null;
        if (result.shap) {
          useSession.setState({ shap: result.shap });
        }
        if (result.spiral_detected !== undefined) {
          useSession.setState({ spiralDetected: result.spiral_detected });
        }
      }
    } catch {}

    if (!result || newRisk === riskScore) {
      if (payTier === 3 && budgetExceeded) {
        flagged = true;
        newRisk = Math.min(riskScore + 4, 100);
        reasonCodes = [
          { code: 'TIER_3', label: 'Tier 3 Budget Exceeded', detail: `Discretionary budget exceeded by ₹${fmt(budgetAfter - (expense?.monthlyBudget || 0))}` },
          { code: 'LARGE_RELATIVE_TXN', label: 'Large Relative Transaction', detail: `₹${fmt(payAmount)} is significant relative to your monthly income` },
          { code: 'HIGH_UTILIZATION', label: 'High Credit Utilization', detail: 'Current utilization is above 60%' },
          { code: 'SPIRAL_TRAJECTORY', label: 'Spiral Trajectory', detail: 'Financial indicators show deteriorating pattern' },
        ];
        nudge = { message: `You spent ₹${fmt(payAmount)} on ${payContact?.name || payCategory}. Your Tier 3 budget has been exceeded. Current dues: ₹${fmt(82000)}. Consider reducing discretionary spending this week.` };
      } else if (budgetNearlyExceeded) {
        newRisk = Math.min(riskScore + 1, 100);
      }
    }

    const finalState = flagged ? 'flagged' : budgetNearlyExceeded ? 'warning' : 'safe';
    setLocalButtonState(finalState);
    setPayButtonState(finalState);

    const newBand = newRisk >= 70 ? 'HIGH' : newRisk >= 50 ? 'ELEVATED' : newRisk >= 30 ? 'MODERATE' : 'LOW';
    updateRisk(newRisk, newBand, reasonCodes, nudge);

    addTransaction({
      id: `tx_${Date.now()}`, label: payContact?.name || payCategory, amount: payAmount,
      category: payCategory, tier: payTier, timestamp: Date.now(), flagged,
      riskBefore: riskScore, riskAfter: newRisk,
    });

    setPayResult({ flagged, riskBefore: riskScore, riskAfter: newRisk, reasonCodes });
    setLoading('txn', false);
    setScreen('pay-success');
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
