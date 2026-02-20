import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { toast } from "sonner";
import { Zap, Mail, Lock, User, ArrowRight, Loader2, Gift } from "lucide-react";

const RegisterPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password || !username) {
      toast.error("Please fill in all fields");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    if (username.length < 3) {
      toast.error("Username must be at least 3 characters");
      return;
    }

    setLoading(true);
    try {
      await register(email, password, username);
      toast.success("Welcome to NeonVegas! You received $100 bonus!");
      navigate("/lobby");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex">
      {/* Left side - Visual */}
      <div className="hidden lg:flex w-1/2 relative bg-gradient-to-bl from-cyan-900/50 via-[#050505] to-purple-900/30 items-center justify-center p-12">
        <div className="absolute inset-0 bg-[url('https://images.pexels.com/photos/3279695/pexels-photo-3279695.jpeg')] bg-cover bg-center opacity-20" />
        <div className="relative text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="w-20 h-20 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center mx-auto mb-6">
              <Gift className="w-10 h-10 text-black" />
            </div>
            <h2 className="font-heading text-4xl font-bold text-white mb-4">
              $100 Welcome<br />Bonus
            </h2>
            <p className="text-gray-400 max-w-sm mx-auto">
              Start playing instantly with free credits. No deposit required!
            </p>
          </motion.div>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-full max-w-md"
        >
          <Link to="/" className="flex items-center gap-2 mb-10">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-heading text-xl font-bold gradient-text">NeonVegas</span>
          </Link>

          <h1 className="font-heading text-3xl font-bold text-white mb-2">Create Account</h1>
          <p className="text-gray-400 mb-8">Join the action and start winning today</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-300">Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  id="username"
                  type="text"
                  placeholder="LuckyPlayer"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-10 bg-zinc-900/80 border-white/10 focus:border-purple-500 h-12 rounded-lg"
                  data-testid="register-username-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-300">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 bg-zinc-900/80 border-white/10 focus:border-purple-500 h-12 rounded-lg"
                  data-testid="register-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 bg-zinc-900/80 border-white/10 focus:border-purple-500 h-12 rounded-lg"
                  data-testid="register-password-input"
                />
              </div>
              <p className="text-xs text-gray-500">Minimum 6 characters</p>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 rounded-full h-12 font-bold"
              data-testid="register-submit-btn"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  Create Account & Get $100
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </form>

          <p className="text-center text-gray-400 mt-8">
            Already have an account?{" "}
            <Link to="/login" className="text-fuchsia-400 hover:text-fuchsia-300 font-medium" data-testid="go-to-login">
              Sign in
            </Link>
          </p>

          <p className="text-center text-xs text-gray-500 mt-6">
            By signing up, you confirm you are 18+ and agree to play responsibly.
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default RegisterPage;
