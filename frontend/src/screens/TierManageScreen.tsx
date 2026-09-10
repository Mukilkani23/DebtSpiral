import { useSession, type TierLevel } from '../store/session';
import BackHeader from '../components/BackHeader';
import TierBadge from '../components/TierBadge';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

const TIER_LABELS: Record<TierLevel, string> = { 1: 'Essential', 2: 'Necessary', 3: 'Discretionary' };

export default function TierManageScreen() {
  const tierFilter = useSession((s) => s.tierManageFilter);
  const expenses = useSession((s) => s.expenses);
  const setScreen = useSession((s) => s.setScreen);
  const setEditExpenseId = useSession((s) => s.setEditExpenseId);
  const setTierManageFilter = useSession((s) => s.setTierManageFilter);

  const filtered = expenses.filter((e) => e.tier === tierFilter);
  const totalBudget = filtered.reduce((s, e) => s + e.monthlyBudget, 0);
  const totalSpent = filtered.reduce((s, e) => s + e.currentSpend, 0);

  return (
    <div className="pb-4 bg-white">
      <BackHeader title={`Tier ${tierFilter} — ${TIER_LABELS[tierFilter]}`} to="tiers" />
      <div className="flex gap-2 px-5 mb-4">
        {([1, 2, 3] as TierLevel[]).map((t) => (
          <button key={t} onClick={() => setTierManageFilter(t)}
            className={`flex-1 py-2 rounded-xl text-[12px] font-semibold border transition-colors ${
              t === tierFilter ? 'bg-accent-light border-accent text-accent' : 'bg-gpay-surface border-border text-text-tertiary'
            }`}>
            Tier {t}
          </button>
        ))}
      </div>
      <div className="px-5 mb-4">
        <div className="bg-white rounded-xl shadow-gpay border border-border p-3 flex justify-between">
          <div><p className="text-[10px] text-text-tertiary">Budget</p><p className="text-[16px] font-bold text-text-primary">{'₹'}{fmt(totalBudget)}</p></div>
          <div><p className="text-[10px] text-text-tertiary">Spent</p><p className={`text-[16px] font-bold ${totalSpent > totalBudget ? 'text-risk-high' : 'text-text-primary'}`}>{'₹'}{fmt(totalSpent)}</p></div>
          <div><p className="text-[10px] text-text-tertiary">Remaining</p><p className={`text-[16px] font-bold ${totalSpent > totalBudget ? 'text-risk-high' : 'text-risk-low'}`}>{'₹'}{fmt(Math.max(totalBudget - totalSpent, 0))}</p></div>
        </div>
      </div>
      <div className="px-5 space-y-2">
        {filtered.map((exp) => {
          const pct = exp.monthlyBudget > 0 ? Math.min(exp.currentSpend / exp.monthlyBudget * 100, 100) : 0;
          const over = exp.currentSpend > exp.monthlyBudget;
          return (
            <div key={exp.id} className="bg-white rounded-xl shadow-gpay border border-border p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[20px]">{exp.icon}</span>
                  <div>
                    <p className="text-[13px] font-medium text-text-primary">{exp.name}</p>
                    <div className="flex items-center gap-1.5">
                      <TierBadge tier={exp.tier} small />
                      <span className="text-[10px] text-text-tertiary">{exp.recurring ? 'Recurring' : 'One-time'} · {exp.priority}</span>
                    </div>
                  </div>
                </div>
                <button onClick={() => { setEditExpenseId(exp.id); setScreen('expense-edit'); }}
                  className="text-[11px] text-accent font-semibold bg-accent-light px-2.5 py-1 rounded-lg">EDIT</button>
              </div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-text-tertiary">{'₹'}{fmt(exp.currentSpend)} / {'₹'}{fmt(exp.monthlyBudget)}</span>
                {over && <span className="text-risk-high font-semibold">Over by {'₹'}{fmt(exp.currentSpend - exp.monthlyBudget)}</span>}
              </div>
              <div className="w-full bg-gpay-surface rounded-full h-1.5">
                <div className={`h-1.5 rounded-full ${over ? 'bg-risk-high' : 'bg-accent'}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && <p className="text-center text-[12px] text-text-tertiary py-6">No expenses in this tier</p>}
      </div>
    </div>
  );
}
