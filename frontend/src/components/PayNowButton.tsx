import type { PayButtonState } from '../store/session';

const STATE_STYLES: Record<PayButtonState, { bg: string; label: string; sub?: string }> = {
  safe: { bg: 'bg-accent', label: 'PAY NOW' },
  warning: { bg: 'bg-[#D97706]', label: 'PAY NOW', sub: 'Budget nearly exceeded' },
  flagged: { bg: 'bg-[#DC2626]', label: 'PAY NOW', sub: 'DebtSpiral Alert' },
};

export default function PayNowButton({
  state, amount, onClick, disabled,
}: {
  state: PayButtonState; amount: number; onClick: () => void; disabled?: boolean;
}) {
  const s = STATE_STYLES[state];
  return (
    <div className="flex flex-col items-center gap-1">
      {s.sub && (
        <span className={`text-[11px] font-medium ${state === 'flagged' ? 'text-risk-high' : 'text-risk-elevated'}`}>
          {s.sub}
        </span>
      )}
      <button onClick={onClick} disabled={disabled}
        className={`${s.bg} w-full py-4 rounded-full text-white font-bold text-[16px] tracking-wide transition-all duration-300 active:scale-[0.97] disabled:opacity-50`}>
        {s.label} {amount > 0 && `₹${amount.toLocaleString('en-IN')}`}
      </button>
    </div>
  );
}
