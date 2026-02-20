import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, API } from "../../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../components/ui/button";
import { toast } from "sonner";
import axios from "axios";
import { Zap, ArrowLeft, Wallet, Minus, Plus, RotateCcw } from "lucide-react";

// Card utilities
const SUITS = ["♠", "♥", "♦", "♣"];
const VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];

const createDeck = () => {
  const deck = [];
  for (const suit of SUITS) {
    for (const value of VALUES) {
      deck.push({ suit, value });
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

const getCardValue = (card) => {
  if (card.value === "A") return 11;
  if (["K", "Q", "J"].includes(card.value)) return 10;
  return parseInt(card.value);
};

const calculateHand = (cards) => {
  let total = 0;
  let aces = 0;
  
  for (const card of cards) {
    if (card.value === "A") aces++;
    total += getCardValue(card);
  }
  
  while (total > 21 && aces > 0) {
    total -= 10;
    aces--;
  }
  
  return total;
};

const Card = ({ card, hidden = false, delay = 0 }) => {
  const isRed = card.suit === "♥" || card.suit === "♦";
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, rotateY: 180 }}
      animate={{ opacity: 1, scale: 1, rotateY: hidden ? 180 : 0 }}
      transition={{ duration: 0.3, delay }}
      className="relative w-16 h-24 sm:w-20 sm:h-28"
    >
      <div className={`w-full h-full rounded-xl flex flex-col items-center justify-center shadow-lg ${
        hidden 
          ? 'bg-gradient-to-br from-purple-600 to-blue-600' 
          : 'bg-white'
      }`}>
        {hidden ? (
          <span className="text-2xl text-white/50">?</span>
        ) : (
          <>
            <span className={`text-lg font-bold ${isRed ? 'text-red-500' : 'text-black'}`}>
              {card.value}
            </span>
            <span className={`text-2xl ${isRed ? 'text-red-500' : 'text-black'}`}>
              {card.suit}
            </span>
          </>
        )}
      </div>
    </motion.div>
  );
};

