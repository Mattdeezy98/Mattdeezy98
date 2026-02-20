import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, API } from "../../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../components/ui/button";
import { toast } from "sonner";
import axios from "axios";
import { Zap, ArrowLeft, Wallet, Minus, Plus, RefreshCw } from "lucide-react";

const SUITS = ["♠", "♥", "♦", "♣"];
const VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];

const createDeck = () => {
  const deck = [];
  for (const suit of SUITS) {
    for (const value of VALUES) {
      deck.push({ suit, value, held: false });
    }
  }
  return deck;
};

const shuffleDeck = (deck) => {
  const shuffled = [...deck];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

const evaluateHand = (cards) => {
  const values = cards.map(c => c.value);
  const suits = cards.map(c => c.suit);
  
  const valueCounts = {};
  values.forEach(v => {
    valueCounts[v] = (valueCounts[v] || 0) + 1;
  });
  
  const counts = Object.values(valueCounts).sort((a, b) => b - a);
  const uniqueValues = Object.keys(valueCounts);
  
  const isFlush = suits.every(s => s === suits[0]);
  
  const valueOrder = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
  const sortedIndices = values.map(v => valueOrder.indexOf(v)).sort((a, b) => a - b);
  const isStraight = sortedIndices.every((v, i, arr) => i === 0 || v === arr[i - 1] + 1) ||
                    JSON.stringify(sortedIndices) === JSON.stringify([0, 9, 10, 11, 12]); // A-10-J-Q-K
  
  const isRoyalFlush = isFlush && JSON.stringify(sortedIndices.sort()) === JSON.stringify([0, 9, 10, 11, 12]);
  
  if (isRoyalFlush) return { rank: "royal_flush", name: "Royal Flush", multiplier: 800 };
  if (isFlush && isStraight) return { rank: "straight_flush", name: "Straight Flush", multiplier: 50 };
  if (counts[0] === 4) return { rank: "four_of_a_kind", name: "Four of a Kind", multiplier: 25 };
  if (counts[0] === 3 && counts[1] === 2) return { rank: "full_house", name: "Full House", multiplier: 9 };
  if (isFlush) return { rank: "flush", name: "Flush", multiplier: 6 };
  if (isStraight) return { rank: "straight", name: "Straight", multiplier: 4 };
  if (counts[0] === 3) return { rank: "three_of_a_kind", name: "Three of a Kind", multiplier: 3 };
  if (counts[0] === 2 && counts[1] === 2) return { rank: "two_pair", name: "Two Pair", multiplier: 2 };
  if (counts[0] === 2) {
    const pairValue = Object.keys(valueCounts).find(k => valueCounts[k] === 2);
    if (["J", "Q", "K", "A"].includes(pairValue)) {
      return { rank: "jacks_or_better", name: "Jacks or Better", multiplier: 1 };
    }
  }
  return { rank: "none", name: "No Win", multiplier: 0 };
};

const Card = ({ card, onClick, disabled }) => {
  const isRed = card.suit === "♥" || card.suit === "♦";
  
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      className={`relative w-14 h-20 sm:w-16 sm:h-24 rounded-lg flex flex-col items-center justify-center shadow-lg transition-all ${
        card.held ? 'ring-2 ring-yellow-400 -translate-y-2' : ''
      } ${disabled ? 'cursor-default' : 'cursor-pointer hover:shadow-xl'}`}
      style={{ background: 'linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%)' }}
    >
      <span className={`text-sm sm:text-base font-bold ${isRed ? 'text-red-500' : 'text-black'}`}>
        {card.value}
      </span>
      <span className={`text-lg sm:text-xl ${isRed ? 'text-red-500' : 'text-black'}`}>
        {card.suit}
      </span>
      {card.held && (
        <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-1 py-0.5 bg-yellow-400 text-black text-[10px] font-bold rounded">
          HELD
        </span>
      )}
    </motion.button>
  );
};

