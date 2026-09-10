import type { TierLevel } from '../store/session';

const TIER_STYLES: Record<TierLevel, { bg: string; text: string; label: string }> = {
  1: { bg: 'bg-accent/20', text: 'text-accent', label: 'T1' },
  2: { bg: 'bg-risk-moderate/20', text: 'text-risk-moderate', label: 'T2' },
  3: { bg: 'bg-risk-elevated/20', text: 'text-risk-elevated', label: 'T3' },
};

export default function TierBadge({ tier, small }: { tier: TierLevel; small?: boolean }) {
  const s = TIER_STYLES[tier];
  return (
    <span className={`${s.bg} ${s.text} font-bold rounded-md inline-flex items-center justify-center ${
      small ? 'text-[9px] px-1.5 py-0.5' : 'text-[10px] px-2 py-0.5'
    }`}>
      {s.label}
    </span>
  );
}
