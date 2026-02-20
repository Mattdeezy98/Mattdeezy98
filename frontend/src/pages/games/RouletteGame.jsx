import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, API } from "../../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../components/ui/button";
import { toast } from "sonner";
import axios from "axios";
import { Zap, ArrowLeft, Wallet, Minus, Plus } from "lucide-react";

const RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36];

const RouletteGame = () => {
  const { user, token, updateBalance } = useAuth();
  const navigate = useNavigate();
  const [betAmount, setBetAmount] = useState(5);
  const [betType, setBetType] = useState("color"); // color, number, even, odd, low, high
  const [selectedColor, setSelectedColor] = useState("red");
  const [selectedNumber, setSelectedNumber] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const [wheelRotation, setWheelRotation] = useState(0);

  const adjustBet = (delta) => {
    const newBet = Math.max(1, Math.min(100, betAmount + delta));
    setBetAmount(newBet);
  };

  const getNumberColor = (num) => {
    if (num === 0) return "green";
    return RED_NUMBERS.includes(num) ? "red" : "black";
  };

  const spin = async () => {
    if (spinning) return;
    if (betAmount > (user?.balance || 0)) {
      toast.error("Insufficient balance");
      return;
    }

    setSpinning(true);
    setResult(null);

    // Animate wheel
    const newRotation = wheelRotation + 1800 + Math.random() * 720;
    setWheelRotation(newRotation);

    try {
      const response = await axios.post(`${API}/games/play`,
        {
          game: "roulette",
          amount: betAmount,
          bet_details: {
            bet_type: betType,
            bet_color: selectedColor,
            bet_number: selectedNumber
          }
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      setTimeout(() => {
        updateBalance(response.data.new_balance);
        setResult(response.data.result);
        setSpinning(false);

        if (response.data.win_amount > 0) {
          toast.success(`🎉 You won $${response.data.win_amount.toFixed(2)}!`);
        }
      }, 4000);

    } catch (error) {
      setSpinning(false);
      toast.error(error.response?.data?.detail || "Spin failed");
    }
  };

  const betTypes = [
    { id: "color", label: "Color", payout: "2x" },
    { id: "even", label: "Even", payout: "2x" },
    { id: "odd", label: "Odd", payout: "2x" },
    { id: "low", label: "1-18", payout: "2x" },
    { id: "high", label: "19-36", payout: "2x" },
    { id: "straight", label: "Number", payout: "35x" },
  ];

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
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-red-500 to-orange-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading text-lg font-bold">Roulette</span>
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
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-heavy rounded-3xl p-6"
          style={{ borderColor: 'rgba(239, 68, 68, 0.5)', boxShadow: '0 0 15px rgba(239, 68, 68, 0.3)', borderWidth: '1px' }}
        >
          {/* Title */}
          <div className="text-center mb-6">
            <h2 className="font-heading text-2xl font-bold text-white mb-1">ROULETTE</h2>
            <p className="text-gray-400 text-sm">Place your bets!</p>
          </div>

          {/* Wheel */}
          <div className="flex justify-center mb-6">
            <div className="relative w-48 h-48">
              <motion.div
                animate={{ rotate: wheelRotation }}
                transition={{ duration: 4, ease: [0.17, 0.67, 0.12, 0.99] }}
                className="w-full h-full rounded-full border-4 border-yellow-500/50"
                style={{
                  background: `conic-gradient(
                    #22c55e 0deg 10deg,
                    #ef4444 10deg 20deg,
                    #000000 20deg 30deg,
                    #ef4444 30deg 40deg,
                    #000000 40deg 50deg,
                    #ef4444 50deg 60deg,
                    #000000 60deg 70deg,
                    #ef4444 70deg 80deg,
                    #000000 80deg 90deg,
                    #ef4444 90deg 100deg,
                    #000000 100deg 110deg,
                    #ef4444 110deg 120deg,
                    #000000 120deg 130deg,
                    #ef4444 130deg 140deg,
                    #000000 140deg 150deg,
                    #ef4444 150deg 160deg,
                    #000000 160deg 170deg,
                    #ef4444 170deg 180deg,
                    #000000 180deg 190deg,
                    #ef4444 190deg 200deg,
                    #000000 200deg 210deg,
                    #ef4444 210deg 220deg,
                    #000000 220deg 230deg,
                    #ef4444 230deg 240deg,
                    #000000 240deg 250deg,
                    #ef4444 250deg 260deg,
                    #000000 260deg 270deg,
                    #ef4444 270deg 280deg,
                    #000000 280deg 290deg,
                    #ef4444 290deg 300deg,
                    #000000 300deg 310deg,
                    #ef4444 310deg 320deg,
                    #000000 320deg 330deg,
                    #ef4444 330deg 340deg,
                    #000000 340deg 350deg,
                    #ef4444 350deg 360deg
                  )`
                }}
              >
                <div className="absolute inset-4 rounded-full bg-zinc-900 flex items-center justify-center">
                  <AnimatePresence mode="wait">
                    {result ? (
                      <motion.div
                        key="result"
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="text-center"
                      >
                        <p className={`font-heading text-3xl font-bold ${
                          result.result_color === 'red' ? 'text-red-500' :
                          result.result_color === 'green' ? 'text-green-500' : 'text-white'
                        }`}>
                          {result.result_number}
                        </p>
                        <p className="text-xs text-gray-400 uppercase">{result.result_color}</p>
                      </motion.div>
                    ) : (
                      <motion.p
                        key="waiting"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="font-heading text-xl text-gray-500"
                      >
                        {spinning ? "..." : "?"}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
              {/* Pointer */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[16px] border-b-yellow-500" />
            </div>
          </div>

          {/* Result */}
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-center mb-6"
              >
                <p className={`font-heading text-xl font-bold ${result.win ? 'text-green-400' : 'text-red-400'}`}>
                  {result.win ? `✅ WIN! ${result.payout}x` : '❌ No win'}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Bet Type Selection */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            {betTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setBetType(type.id)}
                disabled={spinning}
                className={`p-2 rounded-lg text-center transition-all ${
                  betType === type.id
                    ? 'bg-gradient-to-r from-red-600 to-orange-600 text-white'
                    : 'bg-zinc-900/50 text-gray-400 hover:bg-zinc-900'
                }`}
                data-testid={`bet-type-${type.id}`}
              >
                <p className="font-medium text-sm">{type.label}</p>
                <p className="text-xs opacity-70">{type.payout}</p>
              </button>
            ))}
          </div>

          {/* Bet Selection */}
          {betType === "color" && (
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setSelectedColor("red")}
                disabled={spinning}
                className={`flex-1 p-3 rounded-lg font-bold transition-all ${
                  selectedColor === "red"
                    ? 'bg-red-600 text-white ring-2 ring-red-400'
                    : 'bg-red-600/30 text-red-400'
                }`}
                data-testid="color-red"
              >
                RED
              </button>
              <button
                onClick={() => setSelectedColor("black")}
                disabled={spinning}
                className={`flex-1 p-3 rounded-lg font-bold transition-all ${
                  selectedColor === "black"
                    ? 'bg-zinc-700 text-white ring-2 ring-white/50'
                    : 'bg-zinc-800/50 text-gray-400'
                }`}
                data-testid="color-black"
              >
                BLACK
              </button>
            </div>
          )}

          {betType === "straight" && (
            <div className="mb-4">
              <p className="text-gray-400 text-sm mb-2">Select a number (0-36)</p>
              <div className="grid grid-cols-10 gap-1 max-h-[120px] overflow-y-auto">
                {[...Array(37)].map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedNumber(i)}
                    disabled={spinning}
                    className={`p-2 rounded text-sm font-bold transition-all ${
                      selectedNumber === i
                        ? 'ring-2 ring-yellow-400'
                        : ''
                    } ${
                      i === 0 ? 'bg-green-600 text-white' :
                      RED_NUMBERS.includes(i) ? 'bg-red-600 text-white' : 'bg-zinc-700 text-white'
                    }`}
                    data-testid={`number-${i}`}
                  >
                    {i}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Bet Amount */}
          <div className="flex items-center justify-center gap-4 mb-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => adjustBet(-1)}
              disabled={spinning || betAmount <= 1}
              className="rounded-full border-white/20"
              data-testid="decrease-bet"
            >
              <Minus className="w-4 h-4" />
            </Button>
            <div className="text-center">
              <p className="text-gray-400 text-xs">BET</p>
              <p className="font-heading text-2xl font-bold">${betAmount.toFixed(2)}</p>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => adjustBet(1)}
              disabled={spinning || betAmount >= 100}
              className="rounded-full border-white/20"
              data-testid="increase-bet"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {/* Spin Button */}
          <Button
            onClick={spin}
            disabled={spinning || betAmount > (user?.balance || 0)}
            className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 rounded-full h-12 font-bold"
            data-testid="spin-btn"
          >
            {spinning ? "Spinning..." : "🎡 SPIN"}
          </Button>
        </motion.div>
      </div>
    </div>
  );
};

export default RouletteGame;
