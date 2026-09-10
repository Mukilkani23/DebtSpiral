import { create } from 'zustand';

// ── Tier types ──
export type TierLevel = 1 | 2 | 3;

export interface ExpenseCategory {
  id: string;
  name: string;
  tier: TierLevel;
  monthlyBudget: number;
  currentSpend: number;
  recurring: boolean;
  priority: 'critical' | 'high' | 'medium' | 'low';
  icon: string;
}

export interface Transaction {
  id: string;
  label: string;
  amount: number;
  category: string;
  tier: TierLevel;
  timestamp: number;
  flagged: boolean;
  riskBefore?: number;
  riskAfter?: number;
}

export interface Contact {
  id: string;
  name: string;
  avatar: string;
  defaultCategory: string;
  defaultTier: TierLevel;
}

export type Screen =
  | 'home'
  | 'activity'
  | 'debtspiral'
  | 'settings'
  | 'tiers'
  | 'tier-manage'
  | 'pay'
  | 'pay-confirm'
  | 'pay-success'
  | 'contact-pay'
  | 'persona-switch'
  | 'expense-edit';

export type PayButtonState = 'safe' | 'warning' | 'flagged';

interface SessionState {
  // Navigation
  screen: Screen;
  setScreen: (s: Screen) => void;
  prevScreen: Screen;

  // Persona
  personaId: string;
  personaLabel: string;
  setPersonaId: (id: string) => void;

  // Financial state
  monthlyIncome: number;
  bankBalance: number;
  creditLimit: number;

  // Risk
  riskScore: number;
  riskBand: string;
  spiralDetected: boolean;
  modelWarnedMonth: number | null;
  spiralConfirmedMonth: number | null;
  leadTimeMonths: number | null;

  // SHAP
  shap: { base_value: number; items: any[] } | null;

  // Reason codes (transaction-level)
  reasonCodes: any[];
  nudge: any | null;
  nudgeVisible: boolean;
  setNudgeVisible: (v: boolean) => void;

  // Expense tiers
  expenses: ExpenseCategory[];
  setExpenses: (e: ExpenseCategory[]) => void;
  updateExpense: (id: string, updates: Partial<ExpenseCategory>) => void;

  // Transactions
  transactions: Transaction[];
  addTransaction: (t: Transaction) => void;

  // Payment flow
  payContact: Contact | null;
  payAmount: number;
  payCategory: string;
  payTier: TierLevel;
  payButtonState: PayButtonState;
  payResult: any | null;
  setPayContact: (c: Contact | null) => void;
  setPayAmount: (a: number) => void;
  setPayCategory: (c: string) => void;
  setPayTier: (t: TierLevel) => void;
  setPayButtonState: (s: PayButtonState) => void;
  setPayResult: (r: any) => void;

  // Projection
  projection: any | null;
  setProjection: (p: any) => void;
  whatIfReduction: number;
  setWhatIfReduction: (v: number) => void;

  // Loading
  loading: { score: boolean; project: boolean; txn: boolean };
  setLoading: (key: 'score' | 'project' | 'txn', val: boolean) => void;
  error: string | null;
  setError: (e: string | null) => void;

  // API status
  apiConnected: boolean;
  setApiConnected: (v: boolean) => void;

  // Edit target
  editExpenseId: string | null;
  setEditExpenseId: (id: string | null) => void;

  // Tier manage filter
  tierManageFilter: TierLevel;
  setTierManageFilter: (t: TierLevel) => void;

  // Actions
  updateRisk: (score: number, band: string, codes: any[], nudge: any) => void;
  resetDemo: () => void;

  // Contacts
  contacts: Contact[];
}

