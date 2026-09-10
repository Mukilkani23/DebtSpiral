import { useSession } from '../store/session';
import BackHeader from '../components/BackHeader';
import SpiralGauge from '../components/SpiralGauge';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

const TRAJECTORY = [
  { month: 1, score: 22, debt: 35000 },
  { month: 2, score: 28, debt: 39000 },
  { month: 3, score: 34, debt: 44000 },
  { month: 4, score: 41, debt: 50000 },
  { month: 5, score: 49, debt: 58000 },
  { month: 6, score: 56, debt: 64000 },
  { month: 7, score: 63, debt: 71000 },
  { month: 8, score: 72, debt: 78000 },
  { month: 9, score: 78, debt: 82000 },
  { month: 10, score: 82, debt: 86000 },
  { month: 11, score: 85, debt: 90000 },
  { month: 12, score: 87, debt: 94000 },
];

function barColor(v: number) {
  if (v >= 70) return '#EA4335';
  if (v >= 50) return '#F97316';
  if (v >= 30) return '#FBBC04';
  return '#34A853';
}

export default function DebtSpiralScreen() {
  const riskScore = useSession((s) => s.riskScore);
  const riskBand = useSession((s) => s.riskBand);
  const shap = useSession((s) => s.shap);
  const spiralDetected = useSession((s) => s.spiralDetected);
  const modelWarnedMonth = useSession((s) => s.modelWarnedMonth) || 5;
  const spiralConfirmedMonth = useSession((s) => s.spiralConfirmedMonth) || 8;
  const leadTimeMonths = useSession((s) => s.leadTimeMonths);
  const whatIfReduction = useSession((s) => s.whatIfReduction);
  const setWhatIfReduction = useSession((s) => s.setWhatIfReduction);
  const reasonCodes = useSession((s) => s.reasonCodes);

  const currentDebt = 82000;
  const monthlyDebtGrowth = 12000;
  const projMonths = 6;
  const projectedNoChange = currentDebt + monthlyDebtGrowth * projMonths;
  const savingsMultiplier = 2.5;
  const projectedWithChange = Math.max(0, projectedNoChange - whatIfReduction * projMonths * savingsMultiplier);
  const avoided = projectedNoChange - projectedWithChange;

  const maxScore = Math.max(...TRAJECTORY.map(t => t.score));
  const chartH = 120;

  return (
    <div className="pb-6 bg-white">
      <BackHeader title="DebtSpiral Intelligence" to="home" />

      <div className="px-5">
        {/* Gauge */}
        <div className="flex justify-center mb-4 relative h-[170px]">
          <SpiralGauge size={170} />
        </div>

        {spiralDetected && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-5 text-center">
            <p className="text-[13px] font-semibold text-risk-high">Entering Financial Spiral</p>
            <p className="text-[11px] text-text-secondary mt-1">
              Model warned month {modelWarnedMonth} · Confirmed month {spiralConfirmedMonth} · Lead: {leadTimeMonths} months
            </p>
          </div>
        )}

        {/* SHAP — Model-Level Explanation */}
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4">
          <p className="text-[14px] font-semibold text-text-primary mb-1">Why Am I At Risk?</p>
          <p className="text-[11px] text-text-tertiary mb-3">Model-level SHAP feature attribution</p>
          {shap?.items.map((item: any) => {
            const maxShap = Math.max(...shap.items.map((x: any) => Math.abs(x.shap)));
            const pct = (Math.abs(item.shap) / maxShap) * 100;
            return (
              <div key={item.feature} className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] text-text-primary">{item.display_name}</span>
                  <span className={`text-[12px] font-bold tabular-nums ${item.direction === '+' ? 'text-risk-high' : 'text-risk-low'}`}>
                    {item.direction === '+' ? '+' : '-'}{Math.abs(item.shap).toFixed(2)}
                  </span>
                </div>
                <div className="w-full h-2 bg-gpay-surface rounded-full">
                  <div className={`h-2 rounded-full transition-all ${item.direction === '+' ? 'bg-risk-high' : 'bg-risk-low'}`}
                    style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
          <p className="text-[10px] text-text-tertiary mt-2 italic">
            These are aggregated financial features — no individual transaction data crosses the model boundary.
          </p>
        </div>

        {/* Transaction-level reason codes — separate from SHAP */}
        {reasonCodes.length > 0 && (
          <div className="bg-red-50 rounded-xl border border-red-200 p-4 mb-4">
            <p className="text-[14px] font-semibold text-risk-high mb-2">Transaction Flags</p>
            <p className="text-[11px] text-text-secondary mb-2">Why your recent transaction was flagged</p>
            {reasonCodes.map((rc: any, i: number) => (
              <div key={i} className="flex items-start gap-2 py-1.5">
                <span className="text-risk-high text-[10px] mt-1">{'●'}</span>
                <div>
                  <p className="text-[12px] font-medium text-text-primary">{rc.label || rc.code}</p>
                  {rc.detail && <p className="text-[11px] text-text-secondary">{rc.detail}</p>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Trajectory Chart — 12 months */}
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4">
          <p className="text-[14px] font-semibold text-text-primary mb-1">Risk Trajectory</p>
          <p className="text-[11px] text-text-tertiary mb-3">12-month risk score progression</p>

          <div className="relative" style={{ height: chartH + 30 }}>
            {/* Bars */}
            <div className="flex items-end gap-[6px] px-1" style={{ height: chartH }}>
              {TRAJECTORY.map((t) => {
                const h = (t.score / maxScore) * chartH;
                const isWarn = t.month === modelWarnedMonth;
                const isConfirm = t.month === spiralConfirmedMonth;
                return (
                  <div key={t.month} className="flex-1 flex flex-col items-center justify-end relative">
                    {/* Event markers */}
                    {isWarn && (
                      <div className="absolute -top-[18px] left-1/2 -translate-x-1/2 whitespace-nowrap">
                        <div className="bg-risk-moderate text-white text-[7px] font-bold px-1 py-0.5 rounded">Model Warned</div>
                        <div className="w-0 h-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-risk-moderate mx-auto" />
                      </div>
                    )}
                    {isConfirm && (
                      <div className="absolute -top-[18px] left-1/2 -translate-x-1/2 whitespace-nowrap">
                        <div className="bg-risk-high text-white text-[7px] font-bold px-1 py-0.5 rounded">Rule Confirmed</div>
                        <div className="w-0 h-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-risk-high mx-auto" />
                      </div>
                    )}
                    <div className="text-[7px] text-text-secondary font-bold mb-0.5 tabular-nums">{t.score}</div>
                    <div className="w-full rounded-t-sm" style={{ height: h, backgroundColor: barColor(t.score) }} />
                  </div>
                );
              })}
            </div>
            {/* Month labels */}
            <div className="flex gap-[6px] px-1 mt-1">
              {TRAJECTORY.map((t) => (
                <div key={t.month} className="flex-1 text-center text-[8px] text-text-tertiary tabular-nums">
                  M{t.month}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 mt-3 pt-2 border-t border-border">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 bg-risk-moderate rounded-full" />
              <span className="text-[10px] text-text-secondary">Model Warned (M{modelWarnedMonth})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 bg-risk-high rounded-full" />
              <span className="text-[10px] text-text-secondary">Rule Confirmed (M{spiralConfirmedMonth})</span>
            </div>
          </div>
        </div>

        {/* What-If Projection */}
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4">
          <p className="text-[14px] font-semibold text-text-primary mb-1">What Happens Next?</p>
          <p className="text-[11px] text-text-tertiary mb-4">Adjust discretionary spending reduction to see projected impact</p>

          {/* Slider */}
          <div className="mb-4">
            <div className="flex justify-between text-[11px] text-text-secondary mb-2">
              <span>Monthly reduction</span>
              <span className="font-bold text-accent">{'₹'}{fmt(whatIfReduction)}/mo</span>
            </div>
            <input
              type="range"
              min={0}
              max={5000}
              step={250}
              value={whatIfReduction}
              onChange={(e) => setWhatIfReduction(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-[9px] text-text-tertiary mt-1">
              <span>{'₹'}0</span>
              <span>{'₹'}2,500</span>
              <span>{'₹'}5,000</span>
            </div>
          </div>

          {/* Projection comparison chart */}
          <div className="flex items-end gap-8 justify-center mb-4 h-[100px]">
            <div className="flex flex-col items-center">
              <div className="text-[10px] text-text-secondary mb-1">Without Change</div>
              <div className="w-16 bg-risk-high/20 rounded-t flex items-end justify-center"
                style={{ height: `${(projectedNoChange / projectedNoChange) * 80}px` }}>
                <div className="w-full bg-risk-high rounded-t" style={{ height: '100%' }} />
              </div>
            </div>
            <div className="flex flex-col items-center">
              <div className="text-[10px] text-text-secondary mb-1">With Change</div>
              <div className="w-16 bg-risk-low/20 rounded-t flex items-end justify-center"
                style={{ height: `${Math.max((projectedWithChange / projectedNoChange) * 80, 8)}px` }}>
                <div className="w-full bg-risk-low rounded-t" style={{ height: '100%' }} />
              </div>
            </div>
          </div>

          {/* Projection cards */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-red-50 rounded-xl p-3 border border-red-200">
              <p className="text-[10px] text-text-secondary mb-1">Without Change</p>
              <p className="text-[20px] font-bold text-risk-high tabular-nums">{'₹'}{fmt(Math.round(projectedNoChange))}</p>
              <p className="text-[10px] text-text-tertiary">Projected debt (6mo)</p>
            </div>
            <div className="bg-green-50 rounded-xl p-3 border border-green-200">
              <p className="text-[10px] text-text-secondary mb-1">With Change</p>
              <p className="text-[20px] font-bold text-risk-low tabular-nums">{'₹'}{fmt(Math.round(projectedWithChange))}</p>
              <p className="text-[10px] text-text-tertiary">Projected debt (6mo)</p>
            </div>
          </div>

          {/* Avoided debt */}
          {whatIfReduction > 0 && (
            <div className="bg-green-50 rounded-xl p-3 text-center border border-green-200">
              <p className="text-[10px] text-text-secondary mb-0.5">Potentially avoided debt</p>
              <p className="text-[18px] font-bold text-risk-low tabular-nums">{'₹'}{fmt(Math.round(avoided))}</p>
            </div>
          )}

          {whatIfReduction === 0 && (
            <p className="text-[11px] text-text-tertiary text-center italic">
              Move the slider to see how reducing discretionary spending changes your trajectory
            </p>
          )}
        </div>

        {/* Privacy */}
        <div className="text-center text-[10px] text-text-tertiary px-4 py-2">
          Every feature is a ratio or a trend. No merchant names, no identity, no raw transactions cross the aggregation boundary.
        </div>
      </div>
    </div>
  );
}
