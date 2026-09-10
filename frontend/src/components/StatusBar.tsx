export default function StatusBar() {
  const time = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
  return (
    <div className="flex items-center justify-between px-8 pt-[14px] pb-1 text-[12px] font-semibold text-text-primary z-40 relative">
      <span>{time}</span>
      <div className="flex items-center gap-1.5 text-text-primary">
        <svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor"><rect x="0" y="6" width="3" height="6" rx="1"/><rect x="4" y="4" width="3" height="8" rx="1"/><rect x="8" y="2" width="3" height="10" rx="1"/><rect x="12" y="0" width="3" height="12" rx="1"/></svg>
        <svg width="20" height="12" viewBox="0 0 20 12" fill="currentColor"><rect x="0" y="1" width="16" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none"/><rect x="17" y="4" width="2" height="4" rx="0.5"/><rect x="2" y="3" width="10" height="6" rx="1"/></svg>
      </div>
    </div>
  );
}