const DEFAULT_EXPENSES: ExpenseCategory[] = [
  { id: 'medical', name: 'Medical', tier: 1, monthlyBudget: 3000, currentSpend: 0, recurring: true, priority: 'critical', icon: '🏥' },
  { id: 'wifi', name: 'Wi-Fi', tier: 1, monthlyBudget: 1000, currentSpend: 1000, recurring: true, priority: 'critical', icon: '📶' },
  { id: 'recharge', name: 'Recharge', tier: 1, monthlyBudget: 350, currentSpend: 350, recurring: true, priority: 'critical', icon: '📱' },
  { id: 'insurance', name: 'Insurance', tier: 1, monthlyBudget: 0, currentSpend: 0, recurring: true, priority: 'critical', icon: '🛡️' },
  { id: 'petrol', name: 'Petrol', tier: 2, monthlyBudget: 2000, currentSpend: 1650, recurring: true, priority: 'high', icon: '⛽' },
  { id: 'groceries', name: 'Groceries', tier: 2, monthlyBudget: 5000, currentSpend: 3200, recurring: true, priority: 'high', icon: '🛒' },
  { id: 'family', name: 'Family', tier: 2, monthlyBudget: 4000, currentSpend: 2600, recurring: false, priority: 'medium', icon: '👨‍👩‍👧' },
  { id: 'chatgpt', name: 'ChatGPT', tier: 3, monthlyBudget: 2000, currentSpend: 2000, recurring: true, priority: 'low', icon: '🤖' },
  { id: 'friends', name: 'Friends', tier: 3, monthlyBudget: 1500, currentSpend: 1450, recurring: false, priority: 'low', icon: '🍻' },
  { id: 'entertainment', name: 'Entertainment', tier: 3, monthlyBudget: 1500, currentSpend: 1350, recurring: false, priority: 'low', icon: '🎮' },
  { id: 'food_delivery', name: 'Food Delivery', tier: 3, monthlyBudget: 1500, currentSpend: 1350, recurring: false, priority: 'low', icon: '🍕' },
];

const DEFAULT_CONTACTS: Contact[] = [
  { id: 'anand', name: 'Anand', avatar: 'A', defaultCategory: 'friends', defaultTier: 3 },
  { id: 'sathya', name: 'Sathya', avatar: 'S', defaultCategory: 'friends', defaultTier: 3 },
  { id: 'family_m', name: 'Mom', avatar: 'M', defaultCategory: 'family', defaultTier: 2 },
  { id: 'swiggy', name: 'Swiggy', avatar: '🍕', defaultCategory: 'food_delivery', defaultTier: 3 },
  { id: 'zomato', name: 'Zomato', avatar: '🍔', defaultCategory: 'food_delivery', defaultTier: 3 },
  { id: 'flipkart', name: 'Flipkart', avatar: 'F', defaultCategory: 'shopping', defaultTier: 3 },
  { id: 'petrol_bunk', name: 'Petrol Bunk', avatar: '⛽', defaultCategory: 'petrol', defaultTier: 2 },
  { id: 'apollo', name: 'Apollo Pharmacy', avatar: '💊', defaultCategory: 'medical', defaultTier: 1 },
];

const INITIAL_RISK = 87;

