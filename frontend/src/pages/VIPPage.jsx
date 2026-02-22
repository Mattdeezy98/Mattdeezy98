import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, API } from "../App";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import { toast } from "sonner";
import axios from "axios";
import { 
  ArrowLeft, Crown, Gift, TrendingUp, Star, Zap, Wallet,
  CheckCircle2, Lock, Sparkles, Loader2
} from "lucide-react";

const VIPPage = () => {
  const { user, token, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [vipStatus, setVipStatus] = useState(null);
  const [allTiers, setAllTiers] = useState({});
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);

  useEffect(() => {
    fetchVIPData();
  }, []);

  const fetchVIPData = async () => {
    try {
      const [statusRes, tiersRes] = await Promise.all([
        axios.get(`${API}/vip/status`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${API}/vip/tiers`)
      ]);
      setVipStatus(statusRes.data);
      setAllTiers(tiersRes.data.tiers);
    } catch (error) {
      toast.error("Failed to load VIP data");
    } finally {
      setLoading(false);
    }
  };

  const claimDailyBonus = async () => {
    setClaiming(true);
    try {
      const response = await axios.post(`${API}/vip/claim-daily`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        toast.success(`Claimed $${response.data.bonus} daily bonus!`);
        await refreshUser();
      } else {
        toast.info(response.data.message);
      }
    } catch (error) {
      toast.error("Failed to claim bonus");
    } finally {
      setClaiming(false);
    }
  };

  const claimCashback = async () => {
    setClaiming(true);
    try {
      const response = await axios.post(`${API}/vip/claim-cashback`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.cashback > 0) {
        toast.success(`Received $${response.data.cashback.toFixed(2)} cashback!`);
        await refreshUser();
      } else {
        toast.info("No cashback available - keep playing!");
      }
    } catch (error) {
      toast.error("Failed to claim cashback");
    } finally {
      setClaiming(false);
    }
  };

  const getTierIcon = (tier) => {
    const icons = {
      bronze: "🥉",
      silver: "🥈",
      gold: "🥇",
      platinum: "💎",
      diamond: "👑"
    };
    return icons[tier] || "⭐";
  };

  const getTierColor = (tier) => {
    const colors = {
      bronze: "from-amber-700 to-amber-900",
      silver: "from-gray-400 to-gray-600",
      gold: "from-yellow-500 to-yellow-700",
      platinum: "from-cyan-400 to-cyan-600",
      diamond: "from-purple-500 to-pink-500"
    };
    return colors[tier] || "from-gray-600 to-gray-800";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  const currentTier = vipStatus?.tier || "bronze";
  const progress = vipStatus?.next_tier_requirement 
    ? (vipStatus.total_wagered / vipStatus.next_tier_requirement) * 100 
    : 100;

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <nav className="sticky top-0 z-50 glass-heavy border-b border-white/10">
        <div className="max-w-4xl mx-auto flex items-center justify-between px-4 py-3">
          <Button 
            variant="ghost" 
            onClick={() => navigate("/lobby")}
            className="text-gray-400 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
          <div className="flex items-center gap-2">
            <Crown className="w-5 h-5 text-yellow-400" />
            <span className="font-heading text-lg font-bold">VIP Club</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-yellow-500/50 text-yellow-400"
            onClick={() => navigate("/wallet")}
          >
            <Wallet className="w-4 h-4 mr-2" />
            ${user?.balance?.toFixed(2)}
          </Button>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Current Status Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-2xl p-6 mb-8 bg-gradient-to-r ${getTierColor(currentTier)} relative overflow-hidden`}
        >
          <div className="absolute top-0 right-0 text-[120px] opacity-20 -mr-6 -mt-6">
            {getTierIcon(currentTier)}
          </div>
          
          <div className="relative">
            <div className="flex items-center gap-4 mb-4">
              <div className="text-5xl">{getTierIcon(currentTier)}</div>
              <div>
                <p className="text-white/70 text-sm">Your VIP Status</p>
                <h2 className="font-heading text-3xl font-bold text-white uppercase">{currentTier}</h2>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-white/70 text-xs">Cashback</p>
                <p className="text-white font-bold text-lg">{(vipStatus?.cashback_rate * 100).toFixed(0)}%</p>
              </div>
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-white/70 text-xs">Bonus Multiplier</p>
                <p className="text-white font-bold text-lg">{vipStatus?.bonus_multiplier}x</p>
              </div>
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-white/70 text-xs">Daily Bonus</p>
                <p className="text-white font-bold text-lg">${vipStatus?.daily_bonus}</p>
              </div>
            </div>

            {vipStatus?.next_tier && (
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white/70">Progress to {vipStatus.next_tier.toUpperCase()}</span>
                  <span className="text-white">${vipStatus.total_wagered?.toFixed(0)} / ${vipStatus.next_tier_requirement}</span>
                </div>
                <Progress value={progress} className="h-2 bg-black/30" />
              </div>
            )}
          </div>
        </motion.div>

        {/* Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-xl p-5"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center">
                <Gift className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-heading font-bold text-white">Daily Bonus</h3>
                <p className="text-gray-400 text-sm">${vipStatus?.daily_bonus} every day</p>
              </div>
            </div>
            <Button
              onClick={claimDailyBonus}
              disabled={claiming}
              className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full"
            >
              {claiming ? <Loader2 className="w-5 h-5 animate-spin" /> : "Claim Daily Bonus"}
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-xl p-5"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-heading font-bold text-white">Weekly Cashback</h3>
                <p className="text-gray-400 text-sm">{(vipStatus?.cashback_rate * 100).toFixed(0)}% of losses</p>
              </div>
            </div>
            <Button
              onClick={claimCashback}
              disabled={claiming}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
            >
              {claiming ? <Loader2 className="w-5 h-5 animate-spin" /> : "Claim Cashback"}
            </Button>
          </motion.div>
        </div>

        {/* All Tiers */}
        <h3 className="font-heading text-xl font-bold text-white mb-4">VIP Tiers</h3>
        <div className="space-y-3">
          {Object.entries(allTiers).map(([tier, config], index) => {
            const isCurrentTier = tier === currentTier;
            const isUnlocked = vipStatus?.total_wagered >= config.min_wagered;
            
            return (
              <motion.div
                key={tier}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`glass rounded-xl p-4 ${isCurrentTier ? 'ring-2 ring-yellow-400' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{getTierIcon(tier)}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-heading font-bold text-white uppercase">{tier}</h4>
                        {isCurrentTier && (
                          <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded-full">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm">
                        Wager ${config.min_wagered.toLocaleString()}+
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-center">
                      <p className="text-gray-400">Cashback</p>
                      <p className="text-white font-bold">{(config.cashback * 100).toFixed(0)}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-400">Daily</p>
                      <p className="text-white font-bold">${config.daily_bonus}</p>
                    </div>
                    {isUnlocked ? (
                      <CheckCircle2 className="w-6 h-6 text-green-400" />
                    ) : (
                      <Lock className="w-6 h-6 text-gray-500" />
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default VIPPage;
