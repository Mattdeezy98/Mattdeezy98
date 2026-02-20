import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import { Sparkles, Gamepad2, Wallet, Trophy, Star, Zap } from "lucide-react";

const LandingPage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const games = [
    {
      name: "Slots",
      image: "https://images.unsplash.com/photo-1566563255308-753861417000?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      color: "from-pink-600 to-purple-600",
    },
    {
      name: "Blackjack",
      image: "https://images.unsplash.com/photo-1642867749315-d1467617a2f4?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      color: "from-emerald-600 to-teal-600",
    },
    {
      name: "Roulette",
      image: "https://images.pexels.com/photos/7594162/pexels-photo-7594162.jpeg?w=600",
      color: "from-red-600 to-orange-600",
    },
    {
      name: "Poker",
      image: "https://images.unsplash.com/photo-1743677042704-74a8390e765a?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      color: "from-cyan-600 to-blue-600",
    },
  ];

  const features = [
    { icon: Gamepad2, title: "4 Premium Games", desc: "Slots, Blackjack, Roulette & Poker" },
    { icon: Wallet, title: "Instant Deposits", desc: "PayID Demo & Real Stripe Payments" },
    { icon: Trophy, title: "Big Wins", desc: "Up to 800x multipliers on wins" },
    { icon: Star, title: "$100 Welcome Bonus", desc: "Free credits on registration" },
  ];

  return (
    <div className="min-h-screen bg-[#050505] overflow-hidden">
      {/* Hero Section */}
      <div className="relative">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/30 via-transparent to-transparent" />
        
        {/* Navigation */}
        <nav className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-heading text-xl font-bold gradient-text">NeonVegas</span>
          </Link>
          
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <Button 
                onClick={() => navigate("/lobby")}
                className="bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 rounded-full px-6"
                data-testid="enter-casino-btn"
              >
                Enter Casino
              </Button>
            ) : (
              <>
                <Button 
                  variant="ghost" 
                  onClick={() => navigate("/login")}
                  className="text-white hover:bg-white/10"
                  data-testid="login-btn"
                >
                  Login
                </Button>
                <Button 
                  onClick={() => navigate("/register")}
                  className="bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 rounded-full px-6"
                  data-testid="register-btn"
                >
                  Join Now
                </Button>
              </>
            )}
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-20 pb-32">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8"
            >
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-gray-300">Licensed & Secure Gaming</span>
            </motion.div>
            
            <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-black mb-6">
              <span className="text-white">Welcome to</span>
              <br />
              <span className="gradient-text">NeonVegas</span>
            </h1>
            
            <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10">
              Experience the thrill of premium casino gaming with instant PayID deposits, 
              real-time action, and massive jackpots waiting to be won.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button
                onClick={() => navigate(isAuthenticated ? "/lobby" : "/register")}
                className="bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 rounded-full px-8 py-6 text-lg font-bold btn-neon animate-pulse-glow"
                data-testid="cta-play-now"
              >
                <Gamepad2 className="w-5 h-5 mr-2" />
                Play Now
              </Button>
              <p className="text-sm text-gray-500">
                Get $100 free bonus on signup!
              </p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Games Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white mb-4">
              Premium Casino Games
            </h2>
            <p className="text-gray-400">Choose your game and start winning</p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {games.map((game, index) => (
              <motion.div
                key={game.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="group relative overflow-hidden rounded-2xl cursor-pointer card-hover"
                onClick={() => navigate(isAuthenticated ? `/games/${game.name.toLowerCase()}` : "/register")}
                data-testid={`game-card-${game.name.toLowerCase()}`}
              >
                <div className="aspect-[4/5] relative">
                  <img
                    src={game.image}
                    alt={game.name}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                  <div className={`absolute inset-0 bg-gradient-to-t ${game.color} opacity-0 group-hover:opacity-40 transition-opacity duration-300`} />
                  
                  <div className="absolute bottom-0 left-0 right-0 p-6">
                    <h3 className="font-heading text-2xl font-bold text-white mb-2">{game.name}</h3>
                    <div className="flex items-center gap-2 text-gray-300 text-sm">
                      <span className="px-2 py-1 rounded bg-white/10">Live</span>
                      <span>•</span>
                      <span>High RTP</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-gradient-to-b from-transparent via-purple-900/10 to-transparent">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="glass rounded-2xl p-6 text-center"
              >
                <div className="w-14 h-14 rounded-full bg-gradient-to-r from-fuchsia-600 to-purple-600 flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-heading text-lg font-bold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass-heavy rounded-3xl p-12 neon-border"
          >
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white mb-4">
              Ready to Win Big?
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              Join thousands of players already winning at NeonVegas. 
              Sign up now and claim your $100 welcome bonus!
            </p>
            <Button
              onClick={() => navigate(isAuthenticated ? "/lobby" : "/register")}
              className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-400 hover:to-orange-400 rounded-full px-8 py-6 text-lg font-bold text-black"
              data-testid="cta-claim-bonus"
            >
              Claim Your Bonus
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading text-sm font-bold text-gray-400">NeonVegas</span>
          </div>
          <p className="text-sm text-gray-500">
            Licensed Casino • 18+ Only • Play Responsibly
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
