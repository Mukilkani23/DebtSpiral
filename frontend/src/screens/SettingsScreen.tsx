import { useEffect, useState } from 'react';
import { useSession } from '../store/session';
import { api } from '../api/client';

interface PersonaInfo {
  id: string;
  label: string;
  desc: string;
  risk: string;
  isLive: boolean;
}

const FALLBACK_PERSONAS: PersonaInfo[] = [
  { id: 'A', label: 'Steady Eddie', desc: 'Healthy, stable finances', risk: 'LOW', isLive: false },
  { id: 'B', label: 'High Roller', desc: 'High income, poor discipline', risk: 'HIGH', isLive: false },
  { id: 'C', label: 'Rising Pressure', desc: '₹50K/mo, deteriorating trajectory', risk: 'HIGH', isLive: true },
  { id: 'D', label: 'Variable Income', desc: 'Gig worker, inconsistent cash flow', risk: 'MODERATE', isLive: false },
  { id: 'E', label: 'Recovering', desc: 'High debt but improving trajectory', risk: 'LOW', isLive: false },
];

function bandFromScore(s: number) {
  if (s >= 70) return 'HIGH';
  if (s >= 50) return 'ELEVATED';
  if (s >= 30) return 'MODERATE';
  return 'LOW';
}

export default function SettingsScreen() {
  const personaId = useSession((s) => s.personaId);
  const setPersonaId = useSession((s) => s.setPersonaId);
  const setScreen = useSession((s) => s.setScreen);
  const resetDemo = useSession((s) => s.resetDemo);
  const loadFromApi = useSession((s) => s.loadFromApi);
  const setBankBalance = useSession((s) => s.setBankBalance);
  const apiConnected = useSession((s) => s.apiConnected);
  const [personas, setPersonas] = useState<PersonaInfo[]>(FALLBACK_PERSONAS);

  useEffect(() => {
    if (!apiConnected) return;
    api.getPersonas().then((list: any[]) => {
      setPersonas(list.map((p) => ({
        id: p.persona_id,
        label: p.label,
        desc: p.narrative,
        risk: bandFromScore(p.current_risk_score),
        isLive: p.is_live,
      })));
    }).catch(() => {});
  }, [apiConnected]);

  const handleReset = async () => {
    resetDemo();
    if (apiConnected) {
      try {
        await api.reset();
        const [detail, account] = await Promise.all([
          api.getPersona(personaId),
          api.getAccount(personaId),
        ]);
        loadFromApi(detail, null);
        setBankBalance(account.balance_inr);
      } catch {}
    }
  };

  return (
    <div className="px-5 pt-[50px] pb-6 bg-white">
      <h1 className="text-[20px] font-bold text-text-primary mb-5">You</h1>

      <div className="bg-white rounded-xl shadow-gpay border border-border p-4 mb-4 flex items-center gap-3">
        <div className="w-12 h-12 bg-accent-light rounded-full flex items-center justify-center text-accent font-bold text-[18px]">M</div>
        <div>
          <p className="text-[14px] font-semibold text-text-primary">Mukil</p>
          <p className="text-[11px] text-text-secondary">Demo Account · Persona {personaId}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-gpay border border-border divide-y divide-border mb-6">
        {[
          { label: 'Expense Tiers', icon: '📊', action: () => setScreen('tiers') },
          { label: 'DebtSpiral Intelligence', icon: '🔮', action: () => setScreen('debtspiral') },
          { label: 'Transaction History', icon: '📋', action: () => setScreen('activity') },
        ].map((item) => (
          <button key={item.label} onClick={item.action}
            className="w-full flex items-center gap-3 py-3.5 px-4 hover:bg-gpay-surface transition-colors">
            <span className="text-[18px]">{item.icon}</span>
            <span className="text-[13px] text-text-primary flex-1 text-left">{item.label}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9AA0A6" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        ))}
      </div>

      <div className="mb-6">
        <p className="text-[11px] text-text-secondary uppercase tracking-wider mb-2">Switch Persona</p>
        <div className="space-y-1.5">
          {personas.map((p) => (
            <button key={p.id} onClick={() => setPersonaId(p.id)}
              className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-colors ${
                p.id === personaId ? 'bg-accent-light border-accent' : 'bg-white border-border shadow-gpay'
              }`}>
              <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-[13px] ${
                p.id === personaId ? 'bg-accent text-white' : 'bg-gpay-surface text-text-secondary'
              }`}>{p.id}</div>
              <div className="flex-1 text-left">
                <p className="text-[12px] font-medium text-text-primary">{p.label}</p>
                <p className="text-[10px] text-text-secondary truncate max-w-[200px]">{p.desc}</p>
              </div>
              {p.isLive && <span className="text-[9px] bg-accent-light text-accent px-2 py-0.5 rounded-md font-bold">LIVE</span>}
            </button>
          ))}
        </div>
      </div>

      <button onClick={handleReset}
        className="w-full bg-red-50 border border-red-200 py-3 rounded-xl text-risk-high font-semibold text-[13px]">
        Reset Demo Data
      </button>

      <div className="mt-4 text-center">
        <p className="text-[10px] text-text-secondary">API: {apiConnected ? '🟢 Connected' : '🔴 Offline (using fixtures)'}</p>
        <p className="text-[9px] text-text-tertiary mt-1">DebtSpiral v4 · Hackathon Prototype</p>
      </div>
    </div>
  );
}