const PokerGame = () => {
  const { user, token, updateBalance } = useAuth();
  const navigate = useNavigate();
  const [betAmount, setBetAmount] = useState(1);
  const [deck, setDeck] = useState([]);
  const [hand, setHand] = useState([]);
  const [gameState, setGameState] = useState("betting"); // betting, deal, draw, ended
  const [result, setResult] = useState(null);

  const adjustBet = (delta) => {
    const newBet = Math.max(0.5, Math.min(50, betAmount + delta));
    setBetAmount(newBet);
  };

  const deal = () => {
    if (betAmount > (user?.balance || 0)) {
      toast.error("Insufficient balance");
      return;
    }

    const newDeck = shuffleDeck(createDeck());
    const newHand = newDeck.slice(0, 5).map(c => ({ ...c, held: false }));
    
    setDeck(newDeck.slice(5));
    setHand(newHand);
    setResult(null);
    setGameState("deal");
  };

  const toggleHold = (index) => {
    if (gameState !== "deal") return;
    
    setHand(prev => prev.map((card, i) => 
      i === index ? { ...card, held: !card.held } : card
    ));
  };

  const draw = async () => {
    // Replace non-held cards
    let deckIndex = 0;
    const newHand = hand.map(card => {
      if (card.held) return card;
      const newCard = deck[deckIndex++];
      return { ...newCard, held: false };
    });
    
    setHand(newHand);
    setDeck(deck.slice(deckIndex));
    setGameState("ended");

    // Evaluate hand
    const evaluation = evaluateHand(newHand);
    setResult(evaluation);

    // Send to backend
    try {
      const response = await axios.post(`${API}/games/play`,
        {
          game: "poker",
          amount: betAmount,
          bet_details: {
            hand_rank: evaluation.rank
          }
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      updateBalance(response.data.new_balance);
      
      if (response.data.win_amount > 0) {
        toast.success(`🎉 ${evaluation.name}! You won $${response.data.win_amount.toFixed(2)}!`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Game error");
    }
  };

  const newGame = () => {
    setHand([]);
    setDeck([]);
    setResult(null);
    setGameState("betting");
  };

  const payTable = [
    { name: "Royal Flush", payout: "800x" },
    { name: "Straight Flush", payout: "50x" },
    { name: "4 of a Kind", payout: "25x" },
    { name: "Full House", payout: "9x" },
    { name: "Flush", payout: "6x" },
    { name: "Straight", payout: "4x" },
    { name: "3 of a Kind", payout: "3x" },
    { name: "Two Pair", payout: "2x" },
    { name: "Jacks or Better", payout: "1x" },
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
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading text-lg font-bold">Video Poker</span>
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
          style={{ borderColor: 'rgba(6, 182, 212, 0.5)', boxShadow: '0 0 15px rgba(6, 182, 212, 0.3)', borderWidth: '1px' }}
        >
          {/* Title */}
          <div className="text-center mb-4">
            <h2 className="font-heading text-2xl font-bold text-white mb-1">VIDEO POKER</h2>
            <p className="text-gray-400 text-sm">Jacks or Better</p>
          </div>

          {/* Pay Table */}
          <div className="grid grid-cols-3 gap-1 mb-4 text-xs">
            {payTable.map((item, i) => (
              <div key={i} className={`p-1.5 rounded text-center ${
                result?.name === item.name ? 'bg-yellow-500/30 text-yellow-400' : 'bg-zinc-900/50 text-gray-400'
              }`}>
                <p className="truncate">{item.name}</p>
                <p className="font-bold">{item.payout}</p>
              </div>
            ))}
          </div>

          {/* Cards */}
          <div className="flex justify-center gap-2 mb-4">
            {hand.length > 0 ? (
              hand.map((card, index) => (
                <Card
                  key={index}
                  card={card}
                  onClick={() => toggleHold(index)}
                  disabled={gameState !== "deal"}
                />
              ))
            ) : (
              [...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="w-14 h-20 sm:w-16 sm:h-24 rounded-lg border-2 border-dashed border-white/20 flex items-center justify-center text-gray-500"
                >
                  ?
                </div>
              ))
            )}
          </div>

          {/* Instructions */}
          {gameState === "deal" && (
            <p className="text-center text-cyan-400 text-sm mb-4 animate-pulse">
              Click cards to HOLD, then press DRAW
            </p>
          )}

          {/* Result */}
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center mb-4"
              >
                <p className={`font-heading text-xl font-bold ${
                  result.multiplier > 0 ? 'text-yellow-400' : 'text-gray-400'
                }`}>
                  {result.multiplier > 0 ? `🎉 ${result.name}!` : result.name}
                </p>
                {result.multiplier > 0 && (
                  <p className="text-green-400 font-bold">+${(betAmount * result.multiplier).toFixed(2)}</p>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Controls */}
          {gameState === "betting" && (
            <>
              <div className="flex items-center justify-center gap-4 mb-4">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => adjustBet(-0.5)}
                  disabled={betAmount <= 0.5}
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
                  onClick={() => adjustBet(0.5)}
                  disabled={betAmount >= 50}
                  className="rounded-full border-white/20"
                  data-testid="increase-bet"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <Button
                onClick={deal}
                disabled={betAmount > (user?.balance || 0)}
                className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 rounded-full h-12 font-bold"
                data-testid="deal-btn"
              >
                🃏 DEAL
              </Button>
            </>
          )}

          {gameState === "deal" && (
            <Button
              onClick={draw}
              className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 rounded-full h-12 font-bold"
              data-testid="draw-btn"
            >
              <RefreshCw className="w-5 h-5 mr-2" />
              DRAW
            </Button>
          )}

          {gameState === "ended" && (
            <Button
              onClick={newGame}
              className="w-full bg-gradient-to-r from-fuchsia-600 to-purple-600 rounded-full h-12 font-bold"
              data-testid="new-game-btn"
            >
              New Game
            </Button>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default PokerGame;
