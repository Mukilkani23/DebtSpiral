import { useSession } from '../store/session';

const BAND_COLORS: Record<string, string> = {
  LOW: '#34A853',
  MODERATE: '#FBBC04',
  ELEVATED: '#F97316',
  HIGH: '#EA4335',
};

export default function SpiralGauge({ size = 160 }: { size?: number }) {
  const riskScore = useSession((s) => s.riskScore);
  const riskBand = useSession((s) => s.riskBand);
  const color = BAND_COLORS[riskBand] || BAND_COLORS.HIGH;
  const r = (size - 16) / 2;
  const circ = 2 * Math.PI * r;
  const arc = circ * 0.75;
  const progress = (riskScore / 100) * arc;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-[135deg]">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#E8EAED" strokeWidth="10"
          strokeDasharray={`${arc} ${circ}`} strokeLinecap="round" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${progress} ${circ}`} strokeLinecap="round"
          className="transition-all duration-700" />
      </svg>
      <div className="absolute flex flex-col items-center" style={{ marginTop: size * 0.28 }}>
        <span className="text-[36px] font-bold tabular-nums" style={{ color }}>{riskScore}</span>
        <span className="text-[11px] font-semibold tracking-wider" style={{ color }}>{riskBand}</span>
      </div>
    </div>
  );
}
