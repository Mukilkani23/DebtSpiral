import { useSession, type Screen } from '../store/session';

const tabs: { id: Screen; label: string; iconPath: string }[] = [
  { id: 'home', label: 'Home', iconPath: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4' },
  { id: 'activity', label: 'Money', iconPath: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1' },
  { id: 'settings', label: 'You', iconPath: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
];

export default function BottomNav() {
  const screen = useSession((s) => s.screen);
  const setScreen = useSession((s) => s.setScreen);

  return (
    <nav className="flex items-center justify-around bg-white border-t border-border px-2 py-1.5">
      {tabs.map((tab) => {
        const active = screen === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setScreen(tab.id)}
            className="flex flex-col items-center gap-0.5 px-5 py-1.5 rounded-full transition-colors"
          >
            <div className={`p-1 rounded-full ${active ? 'bg-accent-light' : ''}`}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className={active ? 'text-accent' : 'text-text-secondary'}
                stroke="currentColor">
                <path d={tab.iconPath} />
              </svg>
            </div>
            <span className={`text-[11px] font-medium ${active ? 'text-accent' : 'text-text-secondary'}`}>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
