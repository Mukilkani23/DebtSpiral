import { useEffect } from 'react';
import { useSession } from './store/session';
import { api } from './api/client';
import HomeScreen from './screens/HomeScreen';
import ActivityScreen from './screens/ActivityScreen';
import DebtSpiralScreen from './screens/DebtSpiralScreen';
import SettingsScreen from './screens/SettingsScreen';
import TiersScreen from './screens/TiersScreen';
import TierManageScreen from './screens/TierManageScreen';
import PayScreen from './screens/PayScreen';
import PayConfirmScreen from './screens/PayConfirmScreen';
import PaySuccessScreen from './screens/PaySuccessScreen';
import PayFailedScreen from './screens/PayFailedScreen';
import ExpenseEditScreen from './screens/ExpenseEditScreen';
import BottomNav from './components/BottomNav';
import StatusBar from './components/StatusBar';
import NudgeBanner from './components/NudgeBanner';

async function loadPersona(id: string, loadFromApi: (detail: any, score: any) => void) {
  try {
    const detail = await api.getPersona(id);
    loadFromApi(detail, null);
  } catch {}
}

export async function loadAccount(id: string, setBankBalance: (b: number) => void) {
  try {
    const account = await api.getAccount(id);
    setBankBalance(account.balance_inr);
  } catch { /* server is authoritative — leave balance as-is if unreachable */ }
}

function PhoneContent() {
  const screen = useSession((s) => s.screen);
  switch (screen) {
    case 'home': return <HomeScreen />;
    case 'activity': return <ActivityScreen />;
    case 'debtspiral': return <DebtSpiralScreen />;
    case 'settings': return <SettingsScreen />;
    case 'tiers': return <TiersScreen />;
    case 'tier-manage': return <TierManageScreen />;
    case 'pay': case 'contact-pay': return <PayScreen />;
    case 'pay-confirm': return <PayConfirmScreen />;
    case 'pay-success': return <PaySuccessScreen />;
    case 'pay-failed': return <PayFailedScreen />;
    case 'expense-edit': return <ExpenseEditScreen />;
    default: return <HomeScreen />;
  }
}

const NAV_SCREENS = new Set(['home', 'activity', 'debtspiral', 'settings']);

function App() {
  const screen = useSession((s) => s.screen);
  const setApiConnected = useSession((s) => s.setApiConnected);
  const nudgeVisible = useSession((s) => s.nudgeVisible);

  const personaId = useSession((s) => s.personaId);
  const loadFromApi = useSession((s) => s.loadFromApi);
  const setBankBalance = useSession((s) => s.setBankBalance);

  useEffect(() => {
    api.health()
      .then(() => {
        setApiConnected(true);
        return Promise.all([
          loadPersona(personaId, loadFromApi),
          loadAccount(personaId, setBankBalance),
        ]);
      })
      .catch(() => setApiConnected(false));
  }, []);

  useEffect(() => {
    const { apiConnected } = useSession.getState();
    if (apiConnected) {
      loadPersona(personaId, loadFromApi);
      loadAccount(personaId, setBankBalance);
    }
  }, [personaId]);

  return (
    <div className="min-h-screen bg-[#E8EAED] flex items-center justify-center p-4">
      <div className="relative w-[390px] h-[844px] bg-white rounded-[44px] border-[3px] border-[#D2D5DA] shadow-gpay-lg overflow-hidden flex flex-col">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[126px] h-[34px] bg-black rounded-b-[18px] z-50" />
        <StatusBar />
        <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-hide relative bg-white">
          <PhoneContent />
        </div>
        {nudgeVisible && <NudgeBanner />}
        {NAV_SCREENS.has(screen) && <BottomNav />}
        <div className="flex justify-center pb-2 pt-1 bg-white">
          <div className="w-[134px] h-[5px] bg-black/10 rounded-full" />
        </div>
      </div>
    </div>
  );
}

export default App;
