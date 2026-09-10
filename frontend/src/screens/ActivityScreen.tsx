import { useSession } from '../store/session';
import TierBadge from '../components/TierBadge';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function ActivityScreen() {
  const transactions = useSession((s) => s.transactions);
  const expenses = useSession((s) => s.expenses);

  const today = new Date();
  const todayStr = today.toDateString();
  const yesterdayStr = new Date(Date.now() - 86400000).toDateString();

  const grouped: Record<string, typeof transactions> = {};
  transactions.forEach((tx) => {
    const d = new Date(tx.timestamp).toDateString();
    const label = d === todayStr ? 'Today' : d === yesterdayStr ? 'Yesterday' : new Date(tx.timestamp).toLocaleDateString('en-IN', { day: 'numeric', month: 'long' });
    if (!grouped[label]) grouped[label] = [];
    grouped[label].push(tx);
  });

  return (
    <div className="px-5 pt-[50px] pb-4 bg-white">
      <h1 className="text-[20px] font-bold text-text-primary mb-5">Activity</h1>
      {Object.entries(grouped).map(([date, txs]) => (
        <div key={date} className="mb-5">
          <p className="text-[11px] font-semibold text-text-tertiary uppercase tracking-wider mb-2">{date}</p>
          {txs.map((tx) => (
            <div key={tx.id} className="flex items-center gap-3 py-3 border-b border-border last:border-0">
              <div className="w-10 h-10 bg-gpay-surface rounded-full flex items-center justify-center text-[18px]">
                {expenses.find((e) => e.id === tx.category)?.icon || '💳'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-[13px] font-medium text-text-primary truncate">{tx.label}</p>
                  {tx.flagged && <span className="text-[9px] bg-red-50 text-risk-high px-1.5 py-0.5 rounded font-bold border border-red-200">FLAGGED</span>}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <TierBadge tier={tx.tier} small />
                  {tx.riskBefore != null && tx.riskAfter != null && (
                    <span className="text-[9px] text-risk-high font-medium">
                      Risk {tx.riskBefore} → {tx.riskAfter}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <p className="text-[14px] font-semibold text-text-primary tabular-nums">{'₹'}{fmt(tx.amount)}</p>
              </div>
            </div>
          ))}
        </div>
      ))}
      {transactions.length === 0 && (
        <div className="text-center py-10 text-text-tertiary text-[13px]">No transactions yet</div>
      )}
    </div>
  );
}
