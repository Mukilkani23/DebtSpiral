import { useSession } from '../store/session';

function fmt(n: number) { return n.toLocaleString('en-IN'); }

export default function PayFailedScreen() {
  const payContact = useSession((s) => s.payContact);
  const payAmount = useSession((s) => s.payAmount);
  const payError = useSession((s) => s.payError);
  const bankBalance = useSession((s) => s.bankBalance);
  const setScreen = useSession((s) => s.setScreen);
  const setPayError = useSession((s) => s.setPayError);

  const available = payError?.available_balance_inr ?? bankBalance;
  const requested = payError?.requested_amount_inr ?? payAmount;
  const shortfall = payError?.shortfall_inr ?? Math.max(requested - available, 0);

  const handleClose = () => {
    setPayError(null);
    setScreen('home');
  };

  return (
    <div className="px-5 pt-[50px] pb-6 flex flex-col items-center bg-white">
      <div className="w-20 h-20 rounded-full flex items-center justify-center mb-4 bg-red-50">
        <span className="text-[36px]">❌</span>
      </div>

      <p className="text-[16px] font-semibold text-risk-high">Payment Failed</p>
      <p className="text-[13px] text-text-secondary mt-1">Insufficient balance</p>

      <p className="text-[32px] font-bold text-text-primary mt-2 tabular-nums">{'₹'}{fmt(requested)}</p>
      <p className="text-[13px] text-text-secondary mt-1">to {payContact?.name || 'recipient'}</p>

      <div className="w-full mt-6 space-y-3">
        <div className="bg-red-50 rounded-xl border border-red-200 p-4 space-y-2">
          <div className="flex justify-between text-[12px]">
            <span className="text-text-secondary">Available balance</span>
            <span className="text-text-primary font-semibold">{'₹'}{fmt(available)}</span>
          </div>
          <div className="flex justify-between text-[12px]">
            <span className="text-text-secondary">Attempted</span>
            <span className="text-text-primary font-semibold">{'₹'}{fmt(requested)}</span>
          </div>
          <div className="border-t border-red-200 my-1" />
          <div className="flex justify-between text-[12px]">
            <span className="text-risk-high font-semibold">Shortfall</span>
            <span className="text-risk-high font-bold">{'₹'}{fmt(shortfall)}</span>
          </div>
        </div>

        <p className="text-[12px] text-text-secondary text-center px-2">
          Your payment was not completed. No amount was deducted from your account.
        </p>
      </div>

      <div className="w-full mt-6">
        <button onClick={handleClose}
          className="w-full bg-accent py-3 rounded-full text-white font-bold text-[13px]">
          Close
        </button>
      </div>

      <p className="text-[9px] text-text-tertiary mt-4">Simulated payment · No real bank debit occurred</p>
    </div>
  );
}
