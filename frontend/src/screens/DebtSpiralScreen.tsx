import { useEffect, useCallback, useRef } from 'react';
import { useSession } from '../store/session';
import { api } from '../api/client';
import BackHeader from '../components/BackHeader';
import SpiralGauge from '../components/SpiralGauge';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

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
  const modelWarnedMonth = useSession((s) => s.modelWarnedMonth);
  const spiralConfirmedMonth = useSession((s) => s.spiralConfirmedMonth);
  const leadTimeMonths = useSession((s) => s.leadTimeMonths);
  const whatIfReduction = useSession((s) => s.whatIfReduction);
  const setWhatIfReduction = useSession((s) => s.setWhatIfReduction);
  const reasonCodes = useSession((s) => s.reasonCodes);
  const personaId = useSession((s) => s.personaId);
  const personaHistory = useSession((s) => s.personaHistory);
  const projection = useSession((s) => s.projection);
  const setProjection = useSession((s) => s.setProjection);
  const apiConnected = useSession((s) => s.apiConnected);
  const setLoading = useSession((s) => s.setLoading);
  const loading = useSession((s) => s.loading);

  const trajectory = personaHistory.map((snap: any) => ({
    month: snap.month_index,
    debt: snap.outstanding_debt_inr,
  }));

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchProjection = useCallback((reduction: number) => {
    if (!apiConnected) return;
    setLoading('project', true);
    api.project({
      persona_id: personaId,
      levers: {
        discretionary_reduction_inr: reduction,
        repayment_increase_inr: 0,
        stc_reduction_count: 0,
      },
    }).then((data) => {
      setProjection(data);
      setLoading('project', false);
    }).catch(() => setLoading('project', false));
  }, [apiConnected, personaId]);

  useEffect(() => {
    fetchProjection(whatIfReduction);
  }, [personaId]);

  const handleSliderChange = (val: number) => {
    setWhatIfReduction(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchProjection(val), 300);
  };

  const lastDebt = personaHistory.length > 0
    ? personaHistory[personaHistory.length - 1].outstanding_debt_inr
    : 82000;

  const projectedNoChange = projection?.scenario_a?.debt?.[2] ?? lastDebt;
  const projectedWithChange = projection?.scenario_b?.debt?.[2] ?? projectedNoChange;
  const avoided = projectedNoChange - projectedWithChange;

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

        {/* Trajectory Chart — Debt over months */}
        {trajectory.length > 0 && (
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4">
          <p className="text-[14px] font-semibold text-text-primary mb-1">Debt Trajectory</p>
          <p className="text-[11px] text-text-tertiary mb-3">Outstanding debt by month</p>

          {(() => {
            const maxDebt = Math.max(...trajectory.map((t: any) => t.debt));
            const chartH = 120;
            return (
            <div className="relative" style={{ height: chartH + 30 }}>
              <div className="flex items-end gap-[6px] px-1" style={{ height: chartH }}>
                {trajectory.map((t: any) => {
                  const h = (t.debt / maxDebt) * chartH;
                  const utilization = t.debt / (useSession.getState().creditLimit || 120000);
                  const color = utilization >= 0.7 ? '#EA4335' : utilization >= 0.5 ? '#F97316' : utilization >= 0.3 ? '#FBBC04' : '#34A853';
                  const isWarn = modelWarnedMonth != null && t.month === modelWarnedMonth;
                  const isConfirm = spiralConfirmedMonth != null && t.month === spiralConfirmedMonth;
                  return (
                    <div key={t.month} className="flex-1 flex flex-col items-center justify-end relative">
                      {isWarn && (
                        <div className="absolute -top-[18px] left-1/2 -translate-x-1/2 whitespace-nowrap">
                          <div className="bg-risk-moderate text-white text-[7px] font-bold px-1 py-0.5 rounded">Warned</div>
                          <div className="w-0 h-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-risk-moderate mx-auto" />
                        </div>
                      )}
                      {isConfirm && (
                        <div className="absolute -top-[18px] left-1/2 -translate-x-1/2 whitespace-nowrap">
                          <div className="bg-risk-high text-white text-[7px] font-bold px-1 py-0.5 rounded">Spiral</div>
                          <div className="w-0 h-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-risk-high mx-auto" />
                        </div>
                      )}
                      <div className="text-[7px] text-text-secondary font-bold mb-0.5 tabular-nums">{(t.debt/1000).toFixed(0)}k</div>
                      <div className="w-full rounded-t-sm" style={{ height: h, backgroundColor: color }} />
                    </div>
                  );
                })}
              </div>
              <div className="flex gap-[6px] px-1 mt-1">
                {trajectory.map((t: any) => (
                  <div key={t.month} className="flex-1 text-center text-[8px] text-text-tertiary tabular-nums">
                    M{t.month}
                  </div>
                ))}
              </div>
            </div>
            );
          })()}

          {(modelWarnedMonth != null || spiralConfirmedMonth != null) && (
          <div className="flex items-center gap-4 mt-3 pt-2 border-t border-border">
            {modelWarnedMonth != null && (
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 bg-risk-moderate rounded-full" />
              <span className="text-[10px] text-text-secondary">Model Warned (M{modelWarnedMonth})</span>
            </div>
            )}
            {spiralConfirmedMonth != null && (
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 bg-risk-high rounded-full" />
              <span className="text-[10px] text-text-secondary">Spiral Confirmed (M{spiralConfirmedMonth})</span>
            </div>
            )}
          </div>
          )}
        </div>
        )}

        {/* What-If Projection */}
        <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4">
          <p className="text-[14px] font-semibold text-text-primary mb-1">What Happens Next?</p>
          <p className="text-[11px] text-text-tertiary mb-4">Adjust discretionary spending reduction to see projected impact</p>

          {/* Slider */}
          <div className="mb-4">
            <div className="flex justify-between text-[11px] text-text-secondary mb-2">
              <span>Monthly reduction</span>
              <span className="font-bold text-accent">{'₹'}{fmt(whatIfReduction)}/mo {loading.project && '...'}</span>
            </div>
            <input
              type="range"
              min={0}
              max={5000}
              step={250}
              value={whatIfReduction}
              onChange={(e) => handleSliderChange(Number(e.target.value))}
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
              <p className="text-[10px] text-text-tertiary">Projected debt (12mo)</p>
            </div>
            <div className="bg-green-50 rounded-xl p-3 border border-green-200">
              <p className="text-[10px] text-text-secondary mb-1">With Change</p>
              <p className="text-[20px] font-bold text-risk-low tabular-nums">{'₹'}{fmt(Math.round(projectedWithChange))}</p>
              <p className="text-[10px] text-text-tertiary">Projected debt (12mo)</p>
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
