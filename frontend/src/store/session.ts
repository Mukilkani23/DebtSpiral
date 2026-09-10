import { create } from 'zustand';

interface SessionState {
  personaId: string;
  persona: any | null;
  assessment: any | null;
  shap: any | null;
  reasonCodes: any[];
  nudge: any | null;
  projection: any | null;
  loading: { score: boolean; project: boolean; txn: boolean };
  error: string | null;
  setPersonaId: (id: string) => void;
  setPersona: (p: any) => void;
  setAssessment: (a: any) => void;
  setShap: (s: any) => void;
  setReasonCodes: (r: any[]) => void;
  setNudge: (n: any) => void;
  setProjection: (p: any) => void;
  setLoading: (key: 'score' | 'project' | 'txn', val: boolean) => void;
  setError: (e: string | null) => void;
}

export const useSession = create<SessionState>((set) => ({
  personaId: 'C',
  persona: null,
  assessment: null,
  shap: null,
  reasonCodes: [],
  nudge: null,
  projection: null,
  loading: { score: false, project: false, txn: false },
  error: null,
  setPersonaId: (id) => set({ personaId: id, reasonCodes: [], nudge: null }),
  setPersona: (persona) => set({ persona }),
  setAssessment: (assessment) => set({ assessment }),
  setShap: (shap) => set({ shap }),
  setReasonCodes: (reasonCodes) => set({ reasonCodes }),
  setNudge: (nudge) => set({ nudge }),
  setProjection: (projection) => set({ projection }),
  setLoading: (key, val) =>
    set((s) => ({ loading: { ...s.loading, [key]: val } })),
  setError: (error) => set({ error }),
}));
