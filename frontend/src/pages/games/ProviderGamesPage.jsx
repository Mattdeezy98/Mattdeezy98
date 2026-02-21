import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, API } from "../../App";
import { motion } from "framer-motion";
import { Button } from "../../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { toast } from "sonner";
import axios from "axios";
import { 
  ArrowLeft, Wallet, Gamepad2, ExternalLink, Loader2, 
  CheckCircle2, XCircle, Zap, Search
} from "lucide-react";
import { Input } from "../../components/ui/input";

const ProviderGamesPage = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [providers, setProviders] = useState({});
  const [games, setGames] = useState([]);
  const [filteredGames, setFilteredGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeProvider, setActiveProvider] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [launching, setLaunching] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    filterGames();
  }, [games, activeProvider, searchQuery]);

  const fetchData = async () => {
    try {
      const [statusRes, gamesRes] = await Promise.all([
        axios.get(`${API}/providers/status`),
        axios.get(`${API}/providers/games`)
      ]);
      setProviders(statusRes.data);
      setGames(gamesRes.data.games);
    } catch (error) {
      toast.error("Failed to load games");
    } finally {
      setLoading(false);
    }
  };

  const filterGames = () => {
    let filtered = games;
    
    if (activeProvider !== "all") {
      filtered = filtered.filter(g => g.provider === activeProvider);
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(g => 
        g.name.toLowerCase().includes(query) ||
        g.type?.toLowerCase().includes(query)
      );
    }
    
    setFilteredGames(filtered);
  };

  const launchGame = async (provider, gameId, gameName) => {
    setLaunching(gameId);
    try {
      const response = await axios.post(
        `${API}/providers/${provider}/launch?game_id=${gameId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      if (response.data.mode === "demo") {
        toast.info(response.data.message);
        // Redirect to in-house slots as fallback
        navigate(`/games/${response.data.fallback_game}`);
      } else if (response.data.launch_url) {
        window.open(response.data.launch_url, "_blank");
        toast.success(`Launching ${gameName}...`);
      } else {
        toast.error("Failed to launch game");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to launch game");
    } finally {
      setLaunching(null);
    }
  };

  const getProviderColor = (provider) => {
    const colors = {
      jili: "from-yellow-600 to-orange-600",
      imperium: "from-purple-600 to-indigo-600",
      slotomania: "from-green-600 to-emerald-600",
      rich: "from-red-600 to-pink-600"
    };
    return colors[provider] || "from-gray-600 to-gray-500";
  };

  const getProviderLogo = (provider) => {
    const logos = {
      jili: "🎰",
      imperium: "👑",
      slotomania: "🎲",
      rich: "💰"
    };
    return logos[provider] || "🎮";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <nav className="sticky top-0 z-50 glass-heavy border-b border-white/10">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-3">
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
            <Gamepad2 className="w-5 h-5 text-purple-400" />
            <span className="font-heading text-lg font-bold">Provider Games</span>
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

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Provider Status Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {Object.entries(providers).map(([id, info]) => (
            <motion.div
              key={id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`glass rounded-xl p-4 cursor-pointer transition-all ${
                activeProvider === id ? 'ring-2 ring-purple-500' : ''
              }`}
              onClick={() => setActiveProvider(activeProvider === id ? "all" : id)}
              data-testid={`provider-${id}`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${getProviderColor(id)} flex items-center justify-center text-xl`}>
                  {getProviderLogo(id)}
                </div>
                <div>
                  <p className="font-bold text-white text-sm">{info.name}</p>
                  <p className="text-xs text-gray-400">{info.games_count} games</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {info.configured ? (
                  <>
                    <CheckCircle2 className="w-3 h-3 text-green-400" />
                    <span className="text-xs text-green-400">Live</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3 h-3 text-yellow-400" />
                    <span className="text-xs text-yellow-400">Demo</span>
                  </>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <Input
            placeholder="Search games..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-zinc-900/80 border-white/10 h-12 rounded-lg"
            data-testid="search-games"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          <Button
            variant={activeProvider === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveProvider("all")}
            className={activeProvider === "all" ? "bg-purple-600" : "border-white/10"}
          >
            All Games ({games.length})
          </Button>
          {Object.entries(providers).map(([id, info]) => (
            <Button
              key={id}
              variant={activeProvider === id ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveProvider(id)}
              className={activeProvider === id ? `bg-gradient-to-r ${getProviderColor(id)}` : "border-white/10"}
            >
              {info.name}
            </Button>
          ))}
        </div>

        {/* Games Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filteredGames.map((game, index) => (
            <motion.div
              key={game.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.02 }}
              className="group glass rounded-xl overflow-hidden card-hover"
              data-testid={`game-${game.id}`}
            >
              <div className={`aspect-square bg-gradient-to-br ${getProviderColor(game.provider)} p-4 flex flex-col items-center justify-center relative`}>
                <span className="text-4xl mb-2">{getProviderLogo(game.provider)}</span>
                <p className="text-white font-bold text-center text-sm line-clamp-2">{game.name}</p>
                <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-black/30 rounded text-[10px] text-white uppercase">
                  {game.type}
                </span>
              </div>
              <div className="p-3">
                <div className="flex items-center justify-between text-xs text-gray-400 mb-3">
                  <span>RTP: {game.rtp}%</span>
                  <span className={`px-1.5 py-0.5 rounded ${
                    game.volatility === 'high' ? 'bg-red-500/20 text-red-400' :
                    game.volatility === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {game.volatility}
                  </span>
                </div>
                <Button
                  onClick={() => launchGame(game.provider, game.id, game.name)}
                  disabled={launching === game.id}
                  className={`w-full bg-gradient-to-r ${getProviderColor(game.provider)} rounded-lg text-sm py-2`}
                  data-testid={`launch-${game.id}`}
                >
                  {launching === game.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Gamepad2 className="w-4 h-4 mr-1" />
                      Play
                    </>
                  )}
                </Button>
              </div>
            </motion.div>
          ))}
        </div>

        {filteredGames.length === 0 && (
          <div className="text-center py-12">
            <Gamepad2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No games found</p>
          </div>
        )}

        {/* Info Banner */}
        <div className="mt-8 glass rounded-xl p-4 text-center">
          <p className="text-gray-400 text-sm">
            <span className="text-yellow-400">⚠️ Demo Mode:</span> Provider games are shown in demo mode. 
            Add API keys in backend .env to enable real provider integration.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProviderGamesPage;