const BlackjackGame = () => {
  const { user, token, updateBalance } = useAuth();
  const navigate = useNavigate();
  const [betAmount, setBetAmount] = useState(5);
  const [deck, setDeck] = useState([]);
  const [playerHand, setPlayerHand] = useState([]);
  const [dealerHand, setDealerHand] = useState([]);
  const [gameState, setGameState] = useState("betting"); // betting, playing, dealer, ended
  const [result, setResult] = useState(null);
  const [showDealerCard, setShowDealerCard] = useState(false);

  const adjustBet = (delta) => {
    const newBet = Math.max(1, Math.min(100, betAmount + delta));
    setBetAmount(newBet);
  };

  const startGame = () => {
    if (betAmount > (user?.balance || 0)) {
      toast.error("Insufficient balance");
      return;
    }

    const newDeck = shuffleDeck(createDeck());
    const pHand = [newDeck[0], newDeck[2]];
    const dHand = [newDeck[1], newDeck[3]];
    
    setDeck(newDeck.slice(4));
    setPlayerHand(pHand);
    setDealerHand(dHand);
    setShowDealerCard(false);
    setResult(null);
    setGameState("playing");

    // Check for blackjack
    if (calculateHand(pHand) === 21) {
      setTimeout(() => finishGame(pHand, dHand, newDeck.slice(4)), 1000);
    }
  };

  const hit = () => {
    const newCard = deck[0];
    const newHand = [...playerHand, newCard];
    setPlayerHand(newHand);
    setDeck(deck.slice(1));

    const total = calculateHand(newHand);
    if (total > 21) {
      setTimeout(() => finishGame(newHand, dealerHand, deck.slice(1)), 500);
    } else if (total === 21) {
      setTimeout(() => stand(newHand, deck.slice(1)), 500);
    }
  };

  const stand = (pHand = playerHand, currentDeck = deck) => {
    setGameState("dealer");
    setShowDealerCard(true);
    
    // Dealer plays
    let dHand = [...dealerHand];
    let dDeck = [...currentDeck];
    
    const playDealer = () => {
      const dealerTotal = calculateHand(dHand);
      if (dealerTotal < 17) {
        dHand = [...dHand, dDeck[0]];
        dDeck = dDeck.slice(1);
        setDealerHand(dHand);
        setDeck(dDeck);
        setTimeout(playDealer, 700);
      } else {
        finishGame(pHand, dHand, dDeck);
      }
    };
    
    setTimeout(playDealer, 700);
  };

  const finishGame = async (pHand, dHand, remainingDeck) => {
    const playerTotal = calculateHand(pHand);
    const dealerTotal = calculateHand(dHand);
    const playerBlackjack = pHand.length === 2 && playerTotal === 21;
    const dealerBlackjack = dHand.length === 2 && dealerTotal === 21;
    
    setShowDealerCard(true);
    setGameState("ended");

    try {
      const response = await axios.post(`${API}/games/play`,
        {
          game: "blackjack",
          amount: betAmount,
          bet_details: {
            player_value: playerTotal,
            dealer_value: dealerTotal,
            player_blackjack: playerBlackjack,
            dealer_blackjack: dealerBlackjack,
            player_bust: playerTotal > 21,
            dealer_bust: dealerTotal > 21
          }
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      updateBalance(response.data.new_balance);
      setResult({
        outcome: response.data.result.outcome,
        reason: response.data.result.reason,
        winAmount: response.data.win_amount
      });

      if (response.data.win_amount > 0) {
        toast.success(`🎉 You won $${response.data.win_amount.toFixed(2)}!`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Game error");
    }
  };

  const newGame = () => {
    setPlayerHand([]);
    setDealerHand([]);
    setDeck([]);
    setResult(null);
    setShowDealerCard(false);
    setGameState("betting");
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
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading text-lg font-bold">Blackjack</span>
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
          className="glass-heavy rounded-3xl p-6 neon-border-cyan"
        >
          {/* Title */}
          <div className="text-center mb-6">
            <h2 className="font-heading text-2xl font-bold text-white mb-1">BLACKJACK</h2>
            <p className="text-gray-400 text-sm">Beat the dealer to 21</p>
          </div>

          {/* Game Area */}
          <div className="min-h-[300px] flex flex-col justify-between">
            {/* Dealer Hand */}
            <div className="text-center mb-4">
              <p className="text-gray-400 text-sm mb-2">
                Dealer {showDealerCard && dealerHand.length > 0 ? `(${calculateHand(dealerHand)})` : ""}
              </p>
              <div className="flex justify-center gap-2">
                {dealerHand.map((card, index) => (
                  <Card 
                    key={index} 
                    card={card} 
                    hidden={index === 1 && !showDealerCard}
                    delay={index * 0.1}
                  />
                ))}
                {dealerHand.length === 0 && (
                  <div className="w-20 h-28 rounded-xl border-2 border-dashed border-white/20 flex items-center justify-center text-gray-500">
                    ?
                  </div>
                )}
              </div>
            </div>

            {/* Result Display */}
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  className="text-center my-4"
                >
                  <p className={`font-heading text-2xl font-bold ${
                    result.outcome === 'win' || result.outcome === 'blackjack' 
                      ? 'text-green-400' 
                      : result.outcome === 'push' 
                        ? 'text-yellow-400' 
                        : 'text-red-400'
                  }`}>
                    {result.outcome === 'blackjack' ? '🃏 BLACKJACK!' : 
                     result.outcome === 'win' ? '✅ YOU WIN!' :
                     result.outcome === 'push' ? '🤝 PUSH' : '❌ DEALER WINS'}
                  </p>
                  <p className="text-gray-400 text-sm">{result.reason}</p>
                  {result.winAmount > 0 && (
                    <p className="text-yellow-400 font-bold mt-1">+${result.winAmount.toFixed(2)}</p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Player Hand */}
            <div className="text-center mt-4">
              <div className="flex justify-center gap-2 mb-2">
                {playerHand.map((card, index) => (
                  <Card key={index} card={card} delay={index * 0.1 + 0.2} />
                ))}
                {playerHand.length === 0 && (
                  <div className="w-20 h-28 rounded-xl border-2 border-dashed border-white/20 flex items-center justify-center text-gray-500">
                    ?
                  </div>
                )}
              </div>
              <p className="text-gray-400 text-sm">
                Your Hand {playerHand.length > 0 ? `(${calculateHand(playerHand)})` : ""}
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="mt-6">
            {gameState === "betting" && (
              <>
                <div className="flex items-center justify-center gap-4 mb-4">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => adjustBet(-1)}
                    disabled={betAmount <= 1}
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
                    disabled={betAmount >= 100}
                    className="rounded-full border-white/20"
                    data-testid="increase-bet"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <Button
                  onClick={startGame}
                  disabled={betAmount > (user?.balance || 0)}
                  className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full h-12 font-bold"
                  data-testid="deal-btn"
                >
                  Deal Cards
                </Button>
              </>
            )}

            {gameState === "playing" && (
              <div className="flex gap-3">
                <Button
                  onClick={hit}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full h-12 font-bold"
                  data-testid="hit-btn"
                >
                  Hit
                </Button>
                <Button
                  onClick={() => stand()}
                  className="flex-1 bg-gradient-to-r from-yellow-600 to-orange-600 rounded-full h-12 font-bold"
                  data-testid="stand-btn"
                >
                  Stand
                </Button>
              </div>
            )}

            {gameState === "dealer" && (
              <div className="text-center py-4">
                <RotateCcw className="w-8 h-8 animate-spin mx-auto text-cyan-400" />
                <p className="text-gray-400 mt-2">Dealer playing...</p>
              </div>
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
          </div>
        </motion.div>

        {/* Game Info */}
        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          <div className="glass rounded-xl p-4">
            <p className="text-gray-400 text-sm">Blackjack</p>
            <p className="font-heading text-lg font-bold text-green-400">2.5x</p>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-gray-400 text-sm">Win</p>
            <p className="font-heading text-lg font-bold text-white">2x</p>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-gray-400 text-sm">Push</p>
            <p className="font-heading text-lg font-bold text-yellow-400">1x</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlackjackGame;
