import { useSession, useTierTotals } from '../store/session';
import BackHeader from '../components/BackHeader';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function TiersScreen() {
  const setScreen = useSession((s) => s.setScreen);
  const monthlyIncome = useSession((s) => s.monthlyIncome);
  const expenses = useSession((s) => s.expenses);
  const { t1, t2, t3, t1Spent, t2Spent, t3Spent, totalPlanned } = useTierTotals();

  const tiers = [
    { level: 1 as const, label: 'Essential', desc: 'Non-negotiable', budget: t1, spent: t1Spent, textClass: 'text-accent', barClass: 'bg-accent', bgClass: 'bg-blue-50 border-blue-200', items: expenses.filter((e) => e.tier === 1) },
    { level: 2 as const, label: 'Necessary', desc: 'Adjustable', budget: t2, spent: t2Spent, textClass: 'text-risk-moderate', barClass: 'bg-risk-moderate', bgClass: 'bg-yellow-50 border-yellow-200', items: expenses.filter((e) => e.tier === 2) },
    { level: 3 as const, label: 'Discretionary', desc: 'Optional', budget: t3, spent: t3Spent, textClass: 'text-risk-elevated', barClass: 'bg-risk-elevated', bgClass: 'bg-orange-50 border-orange-200', items: expenses.filter((e) => e.tier === 3) },
  ];

  return (
    <div className="pb-4 bg-white">
      <BackHeader title="Expense Tiers" to="home" />
      <div className="px-5 mb-4">
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4">
          <div className="flex justify-between items-center mb-2">
            <p className="text-[11px] text-text-secondary">Monthly Income</p>
            <p className="text-[18px] font-bold text-text-primary">{'₹'}{fmt(monthlyIncome)}</p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="bg-gpay-surface rounded-lg p-2">
              <p className="text-[10px] text-text-tertiary">Total Planned</p>
              <p className="text-[14px] font-bold text-text-primary">{'₹'}{fmt(totalPlanned)}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-2">
              <p className="text-[10px] text-text-tertiary">Flexible</p>
              <p className="text-[14px] font-bold text-risk-low">{'₹'}{fmt(monthlyIncome - totalPlanned)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 space-y-3">
        {tiers.map((tier) => {
          const pct = tier.budget > 0 ? Math.min(tier.spent / tier.budget * 100, 100) : 0;
          const over = tier.spent > tier.budget;
          return (
            <div key={tier.level} className={`rounded-xl p-4 border ${tier.bgClass}`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className={`text-[14px] font-bold ${tier.textClass}`}>TIER {tier.level}</p>
                  <p className="text-[11px] text-text-secondary">{tier.label} / {tier.desc}</p>
                </div>
                <button onClick={() => { useSession.getState().setTierManageFilter(tier.level); setScreen('tier-manage'); }}
                  className="text-[11px] text-accent font-semibold bg-accent-light px-3 py-1.5 rounded-lg">
                  MANAGE
                </button>
              </div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Budget: {'₹'}{fmt(tier.budget)}</span>
                <span className={over ? 'text-risk-high font-semibold' : 'text-text-secondary'}>Spent: {'₹'}{fmt(tier.spent)}</span>
              </div>
              <div className="w-full bg-white/50 rounded-full h-2 mb-2">
                <div className={`h-2 rounded-full transition-all ${over ? 'bg-risk-high' : tier.barClass}`} style={{ width: `${pct}%` }} />
              </div>
              {tier.level !== 1 && (
                <p className="text-[10px] text-text-secondary">
                  Remaining: {'₹'}{fmt(Math.max(tier.budget - tier.spent, 0))}
                  {over && <span className="text-risk-high font-medium"> (over by {'₹'}{fmt(tier.spent - tier.budget)})</span>}
                </p>
              )}
              <div className="flex flex-wrap gap-1.5 mt-2">
                {tier.items.map((e) => (
                  <span key={e.id} className="text-[10px] bg-white/70 px-2 py-0.5 rounded-md text-text-secondary border border-border">
                    {e.icon} {e.name}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
