import { useState, useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth, API } from "../../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../components/ui/button";
import { toast } from "sonner";
import axios from "axios";
import { Zap, ArrowLeft, Wallet, Minus, Plus, RotateCcw, Info, Trophy } from "lucide-react";
import { JackpotDisplay, JackpotWinModal, JackpotContribution } from "../../components/Jackpot";

const ThemedSlotGame = () => {
  const { themeId } = useParams();
  const { user, token, updateBalance } = useAuth();
  const navigate = useNavigate();
  const [slotInfo, setSlotInfo] = useState(null);
  const [betAmount, setBetAmount] = useState(1);
  const [reels, setReels] = useState(["❓", "❓", "❓"]);
  const [spinning, setSpinning] = useState(false);
  const [lastWin, setLastWin] = useState(null);
  const [jackpotContribution, setJackpotContribution] = useState(null);
  const [showJackpotWin, setShowJackpotWin] = useState(false);
  const [jackpotWinAmount, setJackpotWinAmount] = useState(0);
  const [showPaytable, setShowPaytable] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSlotInfo();
  }, [themeId]);

  const fetchSlotInfo = async () => {
    try {
      const response = await axios.get(`${API}/games/themed-slots/${themeId}`);
      setSlotInfo(response.data);
      setReels(response.data.symbols.slice(0, 3));
    } catch (error) {
      toast.error("Slot game not found");
      navigate("/lobby");
    } finally {
      setLoading(false);
    }
  };

  const adjustBet = (delta) => {
    const newBet = Math.max(0.5, Math.min(100, betAmount + delta));
    setBetAmount(newBet);
  };

  const spin = async () => {
    if (spinning) return;
    if (betAmount > (user?.balance || 0)) {
      toast.error("Insufficient balance");
      return;
    }

    setSpinning(true);
    setLastWin(null);

    // Animate reels
    const symbols = slotInfo?.symbols || ["🍒", "🍋", "🍊"];
    const spinInterval = setInterval(() => {
      setReels([
        symbols[Math.floor(Math.random() * symbols.length)],
        symbols[Math.floor(Math.random() * symbols.length)],
        symbols[Math.floor(Math.random() * symbols.length)],
      ]);
    }, 100);

    try {
      const response = await axios.post(`${API}/games/play`,
        {
          game: `themed_slot_${themeId}`,
          amount: betAmount,
          bet_details: {}
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      setTimeout(() => {
        clearInterval(spinInterval);
        setReels(response.data.result.reels);
        updateBalance(response.data.new_balance);
        setJackpotContribution(response.data.jackpot_contribution);

        if (response.data.jackpot_won) {
          setJackpotWinAmount(response.data.result.jackpot_amount);
          setShowJackpotWin(true);
        }

        if (response.data.win_amount > 0) {
          setLastWin(response.data.win_amount);
          toast.success(`🎉 You won $${response.data.win_amount.toFixed(2)}!`);
        }

        setSpinning(false);
      }, 2000);

    } catch (error) {
      clearInterval(spinInterval);
      setSpinning(false);
      toast.error(error.response?.data?.detail || "Spin failed");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  const bgStyle = slotInfo?.bg_color ? { backgroundColor: slotInfo.bg_color } : {};

  return (
    <div className="min-h-screen" style={{ ...bgStyle, background: `linear-gradient(to bottom, ${slotInfo?.bg_color || '#050505'}, #050505)` }}>
      {/* Header */}
      <nav className="sticky top-0 z-50 glass-heavy border-b border-white/10">
        <div className="max-w-4xl mx-auto flex items-center justify-between px-4 py-3">
          <Button 
            variant="ghost" 
            onClick={() => navigate("/lobby")}
            className="text-gray-400 hover:text-white"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Lobby
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-2xl">
              {slotInfo?.symbols?.[0] || "🎰"}
            </div>
            <span className="font-heading text-lg font-bold">{slotInfo?.name}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-yellow-500/50 text-yellow-400"
            onClick={() => navigate("/wallet")}
            data-testid="balance-btn"
          >
            <Wallet className="w-4 h-4 mr-2" />
            ${user?.balance?.toFixed(2)}
          </Button>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Jackpot Display */}
        <JackpotDisplay className="mb-6" />

        {/* Slot Machine */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative"
        >
          <div className="glass-heavy rounded-3xl p-6 neon-border">
            {/* Top Display */}
            <div className="text-center mb-4">
              <h2 className="font-heading text-2xl font-bold text-white mb-1">{slotInfo?.name}</h2>
              <p className="text-gray-400 text-sm">{slotInfo?.description}</p>
              <div className="flex items-center justify-center gap-4 mt-2 text-xs">
                <span className="px-2 py-1 rounded bg-white/10 text-gray-300">
                  RTP: {slotInfo?.rtp}%
                </span>
                <span className={`px-2 py-1 rounded ${
                  slotInfo?.volatility === 'high' ? 'bg-red-500/20 text-red-400' :
                  slotInfo?.volatility === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-green-500/20 text-green-400'
                }`}>
                  {slotInfo?.volatility?.toUpperCase()} Volatility
                </span>
              </div>
            </div>

            {/* Reels */}
            <div className="flex justify-center gap-4 mb-6">
              {reels.map((symbol, index) => (
                <motion.div
                  key={index}
                  animate={spinning ? { y: [0, -10, 0] } : {}}
                  transition={{ duration: 0.1, repeat: spinning ? Infinity : 0 }}
                  className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl bg-zinc-900/80 border-2 border-white/20 flex items-center justify-center shadow-lg"
                >
                  <span className="text-5xl sm:text-6xl">{symbol}</span>
                </motion.div>
              ))}
            </div>

            {/* Win Display */}
            <AnimatePresence>
              {lastWin && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  className="text-center mb-6"
                >
                  <p className="font-heading text-3xl font-black win-text animate-pulse">
                    WIN ${lastWin.toFixed(2)}!
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Paytable Toggle */}
            <div className="mb-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPaytable(!showPaytable)}
                className="w-full text-gray-400 hover:text-white"
                data-testid="paytable-toggle"
              >
                <Info className="w-4 h-4 mr-2" />
                {showPaytable ? "Hide" : "Show"} Paytable
              </Button>
              
              <AnimatePresence>
                {showPaytable && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="grid grid-cols-4 gap-2 mt-3 text-xs text-center">
                      {slotInfo?.symbols?.map((symbol, i) => (
                        <div key={i} className="bg-zinc-900/50 rounded-lg p-2">
                          <span className="text-2xl">{symbol}{symbol}{symbol}</span>
                          <p className="text-yellow-400 font-bold mt-1">
                            {slotInfo?.multipliers?.[symbol]}x
                          </p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Bet Controls */}
            <div className="flex items-center justify-center gap-4 mb-6">
              <Button
                variant="outline"
                size="icon"
                onClick={() => adjustBet(-0.5)}
                disabled={spinning || betAmount <= 0.5}
                className="rounded-full border-white/20 hover:bg-white/10"
                data-testid="decrease-bet"
              >
                <Minus className="w-4 h-4" />
              </Button>
              <div className="text-center">
                <p className="text-gray-400 text-xs mb-1">BET AMOUNT</p>
                <p className="font-heading text-2xl font-bold text-white">${betAmount.toFixed(2)}</p>
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={() => adjustBet(0.5)}
                disabled={spinning || betAmount >= 100}
                className="rounded-full border-white/20 hover:bg-white/10"
                data-testid="increase-bet"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            {/* Spin Button */}
            <Button
              onClick={spin}
              disabled={spinning || betAmount > (user?.balance || 0)}
              className="w-full rounded-full h-14 text-xl font-bold btn-neon"
              style={{ background: `linear-gradient(to right, ${slotInfo?.bg_color || '#d946ef'}, #9333ea)` }}
              data-testid="spin-btn"
            >
              {spinning ? (
                <RotateCcw className="w-6 h-6 animate-spin" />
              ) : (
                `🎰 SPIN`
              )}
            </Button>
          </div>
        </motion.div>

        {/* Jackpot Contribution */}
        {jackpotContribution && (
          <JackpotContribution amount={jackpotContribution} />
        )}
      </div>

      {/* Jackpot Win Modal */}
      <JackpotWinModal 
        open={showJackpotWin} 
        onClose={() => setShowJackpotWin(false)} 
        amount={jackpotWinAmount} 
      />
    </div>
  );
};

export default ThemedSlotGame;