export const useSession = create<SessionState>((set, get) => ({
  screen: 'home',
  prevScreen: 'home',
  setScreen: (screen) => set((s) => ({ screen, prevScreen: s.screen })),

  personaId: 'C',
  personaLabel: 'Rising Pressure',
  setPersonaId: (id) => {
    const labels: Record<string, string> = {
      A: 'Steady Eddie',
      B: 'High Roller',
      C: 'Rising Pressure',
      D: 'Variable Income',
      E: 'Recovering',
    };
    set({
      personaId: id,
      personaLabel: labels[id] || id,
      reasonCodes: [],
      nudge: null,
      nudgeVisible: false,
    });
  },

  monthlyIncome: 50000,
  bankBalance: 50000,
  creditLimit: 120000,

  riskScore: INITIAL_RISK,
  riskBand: 'HIGH',
  spiralDetected: true,
  modelWarnedMonth: 5,
  spiralConfirmedMonth: 8,
  leadTimeMonths: 3.0,

  shap: {
    base_value: 0.25,
    items: [
      { feature: 'utilization_trend', display_name: 'Credit utilization climbing', value: 0.062, shap: 0.14, direction: '+' },
      { feature: 'min_payment_ratio_trend', display_name: 'Repayment discipline eroding', value: -0.031, shap: 0.11, direction: '+' },
      { feature: 'dti_trend', display_name: 'Debt-to-income growing', value: 0.045, shap: 0.09, direction: '+' },
      { feature: 'stc_frequency', display_name: 'Short-term borrowing increasing', value: 0.5, shap: 0.07, direction: '+' },
      { feature: 'recovery_slope', display_name: 'Recovery capacity shrinking', value: -0.02, shap: 0.06, direction: '+' },
      { feature: 'absolute_debt_inr', display_name: 'Outstanding debt level', value: 82000, shap: 0.01, direction: '+' },
    ],
  },

  reasonCodes: [],
  nudge: null,
  nudgeVisible: false,
  setNudgeVisible: (v) => set({ nudgeVisible: v }),

  expenses: [...DEFAULT_EXPENSES],
  setExpenses: (expenses) => set({ expenses }),
  updateExpense: (id, updates) =>
    set((s) => ({
      expenses: s.expenses.map((e) => (e.id === id ? { ...e, ...updates } : e)),
    })),

  transactions: [
    { id: 't1', label: 'Mobile Recharge', amount: 350, category: 'recharge', tier: 1, timestamp: Date.now() - 86400000 * 2, flagged: false },
    { id: 't2', label: 'Petrol', amount: 500, category: 'petrol', tier: 2, timestamp: Date.now() - 86400000, flagged: false },
  ],
  addTransaction: (t) =>
    set((s) => ({
      transactions: [t, ...s.transactions],
      bankBalance: s.bankBalance - t.amount,
      expenses: s.expenses.map((e) =>
        e.id === t.category || e.name.toLowerCase() === t.category.toLowerCase()
          ? { ...e, currentSpend: e.currentSpend + t.amount }
          : e
      ),
    })),

  payContact: null,
  payAmount: 0,
  payCategory: '',
  payTier: 3,
  payButtonState: 'safe',
  payResult: null,
  setPayContact: (c) => set({ payContact: c }),
  setPayAmount: (a) => set({ payAmount: a }),
  setPayCategory: (c) => set({ payCategory: c }),
  setPayTier: (t) => set({ payTier: t }),
  setPayButtonState: (s) => set({ payButtonState: s }),
  setPayResult: (r) => set({ payResult: r }),

  projection: null,
  setProjection: (p) => set({ projection: p }),
  whatIfReduction: 0,
  setWhatIfReduction: (v) => set({ whatIfReduction: v }),

  loading: { score: false, project: false, txn: false },
  setLoading: (key, val) => set((s) => ({ loading: { ...s.loading, [key]: val } })),
  error: null,
  setError: (error) => set({ error }),

  apiConnected: false,
  setApiConnected: (v) => set({ apiConnected: v }),

  editExpenseId: null,
  setEditExpenseId: (id) => set({ editExpenseId: id }),

  tierManageFilter: 1,
  setTierManageFilter: (t) => set({ tierManageFilter: t }),

  updateRisk: (score, band, codes, nudge) =>
    set({
      riskScore: score,
      riskBand: band,
      reasonCodes: codes,
      nudge,
      nudgeVisible: !!nudge,
    }),

  resetDemo: () =>
    set({
      riskScore: INITIAL_RISK,
      riskBand: 'HIGH',
      reasonCodes: [],
      nudge: null,
      nudgeVisible: false,
      transactions: [
        { id: 't1', label: 'Mobile Recharge', amount: 350, category: 'recharge', tier: 1, timestamp: Date.now() - 86400000 * 2, flagged: false },
        { id: 't2', label: 'Petrol', amount: 500, category: 'petrol', tier: 2, timestamp: Date.now() - 86400000, flagged: false },
      ],
      expenses: [...DEFAULT_EXPENSES],
      bankBalance: 50000,
      payResult: null,
      payButtonState: 'safe',
    }),

  contacts: DEFAULT_CONTACTS,
}));

// Derived selectors
export const useTierTotals = () =>
  useSession((s) => {
    const t1 = s.expenses.filter((e) => e.tier === 1).reduce((sum, e) => sum + e.monthlyBudget, 0);
    const t2 = s.expenses.filter((e) => e.tier === 2).reduce((sum, e) => sum + e.monthlyBudget, 0);
    const t3 = s.expenses.filter((e) => e.tier === 3).reduce((sum, e) => sum + e.monthlyBudget, 0);
    const t1Spent = s.expenses.filter((e) => e.tier === 1).reduce((sum, e) => sum + e.currentSpend, 0);
    const t2Spent = s.expenses.filter((e) => e.tier === 2).reduce((sum, e) => sum + e.currentSpend, 0);
    const t3Spent = s.expenses.filter((e) => e.tier === 3).reduce((sum, e) => sum + e.currentSpend, 0);
    const totalPlanned = t1 + t2 + t3;
    const available = s.monthlyIncome - t1;
    return { t1, t2, t3, t1Spent, t2Spent, t3Spent, totalPlanned, available };
  });
