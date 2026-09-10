import { useSession } from '../store/session';

export default function NudgeBanner() {
  const setNudgeVisible = useSession((s) => s.setNudgeVisible);
  const nudge = useSession((s) => s.nudge);
  const setScreen = useSession((s) => s.setScreen);

  return (
    <div className="absolute bottom-[120px] left-3 right-3 bg-white border border-border rounded-2xl p-4 shadow-gpay-lg z-50 animate-slide-up">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-[#25D366] rounded-full flex items-center justify-center text-white text-lg flex-shrink-0">
          W
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[13px] font-semibold text-[#25D366]">DebtSpiral Alert</span>
            <span className="text-[10px] text-text-tertiary">now</span>
          </div>
          <p className="text-[12px] text-text-primary leading-relaxed">
            {nudge?.message || 'Your recent transaction exceeded your Tier 3 budget. Consider reducing discretionary spending.'}
          </p>
          <button
            onClick={() => { setNudgeVisible(false); setScreen('debtspiral'); }}
            className="mt-2 text-[11px] font-semibold text-accent"
          >
            VIEW DETAILS
          </button>
        </div>
        <button onClick={() => setNudgeVisible(false)} className="text-text-tertiary text-lg leading-none">&times;</button>
      </div>
    </div>
  );
}
