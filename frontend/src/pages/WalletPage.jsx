import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth, API } from "../App";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { toast } from "sonner";
import axios from "axios";
import { 
  Zap, Wallet, ArrowLeft, CreditCard, Banknote, ArrowDownLeft, ArrowUpRight,
  CheckCircle2, XCircle, Clock, Loader2, ChevronRight, Gift
} from "lucide-react";

const WalletPage = () => {
  const { user, token, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [depositAmount, setDepositAmount] = useState("");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [payidAccount, setPayidAccount] = useState("");
  const [processing, setProcessing] = useState(false);
  const [checkingPayment, setCheckingPayment] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successAmount, setSuccessAmount] = useState(0);

  // Deposit packages
  const packages = [
    { id: "small", amount: 10, bonus: 0, color: "from-gray-600 to-gray-500" },
    { id: "medium", amount: 25, bonus: 5, color: "from-blue-600 to-blue-500" },
    { id: "large", amount: 50, bonus: 15, color: "from-purple-600 to-purple-500" },
    { id: "xl", amount: 100, bonus: 30, color: "from-yellow-600 to-orange-500", popular: true },
    { id: "xxl", amount: 250, bonus: 100, color: "from-pink-600 to-rose-500" },
  ];

  useEffect(() => {
    fetchTransactions();
    
    // Check for Stripe redirect
    const sessionId = searchParams.get("session_id");
    const cancelled = searchParams.get("cancelled");
    
    if (sessionId) {
      checkStripePayment(sessionId);
    } else if (cancelled) {
      toast.error("Payment was cancelled");
      navigate("/wallet", { replace: true });
    }
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/wallet/transactions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTransactions(response.data);
    } catch (error) {
      console.error("Failed to fetch transactions:", error);
    } finally {
      setLoading(false);
    }
  };

  const checkStripePayment = async (sessionId) => {
    setCheckingPayment(true);
    let attempts = 0;
    const maxAttempts = 5;
    
    const poll = async () => {
      try {
        const response = await axios.get(`${API}/wallet/deposit/stripe/status/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.payment_status === "paid") {
          await refreshUser();
          fetchTransactions();
          setSuccessAmount(response.data.amount);
          setShowSuccessModal(true);
          setCheckingPayment(false);
          navigate("/wallet", { replace: true });
          return;
        }
        
        attempts++;
        if (attempts < maxAttempts && response.data.status !== "expired") {
          setTimeout(poll, 2000);
        } else {
          setCheckingPayment(false);
          if (response.data.status === "expired") {
            toast.error("Payment session expired");
          } else {
            toast.info("Payment is still processing. Check back shortly.");
          }
          navigate("/wallet", { replace: true });
        }
      } catch (error) {
        setCheckingPayment(false);
        toast.error("Failed to verify payment");
        navigate("/wallet", { replace: true });
      }
    };
    
    poll();
  };

  const handlePayIDDeposit = async () => {
    const amount = parseFloat(depositAmount);
    if (!amount || amount <= 0) {
      toast.error("Enter a valid amount");
      return;
    }
    if (amount > 10000) {
      toast.error("Maximum deposit is $10,000");
      return;
    }

    setProcessing(true);
    try {
      const response = await axios.post(`${API}/wallet/deposit/payid`, 
        { amount, method: "payid_demo" },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      toast.success(response.data.message);
      await refreshUser();
      fetchTransactions();
      setDepositAmount("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Deposit failed");
    } finally {
      setProcessing(false);
    }
  };

  const handleStripeDeposit = async (packageId) => {
    setProcessing(true);
    try {
      const response = await axios.post(`${API}/wallet/deposit/stripe/checkout`,
        { 
          package_id: packageId,
          origin_url: window.location.origin
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create checkout");
      setProcessing(false);
    }
  };

  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    if (!amount || amount < 10) {
      toast.error("Minimum withdrawal is $10");
      return;
    }
    if (amount > (user?.balance || 0)) {
      toast.error("Insufficient balance");
      return;
    }
    if (!payidAccount.trim()) {
      toast.error("Enter your PayID account");
      return;
    }

    setProcessing(true);
    try {
      const response = await axios.post(`${API}/wallet/withdraw/payid`,
        { amount, payid_account: payidAccount },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      toast.success(response.data.message);
      await refreshUser();
      fetchTransactions();
      setWithdrawAmount("");
      setPayidAccount("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Withdrawal failed");
    } finally {
      setProcessing(false);
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case "deposit": return <ArrowDownLeft className="w-4 h-4 text-green-400" />;
      case "withdraw": return <ArrowUpRight className="w-4 h-4 text-red-400" />;
      case "win": return <CheckCircle2 className="w-4 h-4 text-yellow-400" />;
      case "bet": return <Wallet className="w-4 h-4 text-purple-400" />;
      case "bonus": return <Gift className="w-4 h-4 text-cyan-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  if (checkingPayment) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-purple-500 mx-auto mb-4" />
          <h2 className="font-heading text-xl text-white mb-2">Processing Payment</h2>
          <p className="text-gray-400">Please wait while we verify your payment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <nav className="sticky top-0 z-50 glass-heavy border-b border-white/10">
        <div className="max-w-4xl mx-auto flex items-center justify-between px-4 py-3">
          <Button 
            variant="ghost" 
            onClick={() => navigate("/lobby")}
            className="text-gray-400 hover:text-white"
            data-testid="back-to-lobby"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
          <Link to="/lobby" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading text-lg font-bold gradient-text">Wallet</span>
          </Link>
          <div className="w-20" />
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Balance Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-heavy rounded-2xl p-6 mb-8 neon-border text-center"
        >
          <p className="text-gray-400 text-sm mb-2">Available Balance</p>
          <h2 className="font-heading text-4xl sm:text-5xl font-black text-white mb-1">
            <span className="font-mono">${user?.balance?.toFixed(2) || '0.00'}</span>
          </h2>
          <p className="text-gray-500 text-xs">AUD</p>
        </motion.div>

        {/* Deposit/Withdraw Tabs */}
        <Tabs defaultValue="deposit" className="mb-8">
          <TabsList className="w-full bg-zinc-900/50 rounded-full p-1 mb-6">
            <TabsTrigger 
              value="deposit" 
              className="flex-1 rounded-full data-[state=active]:bg-gradient-to-r data-[state=active]:from-green-600 data-[state=active]:to-emerald-600"
              data-testid="deposit-tab"
            >
              <ArrowDownLeft className="w-4 h-4 mr-2" />
              Deposit
            </TabsTrigger>
            <TabsTrigger 
              value="withdraw" 
              className="flex-1 rounded-full data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-600 data-[state=active]:to-orange-600"
              data-testid="withdraw-tab"
            >
              <ArrowUpRight className="w-4 h-4 mr-2" />
              Withdraw
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deposit" className="space-y-6">
            {/* Stripe Packages */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <CreditCard className="w-5 h-5 text-[#635BFF]" />
                <h3 className="font-heading font-bold text-white">Card Payment (Stripe)</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {packages.map((pkg) => (
                  <button
                    key={pkg.id}
                    onClick={() => handleStripeDeposit(pkg.id)}
                    disabled={processing}
                    className={`relative rounded-xl p-4 bg-gradient-to-br ${pkg.color} hover:scale-105 transition-transform disabled:opacity-50`}
                    data-testid={`stripe-package-${pkg.id}`}
                  >
                    {pkg.popular && (
                      <span className="absolute -top-2 -right-2 px-2 py-0.5 bg-yellow-400 text-black text-xs font-bold rounded-full">
                        BEST
                      </span>
                    )}
                    <p className="font-heading text-2xl font-bold text-white">${pkg.amount}</p>
                    {pkg.bonus > 0 && (
                      <p className="text-xs text-white/80">+${pkg.bonus} bonus</p>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* PayID Demo */}
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Banknote className="w-5 h-5 text-white" />
                <h3 className="font-heading font-bold text-white">PayID (Demo)</h3>
                <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full">Instant</span>
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <Input
                    type="number"
                    placeholder="Enter amount"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    className="bg-zinc-900/80 border-white/10 h-12 rounded-lg"
                    data-testid="payid-deposit-amount"
                  />
                </div>
                <Button
                  onClick={handlePayIDDeposit}
                  disabled={processing}
                  className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-lg px-6"
                  data-testid="payid-deposit-btn"
                >
                  {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Deposit"}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">Demo mode: Instant credit to your account</p>
            </div>
          </TabsContent>

          <TabsContent value="withdraw" className="space-y-6">
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Banknote className="w-5 h-5 text-white" />
                <h3 className="font-heading font-bold text-white">Withdraw to PayID</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <Label className="text-gray-400 text-sm">Amount</Label>
                  <Input
                    type="number"
                    placeholder="Enter amount (min $10)"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    className="bg-zinc-900/80 border-white/10 h-12 rounded-lg mt-1"
                    data-testid="withdraw-amount"
                  />
                </div>
                <div>
                  <Label className="text-gray-400 text-sm">PayID Account</Label>
                  <Input
                    type="text"
                    placeholder="email@example.com or phone number"
                    value={payidAccount}
                    onChange={(e) => setPayidAccount(e.target.value)}
                    className="bg-zinc-900/80 border-white/10 h-12 rounded-lg mt-1"
                    data-testid="payid-account"
                  />
                </div>
                <Button
                  onClick={handleWithdraw}
                  disabled={processing}
                  className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 rounded-lg h-12"
                  data-testid="withdraw-btn"
                >
                  {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Withdraw"}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">Demo mode: Funds are instantly deducted</p>
            </div>
          </TabsContent>
        </Tabs>

        {/* Transaction History */}
        <div className="glass rounded-xl p-5">
          <h3 className="font-heading font-bold text-white mb-4">Transaction History</h3>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          ) : transactions.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No transactions yet</p>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {transactions.map((tx) => (
                <div 
                  key={tx.id} 
                  className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-900/80 transition-colors"
                  data-testid={`transaction-${tx.id}`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                      {getTransactionIcon(tx.type)}
                    </div>
                    <div>
                      <p className="text-white font-medium capitalize">{tx.type}</p>
                      <p className="text-xs text-gray-500">
                        {tx.method} • {new Date(tx.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <p className={`font-mono font-bold ${
                    tx.type === 'deposit' || tx.type === 'win' || tx.type === 'bonus' 
                      ? 'text-green-400' 
                      : 'text-red-400'
                  }`}>
                    {tx.type === 'deposit' || tx.type === 'win' || tx.type === 'bonus' ? '+' : '-'}
                    ${tx.amount.toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Success Modal */}
      <Dialog open={showSuccessModal} onOpenChange={setShowSuccessModal}>
        <DialogContent className="bg-zinc-900 border-white/10 text-center">
          <DialogHeader>
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8 text-green-400" />
            </div>
            <DialogTitle className="font-heading text-2xl text-white">Payment Successful!</DialogTitle>
            <DialogDescription className="text-gray-400">
              ${successAmount.toFixed(2)} has been added to your balance.
            </DialogDescription>
          </DialogHeader>
          <Button
            onClick={() => setShowSuccessModal(false)}
            className="w-full bg-gradient-to-r from-fuchsia-600 to-purple-600 rounded-full"
            data-testid="success-modal-close"
          >
            Start Playing
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WalletPage;
