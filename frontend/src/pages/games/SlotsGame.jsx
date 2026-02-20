import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, API } from "../../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { toast } from "sonner";
import axios from "axios";
import { Zap, ArrowLeft, Wallet, Minus, Plus, Volume2, VolumeX, RotateCcw, Trophy } from "lucide-react";
import { JackpotDisplay, JackpotWinModal, JackpotContribution } from "../../components/Jackpot";

const SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "⭐", "7️⃣", "💎"];

const SlotsGame = () => {
  const { user, token, updateBalance } = useAuth();
  const navigate = useNavigate();
  const [betAmount, setBetAmount] = useState(1);
  const [reels, setReels] = useState(["🍒", "🍒", "🍒"]);
  const [spinning, setSpinning] = useState(false);
  const [lastWin, setLastWin] = useState(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [jackpotContribution, setJackpotContribution] = useState(null);
  const [showJackpotWin, setShowJackpotWin] = useState(false);
  const [jackpotWinAmount, setJackpotWinAmount] = useState(0);
  const audioRef = useRef(null);

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
    const spinInterval = setInterval(() => {
      setReels([
        SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
        SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
        SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
      ]);
    }, 100);

    try {
      const response = await axios.post(`${API}/games/play`,
        {
          game: "slots",
          amount: betAmount,
          bet_details: {}
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      // Stop animation after delay
      setTimeout(() => {
        clearInterval(spinInterval);
        setReels(response.data.result.reels);
        updateBalance(response.data.new_balance);
        
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

  return (
    <div className="min-h-screen bg-[#050505]">
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
          <Link to="/lobby" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-purple-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading text-lg font-bold">Mega Slots</span>
          </Link>
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
        {/* Slot Machine */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative"
        >
          {/* Machine Frame */}
          <div className="glass-heavy rounded-3xl p-6 neon-border">
            {/* Top Display */}
            <div className="text-center mb-6">
              <h2 className="font-heading text-2xl font-bold gradient-text mb-1">MEGA SLOTS</h2>
              <p className="text-gray-400 text-sm">Match 3 to win big!</p>
            </div>

            {/* Reels */}
            <div className="flex justify-center gap-4 mb-6">
              {reels.map((symbol, index) => (
                <motion.div
                  key={index}
                  animate={spinning ? { y: [0, -10, 0] } : {}}
                  transition={{ duration: 0.1, repeat: spinning ? Infinity : 0 }}
                  className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl bg-zinc-900 border-2 border-white/10 flex items-center justify-center"
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

            {/* Paytable */}
            <div className="grid grid-cols-3 gap-2 mb-6 text-xs text-center">
              <div className="bg-zinc-900/50 rounded-lg p-2">
                <span className="text-lg">💎💎💎</span>
                <p className="text-yellow-400 font-bold">100x</p>
              </div>
              <div className="bg-zinc-900/50 rounded-lg p-2">
                <span className="text-lg">7️⃣7️⃣7️⃣</span>
                <p className="text-yellow-400 font-bold">50x</p>
              </div>
              <div className="bg-zinc-900/50 rounded-lg p-2">
                <span className="text-lg">⭐⭐⭐</span>
                <p className="text-yellow-400 font-bold">25x</p>
              </div>
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
              className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 rounded-full h-14 text-xl font-bold btn-neon"
              data-testid="spin-btn"
            >
              {spinning ? (
                <RotateCcw className="w-6 h-6 animate-spin" />
              ) : (
                "🎰 SPIN"
              )}
            </Button>
          </div>
        </motion.div>

        {/* Game Info */}
        <div className="mt-6 grid grid-cols-2 gap-4 text-center">
          <div className="glass rounded-xl p-4">
            <p className="text-gray-400 text-sm">Min Bet</p>
            <p className="font-heading text-lg font-bold text-white">$0.50</p>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-gray-400 text-sm">Max Win</p>
            <p className="font-heading text-lg font-bold text-yellow-400">100x</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SlotsGame;
