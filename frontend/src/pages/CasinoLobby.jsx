import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, API } from "../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import axios from "axios";
import { 
  Menu, Home, Clock, Gift, MessageCircle, Settings, 
  ChevronRight, Crown, Wallet, LogOut, User
} from "lucide-react";

// Provider logos/icons mapping
const PROVIDER_LOGOS = {
  jili: { name: "JILI", color: "#ff6b35", textColor: "#fff" },
  pragmatic: { name: "PRAGMATIC", color: "#e91e63", textColor: "#fff" },
  pgsoft: { name: "PG SOFT", color: "#7c3aed", textColor: "#fff" },
  spadegaming: { name: "SPADE", color: "#10b981", textColor: "#fff" },
  microgaming: { name: "MICRO GAMING", color: "#dc2626", textColor: "#fff" },
  hacksaw: { name: "HACKSAW", color: "#f59e0b", textColor: "#000" },
  evo888: { name: "EVO888H5", color: "#fbbf24", textColor: "#000" },
  epicwin: { name: "EPIC WIN", color: "#8b5cf6", textColor: "#fff" },
  afb777: { name: "AFB777", color: "#ef4444", textColor: "#fff" },
  vpower: { name: "V POWER", color: "#3b82f6", textColor: "#fff" },
  pegasus: { name: "PEGASUS", color: "#6366f1", textColor: "#fff" },
  booongo: { name: "BOOONGO", color: "#22c55e", textColor: "#fff" },
  advantplay: { name: "ADVANT PLAY", color: "#0ea5e9", textColor: "#fff" },
  jdb: { name: "JDB", color: "#f97316", textColor: "#fff" },
  uuslots: { name: "UU SLOTS", color: "#ec4899", textColor: "#fff" },
  acewin: { name: "ACE WIN", color: "#14b8a6", textColor: "#fff" },
  ace333: { name: "ACE333", color: "#eab308", textColor: "#000" },
  yellowbat: { name: "YELLOW BAT", color: "#facc15", textColor: "#000" },
  bgaming: { name: "BGAMING", color: "#64748b", textColor: "#fff" },
  fastspin: { name: "FAST SPIN", color: "#f43f5e", textColor: "#fff" },
  metagaming: { name: "META GAMING", color: "#d946ef", textColor: "#fff" },
  cq9: { name: "CQ9", color: "#0891b2", textColor: "#fff" },
  joker: { name: "JOKER", color: "#84cc16", textColor: "#000" },
  slotomania: { name: "SLOTOMANIA", color: "#c026d3", textColor: "#fff" },
  rich: { name: "RICH", color: "#fbbf24", textColor: "#000" },
};

