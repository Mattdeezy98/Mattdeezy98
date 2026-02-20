import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Zap, Wallet, User, LogOut, Gamepad2, Trophy, ChevronDown, Shield } from "lucide-react";
import { JackpotDisplay } from "../components/Jackpot";
import { ResponsibleGamblingModal } from "../components/ResponsibleGambling";

const NavBar = ({ onOpenRG }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="sticky top-0 z-50 glass-heavy border-b border-white/10">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-3">
        <Link to="/lobby" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-heading text-lg font-bold gradient-text hidden sm:block">NeonVegas</span>
        </Link>

        <div className="flex items-center gap-3">
          {/* Balance Display */}
          <Button
            variant="outline"
            className="border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10 rounded-full px-4"
            onClick={() => navigate("/wallet")}
            data-testid="nav-balance-btn"
          >
            <Wallet className="w-4 h-4 mr-2" />
            <span className="font-mono font-bold">${user?.balance?.toFixed(2) || '0.00'}</span>
          </Button>

          {/* Deposit Button */}
          <Button
            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 rounded-full px-4"
            onClick={() => navigate("/wallet")}
            data-testid="nav-deposit-btn"
          >
            + Deposit
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="rounded-full px-3 hover:bg-white/10" data-testid="nav-user-menu">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center mr-2">
                  <User className="w-4 h-4 text-white" />
                </div>
                <span className="hidden sm:block text-white">{user?.username}</span>
                <ChevronDown className="w-4 h-4 ml-1 text-gray-400" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 bg-zinc-900 border-white/10">
              <div className="px-3 py-2">
                <p className="text-sm font-medium text-white">{user?.username}</p>
                <p className="text-xs text-gray-400">{user?.email}</p>
              </div>
              <DropdownMenuSeparator className="bg-white/10" />
              <DropdownMenuItem 
                onClick={() => navigate("/lobby")} 
                className="text-gray-300 hover:text-white cursor-pointer"
                data-testid="menu-games"
              >
                <Gamepad2 className="w-4 h-4 mr-2" />
                Games
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => navigate("/wallet")} 
                className="text-gray-300 hover:text-white cursor-pointer"
                data-testid="menu-wallet"
              >
                <Wallet className="w-4 h-4 mr-2" />
                Wallet
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={onOpenRG} 
                className="text-green-400 hover:text-green-300 cursor-pointer"
                data-testid="menu-responsible-gambling"
              >
                <Shield className="w-4 h-4 mr-2" />
                Responsible Gambling
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-white/10" />
              <DropdownMenuItem 
                onClick={() => {
                  logout();
                  navigate("/");
                }} 
                className="text-red-400 hover:text-red-300 cursor-pointer"
                data-testid="menu-logout"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  );
};

const CasinoLobby = () => {
  const navigate = useNavigate();
  const [showRGModal, setShowRGModal] = useState(false);

  const games = [
    {
      id: "slots",
      name: "Mega Slots",
      description: "Spin to win up to 100x!",
      image: "https://images.unsplash.com/photo-1566563255308-753861417000?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      color: "from-pink-600 to-purple-600",
      minBet: "$0.50",
      maxWin: "100x",
    },
    {
      id: "blackjack",
      name: "Blackjack",
      description: "Beat the dealer to 21",
      image: "https://images.unsplash.com/photo-1642867749315-d1467617a2f4?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      color: "from-emerald-600 to-teal-600",
      minBet: "$1.00",
      maxWin: "2.5x",
    },
    {
      id: "roulette",
      name: "Roulette",
      description: "Place your bets & spin",
      image: "https://images.pexels.com/photos/7594162/pexels-photo-7594162.jpeg?w=600",
      color: "from-red-600 to-orange-600",
      minBet: "$1.00",
      maxWin: "35x",
    },
    {
      id: "poker",
      name: "Video Poker",
      description: "Jacks or Better",
      image: "https://images.unsplash.com/photo-1743677042704-74a8390e765a?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      color: "from-cyan-600 to-blue-600",
      minBet: "$0.50",
      maxWin: "800x",
    },
  ];

  return (
    <div className="min-h-screen bg-[#050505]">
      <NavBar onOpenRG={() => setShowRGModal(true)} />

      {/* Hero Banner with Jackpot */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/40 via-transparent to-cyan-900/40" />
        <div className="max-w-7xl mx-auto px-4 py-8 relative">
          {/* Jackpot Display */}
          <JackpotDisplay className="mb-6" />
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h1 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
              Choose Your <span className="gradient-text">Game</span>
            </h1>
            <p className="text-gray-400 max-w-lg mx-auto">
              Premium casino games with the best odds. Play smart, win big.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Games Grid */}
      <div className="max-w-7xl mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {games.map((game, index) => (
            <motion.div
              key={game.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => navigate(`/games/${game.id}`)}
              className="group cursor-pointer"
              data-testid={`lobby-game-${game.id}`}
            >
              <div className="relative overflow-hidden rounded-2xl card-hover neon-border">
                <div className="aspect-[3/4] relative">
                  <img
                    src={game.image}
                    alt={game.name}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />
                  <div className={`absolute inset-0 bg-gradient-to-t ${game.color} opacity-0 group-hover:opacity-30 transition-opacity duration-300`} />
                  
                  {/* Game Info */}
                  <div className="absolute bottom-0 left-0 right-0 p-5">
                    <h3 className="font-heading text-xl font-bold text-white mb-1">{game.name}</h3>
                    <p className="text-gray-400 text-sm mb-3">{game.description}</p>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">Min: {game.minBet}</span>
                      <span className="px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 text-xs font-bold">
                        Up to {game.maxWin}
                      </span>
                    </div>
                  </div>

                  {/* Play Button Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button className={`bg-gradient-to-r ${game.color} rounded-full px-8 py-3 font-bold shadow-lg`}>
                      <Gamepad2 className="w-5 h-5 mr-2" />
                      Play Now
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Quick Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4"
        >
          {[
            { label: "Total Won Today", value: "$847,392", color: "text-green-400" },
            { label: "Active Players", value: "1,234", color: "text-cyan-400" },
            { label: "Biggest Win", value: "$12,500", color: "text-yellow-400" },
            { label: "Games Played", value: "45,678", color: "text-purple-400" },
          ].map((stat, index) => (
            <div key={index} className="glass rounded-xl p-4 text-center">
              <p className={`font-heading text-xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-gray-500">{stat.label}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
};

export default CasinoLobby;
