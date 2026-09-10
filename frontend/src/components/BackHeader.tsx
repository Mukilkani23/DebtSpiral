import { useSession, type Screen } from '../store/session';

export default function BackHeader({ title, to }: { title: string; to?: Screen }) {
  const setScreen = useSession((s) => s.setScreen);
  const prevScreen = useSession((s) => s.prevScreen);

  return (
    <div className="flex items-center gap-3 px-4 pt-[50px] pb-3 bg-white">
      <button
        onClick={() => setScreen(to || prevScreen || 'home')}
        className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gpay-surface text-text-primary"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
      <h1 className="text-[17px] font-semibold text-text-primary">{title}</h1>
    </div>
  );
}
