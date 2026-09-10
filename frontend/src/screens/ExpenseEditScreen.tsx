import { useState } from 'react';
import { useSession, type TierLevel } from '../store/session';
import BackHeader from '../components/BackHeader';

export default function ExpenseEditScreen() {
  const editId = useSession((s) => s.editExpenseId);
  const expenses = useSession((s) => s.expenses);
  const updateExpense = useSession((s) => s.updateExpense);
  const setScreen = useSession((s) => s.setScreen);

  const expense = expenses.find((e) => e.id === editId);
  const [tier, setTier] = useState<TierLevel>(expense?.tier || 2);
  const [budget, setBudget] = useState(expense?.monthlyBudget?.toString() || '0');
  const [recurring, setRecurring] = useState(expense?.recurring ?? false);
  const [priority, setPriority] = useState(expense?.priority || 'medium');

  if (!expense) return <div className="p-5 pt-[50px] text-text-tertiary">Expense not found</div>;

  const handleSave = () => {
    updateExpense(expense.id, { tier, monthlyBudget: parseInt(budget) || 0, recurring, priority: priority as any });
    setScreen('tier-manage');
  };

  return (
    <div className="pb-4 bg-white">
      <BackHeader title="Edit Expense" to="tier-manage" />
      <div className="px-5 space-y-4">
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 flex items-center gap-3">
          <span className="text-[28px]">{expense.icon}</span>
          <div>
            <p className="text-[16px] font-bold text-text-primary">{expense.name}</p>
            <p className="text-[11px] text-text-secondary">Currently Tier {expense.tier}</p>
          </div>
        </div>

        <div>
          <label className="text-[11px] text-text-secondary uppercase tracking-wider">Tier</label>
          <div className="flex gap-2 mt-1.5">
            {([1, 2, 3] as TierLevel[]).map((t) => (
              <button key={t} onClick={() => setTier(t)}
                className={`flex-1 py-2.5 rounded-xl text-[12px] font-semibold border transition-all ${
                  t === tier ? 'bg-accent-light border-accent text-accent' : 'bg-gpay-surface border-border text-text-tertiary'
                }`}>Tier {t}</button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-[11px] text-text-secondary uppercase tracking-wider">Monthly Limit</label>
          <div className="flex items-center bg-gpay-surface rounded-xl border border-border mt-1.5 px-4">
            <span className="text-text-secondary text-[14px]">{'₹'}</span>
            <input type="number" value={budget} onChange={(e) => setBudget(e.target.value)}
              className="flex-1 bg-transparent py-3 px-2 text-[16px] text-text-primary outline-none tabular-nums" />
          </div>
        </div>

        <div className="flex items-center justify-between bg-gpay-surface rounded-xl border border-border px-4 py-3">
          <span className="text-[13px] text-text-primary">Recurring</span>
          <button onClick={() => setRecurring(!recurring)}
            className={`w-11 h-6 rounded-full transition-colors ${recurring ? 'bg-accent' : 'bg-gray-300'}`}>
            <div className={`w-5 h-5 bg-white rounded-full transition-transform mx-0.5 shadow ${recurring ? 'translate-x-5' : ''}`} />
          </button>
        </div>

        <div>
          <label className="text-[11px] text-text-secondary uppercase tracking-wider">Priority</label>
          <div className="grid grid-cols-4 gap-1.5 mt-1.5">
            {(['critical', 'high', 'medium', 'low'] as const).map((p) => (
              <button key={p} onClick={() => setPriority(p)}
                className={`py-2 rounded-lg text-[11px] font-medium capitalize border ${
                  p === priority ? 'bg-accent-light border-accent text-accent' : 'bg-gpay-surface border-border text-text-tertiary'
                }`}>{p}</button>
            ))}
          </div>
        </div>

        <button onClick={handleSave}
          className="w-full bg-accent py-3.5 rounded-full text-white font-bold text-[14px] mt-4 active:scale-[0.97] transition-transform">
          SAVE CHANGES
        </button>
      </div>
    </div>
  );
}
