import { useSession } from '../store/session';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function HomeScreen() {
  const setScreen = useSession((s) => s.setScreen);
  const riskScore = useSession((s) => s.riskScore);
  const riskBand = useSession((s) => s.riskBand);
  const bankBalance = useSession((s) => s.bankBalance);
  const contacts = useSession((s) => s.contacts);
  const personaId = useSession((s) => s.personaId);
  const transactions = useSession((s) => s.transactions);

  const peopleContacts = contacts.filter((c) => !['swiggy', 'zomato', 'flipkart', 'petrol_bunk', 'apollo'].includes(c.id));
  const billServices = [
    { id: 'recharge', name: 'Mobile recharge', icon: '📱', color: 'bg-blue-50' },
    { id: 'electricity', name: 'Electricity', icon: '💡', color: 'bg-yellow-50' },
    { id: 'wifi', name: 'DTH / Cable TV', icon: '📺', color: 'bg-purple-50' },
    { id: 'insurance', name: 'Insurance', icon: '🛡️', color: 'bg-green-50' },
  ];

  const bandColorText: Record<string, string> = {
    LOW: 'text-risk-low', MODERATE: 'text-risk-moderate',
    ELEVATED: 'text-risk-elevated', HIGH: 'text-risk-high',
  };
  const bandColorBg: Record<string, string> = {
    LOW: 'bg-risk-low', MODERATE: 'bg-risk-moderate',
    ELEVATED: 'bg-risk-elevated', HIGH: 'bg-risk-high',
  };

  return (
    <div className="pt-[50px] pb-4">
      {/* Search bar */}
      <div className="px-4 mb-4">
        <div className="flex items-center gap-3 bg-gpay-surface rounded-full px-4 py-3 shadow-gpay">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9AA0A6" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <span className="text-[14px] text-text-tertiary flex-1">Pay friends and merchants</span>
          <button onClick={() => setScreen('settings')}
            className="w-8 h-8 bg-accent rounded-full flex items-center justify-center text-white font-bold text-[13px]">
            {personaId}
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-4 gap-4 px-6 mb-6">
        {[
          { icon: '⬜', label: 'Scan any\nQR code', action: () => {} },
          { icon: '₹', label: 'Pay\nanyone', action: () => setScreen('pay') },
          { icon: '🏦', label: 'Bank\ntransfer', action: () => {} },
          { icon: '📱', label: 'Mobile\nrecharge', action: () => setScreen('pay') },
        ].map((a, i) => (
          <button key={i} onClick={a.action} className="flex flex-col items-center gap-2">
            <div className="w-[52px] h-[52px] bg-accent-light rounded-2xl flex items-center justify-center">
              {a.icon === '₹' ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1A73E8" strokeWidth="2" strokeLinecap="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
              ) : a.icon === '⬜' ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1A73E8" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
              ) : a.icon === '🏦' ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1A73E8" strokeWidth="2" strokeLinecap="round"><path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/></svg>
              ) : (
                <span className="text-[22px]">{a.icon}</span>
              )}
            </div>
            <span className="text-[11px] text-text-primary text-center leading-tight whitespace-pre-line">{a.label}</span>
          </button>
        ))}
      </div>

      {/* DebtSpiral Card */}
      <div className="px-4 mb-5">
        <button onClick={() => setScreen('debtspiral')}
          className="w-full flex items-center gap-3 p-4 rounded-2xl shadow-gpay border border-border bg-white active:bg-gpay-surface transition-colors">
          <div className={`w-11 h-11 ${bandColorBg[riskBand]} rounded-full flex items-center justify-center`}>
            <span className="text-white font-bold text-[14px]">{riskScore}</span>
          </div>
          <div className="flex-1 text-left">
            <p className="text-[14px] font-semibold text-text-primary">DebtSpiral</p>
            <p className="text-[12px] text-text-secondary">Risk: <span className={`font-semibold ${bandColorText[riskBand]}`}>{riskBand}</span> · Tap for insights</p>
          </div>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9AA0A6" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>

      {/* People */}
      <div className="px-4 mb-5">
        <p className="text-[16px] font-semibold text-text-primary mb-3">People</p>
        <div className="grid grid-cols-4 gap-4">
          {peopleContacts.slice(0, 4).map((c) => (
            <button key={c.id} onClick={() => {
              useSession.getState().setPayContact(c);
              useSession.getState().setPayCategory(c.defaultCategory);
              useSession.getState().setPayTier(c.defaultTier);
              setScreen('contact-pay');
            }}
              className="flex flex-col items-center gap-2">
              <div className="w-[52px] h-[52px] bg-accent-light rounded-full flex items-center justify-center text-accent font-bold text-[18px]">
                {c.avatar}
              </div>
              <span className="text-[11px] text-text-primary text-center truncate w-full">{c.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Bills & recharges */}
      <div className="px-4 mb-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[16px] font-semibold text-text-primary">Bills & recharges</p>
          <button className="text-[13px] text-accent font-medium flex items-center gap-1">
            Manage
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
        <div className="grid grid-cols-4 gap-4">
          {billServices.map((b) => (
            <button key={b.id} onClick={() => setScreen('pay')}
              className="flex flex-col items-center gap-2">
              <div className={`w-[52px] h-[52px] ${b.color} rounded-full flex items-center justify-center text-[22px]`}>
                {b.icon}
              </div>
              <span className="text-[11px] text-text-primary text-center leading-tight">{b.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Businesses */}
      <div className="px-4 mb-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[16px] font-semibold text-text-primary">Businesses</p>
          <button className="text-[13px] text-accent font-medium flex items-center gap-1">
            Explore
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
        <div className="grid grid-cols-4 gap-4">
          {contacts.filter(c => ['swiggy', 'zomato', 'flipkart'].includes(c.id)).map((c) => (
            <button key={c.id} onClick={() => {
              useSession.getState().setPayContact(c);
              useSession.getState().setPayCategory(c.defaultCategory);
              useSession.getState().setPayTier(c.defaultTier);
              setScreen('contact-pay');
            }}
              className="flex flex-col items-center gap-2">
              <div className="w-[52px] h-[52px] bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-[18px]">
                {c.avatar}
              </div>
              <span className="text-[11px] text-text-primary text-center truncate w-full">{c.name}</span>
            </button>
          ))}
          <button className="flex flex-col items-center gap-2">
            <div className="w-[52px] h-[52px] bg-gpay-surface rounded-full flex items-center justify-center border border-border">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9AA0A6" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <span className="text-[11px] text-text-primary text-center">More</span>
          </button>
        </div>
      </div>

      {/* Manage your money */}
      <div className="px-4 mb-4">
        <p className="text-[16px] font-semibold text-text-primary mb-3">Manage your money</p>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <button onClick={() => setScreen('tiers')}
            className="bg-white rounded-xl p-4 shadow-gpay border border-border text-left">
            <p className="text-[11px] text-accent font-medium mb-1">Expense Tiers</p>
            <p className="text-[13px] font-semibold text-text-primary">Track spending</p>
            <p className="text-[11px] text-text-secondary mt-1">3-tier budget system</p>
          </button>
          <button onClick={() => setScreen('debtspiral')}
            className="bg-white rounded-xl p-4 shadow-gpay border border-border text-left">
            <p className="text-[11px] text-accent font-medium mb-1">Predictions</p>
            <p className="text-[13px] font-semibold text-text-primary">What-If analysis</p>
            <p className="text-[11px] text-text-secondary mt-1">See future impact</p>
          </button>
        </div>

        {/* Action items */}
        <div className="bg-white rounded-xl shadow-gpay border border-border divide-y divide-border">
          <button onClick={() => setScreen('activity')} className="w-full flex items-center gap-3 px-4 py-3.5">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5F6368" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span className="text-[13px] text-text-primary flex-1 text-left">See transaction history</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9AA0A6" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
          <button onClick={() => setScreen('tiers')} className="w-full flex items-center gap-3 px-4 py-3.5">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5F6368" strokeWidth="2"><rect x="1" y="4" width="22" height="16" rx="2"/><path d="M1 10h22"/></svg>
            <span className="text-[13px] text-text-primary flex-1 text-left">Check bank balance</span>
            <span className="text-[13px] font-semibold text-text-primary">{'₹'}{fmt(bankBalance)}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
