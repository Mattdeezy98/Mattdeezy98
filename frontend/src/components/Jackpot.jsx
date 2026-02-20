import { useState, useEffect } from "react";
import { API } from "../App";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { Trophy, Sparkles } from "lucide-react";

export const JackpotDisplay = ({ className = "" }) => {
  const [jackpot, setJackpot] = useState(1000);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJackpot();
    // Poll jackpot every 10 seconds
    const interval = setInterval(fetchJackpot, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchJackpot = async () => {
    try {
      const response = await axios.get(`${API}/jackpot`);
      setJackpot(response.data.amount);
    } catch (error) {
      console.error("Failed to fetch jackpot:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-r from-yellow-600/20 via-orange-600/20 to-yellow-600/20 border border-yellow-500/30 p-4 ${className}`}
      data-testid="jackpot-display"
    >
      {/* Animated background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-yellow-500/10 via-transparent to-transparent animate-pulse" />
      
      <div className="relative flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center animate-pulse">
            <Trophy className="w-6 h-6 text-black" />
          </div>
          <div>
            <p className="text-yellow-400 text-sm font-medium flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              PROGRESSIVE JACKPOT
            </p>
            <motion.p
              key={jackpot}
              initial={{ scale: 1.1 }}
              animate={{ scale: 1 }}
              className="font-heading text-2xl sm:text-3xl font-black text-white"
            >
              ${jackpot.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </motion.p>
          </div>
        </div>
        
        <div className="hidden sm:block text-right">
          <p className="text-xs text-gray-400">Win up to</p>
          <p className="text-yellow-400 font-bold">ANY SPIN!</p>
        </div>
      </div>
    </motion.div>
  );
};

export const JackpotWinModal = ({ open, onClose, amount }) => {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.5, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0.5, rotate: 10 }}
            transition={{ type: "spring", damping: 15 }}
            className="relative p-8 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Confetti effect */}
            <div className="absolute inset-0 pointer-events-none">
              {[...Array(20)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ 
                    opacity: 1, 
                    x: 0, 
                    y: 0,
                    scale: 1
                  }}
                  animate={{ 
                    opacity: 0, 
                    x: (Math.random() - 0.5) * 400,
                    y: (Math.random() - 0.5) * 400,
                    scale: 0
                  }}
                  transition={{ duration: 2, delay: i * 0.1 }}
                  className="absolute left-1/2 top-1/2 w-4 h-4 rounded-full"
                  style={{
                    background: ['#eab308', '#f97316', '#ef4444', '#22c55e', '#06b6d4'][i % 5]
                  }}
                />
              ))}
            </div>

            <motion.div
              animate={{ 
                scale: [1, 1.1, 1],
                rotate: [0, 5, -5, 0]
              }}
              transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 1 }}
              className="mb-6"
            >
              <Trophy className="w-24 h-24 text-yellow-400 mx-auto" />
            </motion.div>

            <h1 className="font-heading text-4xl sm:text-5xl font-black text-white mb-4">
              🎉 JACKPOT! 🎉
            </h1>
            
            <motion.p
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="font-heading text-5xl sm:text-6xl font-black win-text mb-6"
            >
              ${amount?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </motion.p>

            <p className="text-gray-400 mb-6">Congratulations! You've won the progressive jackpot!</p>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onClose}
              className="px-8 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full font-bold text-black"
              data-testid="jackpot-close-btn"
            >
              Claim Winnings
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export const JackpotContribution = ({ amount }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center text-xs text-gray-500 mt-2"
    >
      <span className="text-yellow-400">${amount?.toFixed(2)}</span> added to jackpot
    </motion.div>
  );
};

export default JackpotDisplay;
