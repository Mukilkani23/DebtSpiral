import { useSession } from '../store/session';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function PaySuccessScreen() {
  const payContact = useSession((s) => s.payContact);
  const payAmount = useSession((s) => s.payAmount);
  const payTier = useSession((s) => s.payTier);
  const payResult = useSession((s) => s.payResult);
  const riskBand = useSession((s) => s.riskBand);
  const bankBalance = useSession((s) => s.bankBalance);
  const expenses = useSession((s) => s.expenses);
  const setScreen = useSession((s) => s.setScreen);
  const reasonCodes = useSession((s) => s.reasonCodes);
  const payCategory = useSession((s) => s.payCategory);
  const expense = expenses.find((e) => e.id === payCategory);

  const bandColor: Record<string, string> = {
    LOW: 'text-risk-low', MODERATE: 'text-risk-moderate',
    ELEVATED: 'text-risk-elevated', HIGH: 'text-risk-high',
  };

  return (
    <div className="px-5 pt-[50px] pb-6 flex flex-col items-center bg-white">
      <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-4 ${
        payResult?.flagged ? 'bg-red-50' : 'bg-green-50'
      }`}>
        <span className="text-[36px]">{payResult?.flagged ? '⚠️' : '✓'}</span>
      </div>

      <p className={`text-[16px] font-semibold ${payResult?.flagged ? 'text-risk-high' : 'text-risk-low'}`}>
        Payment {payResult?.flagged ? 'Completed with Warning' : 'Successful'}
      </p>

      <p className="text-[32px] font-bold text-text-primary mt-2 tabular-nums">{'₹'}{fmt(payAmount)}</p>
      <p className="text-[13px] text-text-secondary mt-1">Paid to {payContact?.name}</p>

      <div className="w-full mt-6 space-y-3">
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4">
          <div className="flex justify-between text-[12px] mb-2">
            <span className="text-text-secondary">Remaining balance</span>
            <span className="text-text-primary font-semibold">{'₹'}{fmt(bankBalance)}</span>
          </div>
          {expense && (
            <div className="flex justify-between text-[12px]">
              <span className="text-text-secondary">Tier {payTier} spent</span>
              <span className={expense.currentSpend > expense.monthlyBudget ? 'text-risk-high font-bold' : 'text-text-primary'}>
                {'₹'}{fmt(expense.currentSpend)} / {'₹'}{fmt(expense.monthlyBudget)}
              </span>
            </div>
          )}
        </div>

        {payResult && (
          <div className={`rounded-xl p-4 border ${
            payResult.flagged ? 'bg-red-50 border-red-200' : 'bg-white shadow-gpay border-border'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[12px] text-text-secondary">DebtSpiral Risk</span>
              <div className="flex items-center gap-2">
                <span className="text-[14px] text-text-secondary">{payResult.riskBefore}</span>
                <span className="text-text-tertiary">→</span>
                <span className={`text-[18px] font-bold ${bandColor[riskBand]}`}>{payResult.riskAfter}</span>
              </div>
            </div>
            {payResult.flagged && reasonCodes.length > 0 && (
              <div className="border-t border-border pt-2 mt-2">
                <p className="text-[11px] text-risk-high font-semibold mb-1.5">Risk increased because:</p>
                {reasonCodes.slice(0, 4).map((rc: any, i: number) => (
                  <div key={i} className="flex items-start gap-1.5 py-0.5">
                    <span className="text-risk-high text-[8px] mt-1">●</span>
                    <span className="text-[11px] text-text-secondary">{rc.label || rc.code}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="w-full mt-6 space-y-2">
        {payResult?.flagged && (
          <button onClick={() => setScreen('debtspiral')}
            className="w-full bg-red-50 border border-red-200 py-3 rounded-full text-risk-high font-bold text-[13px]">
            View DebtSpiral
          </button>
        )}
        <button onClick={() => setScreen('home')}
          className="w-full bg-accent py-3 rounded-full text-white font-bold text-[13px]">
          Done
        </button>
      </div>

      <p className="text-[9px] text-text-tertiary mt-4">Simulated payment · No real bank debit occurred</p>
    </div>
  );
}
