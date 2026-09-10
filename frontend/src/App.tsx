import { useEffect, useState } from 'react';
import { api } from './api/client';
import fixtureC from './fixtures/persona_c.json';

function App() {
  const [health, setHealth] = useState<any>(null);
  const [personas, setPersonas] = useState<any[]>([]);
  const [useFixtures, setUseFixtures] = useState(true);

  useEffect(() => {
    api.health()
      .then((h) => {
        setHealth(h);
        setUseFixtures(false);
        return api.getPersonas();
      })
      .then(setPersonas)
      .catch(() => {
        setUseFixtures(true);
      });
  }, []);

  const riskScore = useFixtures
    ? fixtureC.assessment.risk_score
    : 0;

  const band = useFixtures
    ? fixtureC.assessment.band
    : 'LOW';

  const bandColor: Record<string, string> = {
    LOW: 'text-risk-low',
    MODERATE: 'text-risk-moderate',
    ELEVATED: 'text-risk-elevated',
    HIGH: 'text-risk-high',
  };

  return (
    <div className="min-h-screen bg-base p-6">
      <header className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-text-primary">
          DebtSpiral
        </h1>
        <div className="flex gap-2">
          {['A', 'B', 'C', 'D', 'E'].map((id) => (
            <button
              key={id}
              className={`px-3 py-1 rounded-card text-sm font-medium border ${
                id === 'C'
                  ? 'bg-accent text-white border-accent'
                  : 'bg-card text-text-secondary border-white/[0.06]'
              }`}
            >
              {id}
            </button>
          ))}
        </div>
        <span className="text-xs text-text-tertiary">
          {health ? `API connected · ${health.personas_loaded} personas` : useFixtures ? 'Using fixtures' : 'Connecting...'}
        </span>
      </header>

      <div className="grid grid-cols-3 gap-6">
        {/* LEFT — Gauge */}
        <div className="bg-card rounded-card border border-white/[0.06] p-5 flex flex-col items-center">
          <p className="text-text-secondary text-sm mb-4">Risk Score</p>
          <p className={`text-[44px] font-bold tabular-nums ${bandColor[band]}`}>
            {riskScore}
          </p>
          <p className={`text-sm font-medium ${bandColor[band]}`}>{band}</p>
        </div>

        {/* CENTER — Trajectory placeholder */}
        <div className="bg-card rounded-card border border-white/[0.06] p-5">
          <p className="text-text-secondary text-sm mb-2">Trajectory</p>
          <p className="text-text-tertiary text-xs">Chart renders in Phase 4</p>
        </div>

        {/* RIGHT — SHAP placeholder */}
        <div className="bg-card rounded-card border border-white/[0.06] p-5">
          <p className="text-text-secondary text-sm mb-2">Why Am I At Risk?</p>
          {useFixtures && fixtureC.shap.items.map((item) => (
            <div key={item.feature} className="flex justify-between text-xs py-1">
              <span className="text-text-primary">{item.display_name}</span>
              <span className={item.direction === '+' ? 'text-risk-high' : 'text-risk-low'}>
                {item.direction === '+' ? '+' : '−'}{Math.abs(item.shap).toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <footer className="mt-8 text-center text-xs text-text-tertiary">
        Every feature is a ratio or a trend. No merchant names, no identity, no raw transactions cross the aggregation boundary.
      </footer>
    </div>
  );
}

export default App;