// Popular games with images
const POPULAR_GAMES = [
  { id: "sugar_rush_1000", name: "Sugar Rush 1000", provider: "pragmatic", image: "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=400&h=400&fit=crop", hot: true },
  { id: "big_bass_bonanza", name: "Big Bass Bonanza 1000", provider: "pragmatic", image: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=400&fit=crop", hot: true },
  { id: "gates_of_gatot", name: "Gates of Gatot Kaca", provider: "pragmatic", image: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400&h=400&fit=crop", hot: true },
  { id: "starlight_princess", name: "Starlight Princess 1000", provider: "pragmatic", image: "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=400&h=400&fit=crop", new: true },
  { id: "sweet_bonanza", name: "Sweet Bonanza 1000", provider: "pragmatic", image: "https://images.unsplash.com/photo-1499195333224-3ce974eecb47?w=400&h=400&fit=crop", hot: true },
  { id: "wisdom_athena", name: "Wisdom of Athena", provider: "pragmatic", image: "https://images.unsplash.com/photo-1608889175123-8ee362201f81?w=400&h=400&fit=crop", new: true },
  { id: "lucky_tiger", name: "Lucky Tiger 1000", provider: "pgsoft", image: "https://images.unsplash.com/photo-1615963244664-5b845b2025ee?w=400&h=400&fit=crop", hot: true },
  { id: "gates_olympus", name: "Gates of Olympus 1000", provider: "pragmatic", image: "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=400&h=400&fit=crop", hot: true },
  { id: "fortune_tiger", name: "Fortune Tiger", provider: "pgsoft", image: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400&h=400&fit=crop", new: true },
];

// Live transactions mock data
const generateTransactions = () => {
  const types = ["deposit", "withdraw"];
  const providers = ["JILI", "BNG", "PG", "PP"];
  const transactions = [];
  for (let i = 0; i < 10; i++) {
    transactions.push({
      id: `61******${Math.floor(Math.random() * 900) + 100}`,
      type: types[Math.floor(Math.random() * 2)],
      amount: (Math.random() * 100 + 10).toFixed(2),
      provider: providers[Math.floor(Math.random() * providers.length)],
    });
  }
  return transactions;
};

const CasinoLobby = () => {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState("pokies");
  const [providers, setProviders] = useState([]);
  const [transactions, setTransactions] = useState(generateTransactions());
  const [showMenu, setShowMenu] = useState(false);

  const categories = [
    { id: "pokies", name: "POKIES", icon: "🎰" },
    { id: "slots", name: "SLOTS", icon: "🎲" },
    { id: "live", name: "LIVE", icon: "🎬" },
    { id: "fishing", name: "FISHING", icon: "🐟" },
    { id: "events", name: "EVENTS", icon: "🎁" },
  ];

  useEffect(() => {
    // Fetch providers
    const fetchProviders = async () => {
      try {
        const res = await axios.get(`${API}/providers/status`);
        setProviders(Object.entries(res.data));
      } catch (e) {
        console.error(e);
      }
    };
    fetchProviders();

    // Update transactions every 5 seconds
    const interval = setInterval(() => {
      setTransactions(generateTransactions());
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const allProviders = Object.keys(PROVIDER_LOGOS);

  return (
    <div className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-black/95 backdrop-blur-sm border-b border-yellow-900/30">
        <div className="flex items-center justify-between px-4 py-3">
          <button onClick={() => setShowMenu(!showMenu)} className="text-white p-2">
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg gold-border flex items-center justify-center">
              <Crown className="w-6 h-6 text-yellow-500" />
            </div>
            <div>
              <h1 className="font-bold text-lg gold-text font-heading">NEON</h1>
              <p className="text-[10px] text-yellow-600 -mt-1">BETKING</p>
            </div>
          </div>

          <button 
            onClick={() => navigate("/wallet")}
            className="flex items-center gap-1 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black px-3 py-1.5 rounded-full text-sm font-bold"
          >
            <Wallet className="w-4 h-4" />
            ${user?.balance?.toFixed(2) || '0.00'}
          </button>
        </div>

        {/* Marquee */}
        <div className="marquee-container py-1.5">
          <p className="marquee-text text-black text-xs font-semibold">
            🎰 Premium Black-Gold Pokies Hub For Aussie Players | Same-Day Withdrawals | High RTP Games | 24/7 Customer Support 🎰
          </p>
        </div>
      </header>

      {/* Side Menu */}
      <AnimatePresence>
        {showMenu && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 z-50"
              onClick={() => setShowMenu(false)}
            />
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              className="fixed left-0 top-0 bottom-0 w-72 bg-zinc-900 z-50 border-r border-yellow-900/30"
            >
              <div className="p-6 border-b border-yellow-900/30">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-yellow-500 to-yellow-600 flex items-center justify-center">
                    <User className="w-6 h-6 text-black" />
                  </div>
                  <div>
                    <p className="font-bold text-white">{user?.username}</p>
                    <p className="text-xs text-yellow-500">VIP Member</p>
                  </div>
                </div>
              </div>
              <nav className="p-4 space-y-2">
                {[
                  { icon: Home, label: "Home", path: "/lobby" },
                  { icon: Wallet, label: "Wallet", path: "/wallet" },
                  { icon: Crown, label: "VIP Club", path: "/vip" },
                  { icon: Gift, label: "Bonus", path: "/bonus" },
                  { icon: Clock, label: "History", path: "/history" },
                  { icon: Settings, label: "Settings", path: "/settings" },
                ].map((item) => (
                  <button
                    key={item.label}
                    onClick={() => { navigate(item.path); setShowMenu(false); }}
                    className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-yellow-500/10 text-gray-300 hover:text-yellow-500 transition-colors"
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                ))}
                <button
                  onClick={() => { logout(); navigate("/"); }}
                  className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-red-500/10 text-red-400 transition-colors mt-4"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              </nav>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Category Tabs */}
      <div className="px-3 py-3 overflow-x-auto">
        <div className="flex gap-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`category-tab flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                activeCategory === cat.id 
                  ? 'active bg-gradient-to-r from-yellow-500 to-yellow-600 text-black' 
                  : 'text-gray-300'
              }`}
            >
              <span>{cat.icon}</span>
              <span>{cat.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Promo Banner */}
      <div className="px-3 mb-4">
        <div className="promo-banner relative overflow-hidden rounded-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-black/80 to-transparent z-10" />
          <img 
            src="https://images.unsplash.com/photo-1596838132731-3301c3fd4317?w=800&h=300&fit=crop" 
            alt="Promo" 
            className="w-full h-40 object-cover"
          />
          <div className="absolute inset-0 z-20 p-6 flex flex-col justify-center">
            <p className="text-yellow-500 text-sm font-bold">WEEKLY</p>
            <h2 className="text-white text-2xl font-heading font-bold">KING BONUS</h2>
            <p className="gold-text text-4xl font-heading font-black">$2000</p>
          </div>
          <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1.5 z-20">
            {[0,1,2,3].map(i => (
              <div key={i} className={`w-2 h-2 rounded-full ${i === 0 ? 'bg-yellow-500' : 'bg-gray-600'}`} />
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-3 mb-4">
        <div className="flex gap-2">
          <button 
            onClick={() => navigate("/register")}
            className="flex-1 py-3 bg-zinc-900 border border-yellow-900/30 rounded-xl flex items-center justify-center gap-2 text-white font-semibold"
          >
            REGISTER <ChevronRight className="w-4 h-4" />
          </button>
          <button 
            onClick={() => navigate("/login")}
            className="flex-1 py-3 bg-zinc-900 border border-yellow-900/30 rounded-xl flex items-center justify-center gap-2 text-white font-semibold"
          >
            LOGIN <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Deposit/Withdraw Banner */}
      <div className="px-3 mb-4">
        <div className="flex items-center justify-between bg-zinc-900 border border-yellow-900/30 rounded-xl p-3">
          <div className="flex items-center gap-4">
            <span className="text-yellow-500 font-bold text-sm">DEPOSIT FAST & SECURE</span>
            <div className="flex items-center -space-x-1">
              {['💳', '🏦', '📱', '💰'].map((icon, i) => (
                <div key={i} className="w-6 h-6 bg-white rounded flex items-center justify-center text-sm">
                  {icon}
                </div>
              ))}
            </div>
          </div>
          <span className="text-yellow-500 font-bold text-sm">WITHDRAW NOW</span>
        </div>
      </div>

      {/* Provider Grid */}
      <div className="px-3 mb-6">
        <div className="grid grid-cols-3 gap-3">
          {allProviders.map((providerId, index) => {
            const provider = PROVIDER_LOGOS[providerId];
            return (
              <motion.button
                key={providerId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                onClick={() => navigate(`/games/provider/${providerId}`)}
                className="provider-card aspect-square flex flex-col items-center justify-center p-3 rounded-2xl"
              >
                <div 
                  className="w-full h-3/4 flex items-center justify-center rounded-lg mb-2"
                  style={{ backgroundColor: provider.color + '20' }}
                >
                  <span 
                    className="font-bold text-sm text-center leading-tight"
                    style={{ color: provider.color }}
                  >
                    {provider.name}
                  </span>
                </div>
                <div className="ratio-badge">RATIO 1:1</div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Live Transactions */}
      <div className="px-3 mb-6">
        <div className="bg-zinc-900 border border-yellow-900/30 rounded-xl overflow-hidden">
          <div className="p-3 border-b border-yellow-900/30">
            <h3 className="text-white font-bold flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              LIVE TRANSACTION
            </h3>
          </div>
          <div className="grid grid-cols-2">
            <div className="border-r border-yellow-900/30">
              <div className="p-2 bg-yellow-500/10 text-yellow-500 font-bold text-sm text-center">
                DEPOSIT
              </div>
              {transactions.filter(t => t.type === 'deposit').slice(0, 4).map((tx, i) => (
                <div key={i} className="transaction-row p-2 flex justify-between text-sm">
                  <span className="text-gray-400">{tx.id}</span>
                  <span className="text-green-400">AUD {tx.amount}</span>
                </div>
              ))}
            </div>
            <div>
              <div className="p-2 bg-yellow-500/10 text-yellow-500 font-bold text-sm text-center">
                WITHDRAW
              </div>
              {transactions.filter(t => t.type === 'withdraw').slice(0, 4).map((tx, i) => (
                <div key={i} className="transaction-row p-2 flex justify-between text-sm">
                  <span className="text-gray-400">{tx.id}</span>
                  <span className="text-yellow-400">AUD {tx.amount}</span>
                  <span className="text-gray-500 text-xs">{tx.provider}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Popular Games */}
      <div className="px-3 mb-6">
        <h3 className="text-white font-bold mb-3 flex items-center gap-2">
          🔥 HOT GAMES
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {POPULAR_GAMES.map((game, index) => (
            <motion.div
              key={game.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              className="game-card"
            >
              <div className="relative">
                <img 
                  src={game.image} 
                  alt={game.name}
                  className="game-card-image w-full rounded-t-xl"
                />
                {game.hot && (
                  <span className="absolute top-2 left-2 bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded">
                    HOT
                  </span>
                )}
                {game.new && (
                  <span className="absolute top-2 left-2 bg-green-500 text-white text-[10px] font-bold px-2 py-0.5 rounded">
                    NEW
                  </span>
                )}
              </div>
              <button 
                onClick={() => navigate(`/games/play/${game.id}`)}
                className="play-button w-full py-2 text-center font-bold text-sm rounded-b-xl"
              >
                PLAY
              </button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Bottom Navigation */}
      <nav className="bottom-nav fixed bottom-0 left-0 right-0 z-40">
        <div className="flex items-center justify-around py-2">
          {[
            { icon: Home, label: "HOME", path: "/lobby", active: true },
            { icon: Clock, label: "HISTORY", path: "/history" },
            { icon: Gift, label: "BONUS", path: "/bonus", badge: 1 },
            { icon: MessageCircle, label: "LIVE CHAT", path: "/chat", badge: 1 },
            { icon: Settings, label: "SETTING", path: "/settings" },
          ].map((item) => (
            <button
              key={item.label}
              onClick={() => navigate(item.path)}
              className={`bottom-nav-item flex flex-col items-center gap-1 px-3 py-1 ${item.active ? 'active' : ''}`}
            >
              <div className="relative">
                {item.label === "BONUS" ? (
                  <div className="w-10 h-10 -mt-4 bg-gradient-to-t from-yellow-600 to-yellow-400 rounded-full flex items-center justify-center border-4 border-black">
                    <Crown className="w-5 h-5 text-black" />
                  </div>
                ) : (
                  <item.icon className="w-5 h-5" />
                )}
                {item.badge && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
};

export default CasinoLobby;
