import { useState } from 'react';
import { useSession, type TierLevel } from '../store/session';
import BackHeader from '../components/BackHeader';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function PayScreen() {
  const contacts = useSession((s) => s.contacts);
  const expenses = useSession((s) => s.expenses);
  const setScreen = useSession((s) => s.setScreen);
  const setPayContact = useSession((s) => s.setPayContact);
  const setPayAmount = useSession((s) => s.setPayAmount);
  const setPayCategory = useSession((s) => s.setPayCategory);
  const setPayTier = useSession((s) => s.setPayTier);
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [tier, setTier] = useState<TierLevel>(3);

  const filtered = search
    ? contacts.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()))
    : contacts;

  const selected = contacts.find((c) => c.id === selectedId);

  const handleProceed = () => {
    if (!selected || !amount) return;
    const cat = category || selected.defaultCategory;
    setPayContact(selected);
    setPayAmount(parseInt(amount));
    setPayCategory(cat);
    setPayTier(tier);
    setScreen('pay-confirm');
  };

  const matchedExpense = expenses.find((e) => e.id === (category || selected?.defaultCategory));
  const budgetInfo = matchedExpense ? {
    budget: matchedExpense.monthlyBudget,
    spent: matchedExpense.currentSpend,
    after: matchedExpense.currentSpend + (parseInt(amount) || 0),
  } : null;

  return (
    <div className="pb-4 bg-white">
      <BackHeader title="Pay" to="home" />
      <div className="px-5">
        <div className="bg-gpay-surface rounded-full border border-border px-4 py-2.5 mb-4">
          <input type="text" placeholder="Search people / contacts" value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-transparent text-[13px] text-text-primary outline-none placeholder:text-text-tertiary" />
        </div>

        {!selectedId && (
          <div className="space-y-1 mb-4">
            {filtered.map((c) => (
              <button key={c.id} onClick={() => { setSelectedId(c.id); setCategory(c.defaultCategory); setTier(c.defaultTier); }}
                className="w-full flex items-center gap-3 py-3 px-3 rounded-xl hover:bg-gpay-surface transition-colors">
                <div className="w-10 h-10 bg-accent-light rounded-full flex items-center justify-center text-accent font-bold text-[14px]">
                  {c.avatar}
                </div>
                <p className="text-[13px] font-medium text-text-primary">{c.name}</p>
              </button>
            ))}
          </div>
        )}

        {selected && (
          <>
            <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4 flex items-center gap-3">
              <div className="w-12 h-12 bg-accent-light rounded-full flex items-center justify-center text-accent font-bold text-[18px]">
                {selected.avatar}
              </div>
              <div className="flex-1">
                <p className="text-[15px] font-semibold text-text-primary">{selected.name}</p>
                <p className="text-[11px] text-text-secondary">{category || selected.defaultCategory}</p>
              </div>
              <button onClick={() => setSelectedId(null)} className="text-accent text-[11px] font-medium">Change</button>
            </div>

            <div className="mb-4">
              <label className="text-[11px] text-text-secondary uppercase tracking-wider">Amount</label>
              <div className="flex items-center bg-gpay-surface rounded-xl border border-border mt-1.5 px-4">
                <span className="text-text-secondary text-[18px]">{'₹'}</span>
                <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0"
                  className="flex-1 bg-transparent py-3 px-2 text-[24px] font-bold text-text-primary outline-none tabular-nums" />
              </div>
            </div>

            <div className="mb-4">
              <label className="text-[11px] text-text-secondary uppercase tracking-wider">Category</label>
              <select value={category} onChange={(e) => {
                setCategory(e.target.value);
                const exp = expenses.find((x) => x.id === e.target.value);
                if (exp) setTier(exp.tier);
              }}
                className="w-full bg-gpay-surface rounded-xl border border-border mt-1.5 px-4 py-3 text-[13px] text-text-primary outline-none">
                {expenses.map((e) => (
                  <option key={e.id} value={e.id}>{e.icon} {e.name} (T{e.tier})</option>
                ))}
              </select>
            </div>

            {budgetInfo && parseInt(amount) > 0 && (
              <div className={`rounded-xl p-3 mb-4 border ${
                budgetInfo.after > budgetInfo.budget
                  ? 'bg-red-50 border-red-200'
                  : budgetInfo.after > budgetInfo.budget * 0.8
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-gpay-surface border-border'
              }`}>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-text-secondary">Monthly budget</span>
                  <span className="text-text-primary font-medium">{'₹'}{fmt(budgetInfo.budget)}</span>
                </div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-text-secondary">Already spent</span>
                  <span className="text-text-primary">{'₹'}{fmt(budgetInfo.spent)}</span>
                </div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-text-secondary">After payment</span>
                  <span className={budgetInfo.after > budgetInfo.budget ? 'text-risk-high font-bold' : 'text-text-primary'}>
                    {'₹'}{fmt(budgetInfo.after)}
                  </span>
                </div>
                {budgetInfo.after > budgetInfo.budget && (
                  <p className="text-[11px] text-risk-high font-semibold mt-1">
                    Budget exceeded by {'₹'}{fmt(budgetInfo.after - budgetInfo.budget)}
                  </p>
                )}
              </div>
            )}

            <button onClick={handleProceed} disabled={!amount || parseInt(amount) <= 0}
              className="w-full bg-accent py-3.5 rounded-full text-white font-bold text-[14px] disabled:opacity-40 active:scale-[0.97] transition-transform">
              CONTINUE
            </button>
          </>
        )}
      </div>
    </div>
  );
}
