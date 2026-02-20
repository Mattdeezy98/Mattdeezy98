import { useState, useEffect } from "react";
import { useAuth, API } from "../App";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import axios from "axios";
import { Shield, Clock, Ban, AlertTriangle, Loader2 } from "lucide-react";

export const ResponsibleGamblingModal = ({ open, onClose }) => {
  const { token, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState("limits");
  const [loading, setLoading] = useState(false);
  const [limits, setLimits] = useState({
    daily_limit: "",
    weekly_limit: "",
    monthly_limit: "",
    session_time_limit: "",
    reality_check_interval: "",
  });
  const [exclusionDuration, setExclusionDuration] = useState("");
  const [exclusionReason, setExclusionReason] = useState("");

  useEffect(() => {
    if (open) {
      fetchLimits();
    }
  }, [open]);

  const fetchLimits = async () => {
    try {
      const response = await axios.get(`${API}/responsible-gambling/limits`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const currentLimits = response.data.limits || {};
      setLimits({
        daily_limit: currentLimits.daily_limit || "",
        weekly_limit: currentLimits.weekly_limit || "",
        monthly_limit: currentLimits.monthly_limit || "",
        session_time_limit: currentLimits.session_time_limit || "",
        reality_check_interval: currentLimits.reality_check_interval || "",
      });
    } catch (error) {
      console.error("Failed to fetch limits:", error);
    }
  };

  const handleSaveLimits = async () => {
    setLoading(true);
    try {
      const payload = {};
      if (limits.daily_limit) payload.daily_limit = parseFloat(limits.daily_limit);
      if (limits.weekly_limit) payload.weekly_limit = parseFloat(limits.weekly_limit);
      if (limits.monthly_limit) payload.monthly_limit = parseFloat(limits.monthly_limit);
      if (limits.session_time_limit) payload.session_time_limit = parseInt(limits.session_time_limit);
      if (limits.reality_check_interval) payload.reality_check_interval = parseInt(limits.reality_check_interval);

      await axios.post(`${API}/responsible-gambling/limits`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Gambling limits updated successfully");
      await refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update limits");
    } finally {
      setLoading(false);
    }
  };

  const handleSelfExclusion = async () => {
    if (!exclusionDuration) {
      toast.error("Please select an exclusion duration");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/responsible-gambling/self-exclusion`, {
        duration: exclusionDuration,
        reason: exclusionReason || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Self-exclusion activated for ${exclusionDuration}`);
      onClose();
      window.location.href = "/";
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to activate self-exclusion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-heading text-xl text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-400" />
            Responsible Gambling
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Set limits to help you play responsibly
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab("limits")}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "limits"
                ? "bg-green-600 text-white"
                : "bg-zinc-800 text-gray-400 hover:bg-zinc-700"
            }`}
            data-testid="limits-tab"
          >
            <Clock className="w-4 h-4 inline mr-2" />
            Set Limits
          </button>
          <button
            onClick={() => setActiveTab("exclusion")}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "exclusion"
                ? "bg-red-600 text-white"
                : "bg-zinc-800 text-gray-400 hover:bg-zinc-700"
            }`}
            data-testid="exclusion-tab"
          >
            <Ban className="w-4 h-4 inline mr-2" />
            Self-Exclusion
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "limits" ? (
            <motion.div
              key="limits"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-400 text-sm">Daily Deposit Limit ($)</Label>
                  <Input
                    type="number"
                    placeholder="No limit"
                    value={limits.daily_limit}
                    onChange={(e) => setLimits({ ...limits, daily_limit: e.target.value })}
                    className="bg-zinc-800 border-white/10 mt-1"
                    data-testid="daily-limit-input"
                  />
                </div>
                <div>
                  <Label className="text-gray-400 text-sm">Weekly Deposit Limit ($)</Label>
                  <Input
                    type="number"
                    placeholder="No limit"
                    value={limits.weekly_limit}
                    onChange={(e) => setLimits({ ...limits, weekly_limit: e.target.value })}
                    className="bg-zinc-800 border-white/10 mt-1"
                    data-testid="weekly-limit-input"
                  />
                </div>
              </div>

              <div>
                <Label className="text-gray-400 text-sm">Monthly Deposit Limit ($)</Label>
                <Input
                  type="number"
                  placeholder="No limit"
                  value={limits.monthly_limit}
                  onChange={(e) => setLimits({ ...limits, monthly_limit: e.target.value })}
                  className="bg-zinc-800 border-white/10 mt-1"
                  data-testid="monthly-limit-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-400 text-sm">Session Time Limit (min)</Label>
                  <Input
                    type="number"
                    placeholder="No limit"
                    value={limits.session_time_limit}
                    onChange={(e) => setLimits({ ...limits, session_time_limit: e.target.value })}
                    className="bg-zinc-800 border-white/10 mt-1"
                    data-testid="session-limit-input"
                  />
                </div>
                <div>
                  <Label className="text-gray-400 text-sm">Reality Check (min)</Label>
                  <Input
                    type="number"
                    placeholder="No reminder"
                    value={limits.reality_check_interval}
                    onChange={(e) => setLimits({ ...limits, reality_check_interval: e.target.value })}
                    className="bg-zinc-800 border-white/10 mt-1"
                    data-testid="reality-check-input"
                  />
                </div>
              </div>

              <Button
                onClick={handleSaveLimits}
                disabled={loading}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 rounded-full"
                data-testid="save-limits-btn"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Save Limits"}
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="exclusion"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />
                  <div>
                    <p className="text-red-400 font-medium">Warning</p>
                    <p className="text-sm text-gray-400">
                      Self-exclusion will immediately lock you out of your account.
                      This cannot be undone until the period expires.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <Label className="text-gray-400 text-sm">Exclusion Duration</Label>
                <Select value={exclusionDuration} onValueChange={setExclusionDuration}>
                  <SelectTrigger className="bg-zinc-800 border-white/10 mt-1" data-testid="exclusion-duration-select">
                    <SelectValue placeholder="Select duration" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-800 border-white/10">
                    <SelectItem value="24h">24 Hours</SelectItem>
                    <SelectItem value="7d">7 Days</SelectItem>
                    <SelectItem value="30d">30 Days</SelectItem>
                    <SelectItem value="6m">6 Months</SelectItem>
                    <SelectItem value="1y">1 Year</SelectItem>
                    <SelectItem value="permanent">Permanent</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-gray-400 text-sm">Reason (Optional)</Label>
                <Input
                  placeholder="Why are you taking a break?"
                  value={exclusionReason}
                  onChange={(e) => setExclusionReason(e.target.value)}
                  className="bg-zinc-800 border-white/10 mt-1"
                  data-testid="exclusion-reason-input"
                />
              </div>

              <Button
                onClick={handleSelfExclusion}
                disabled={loading || !exclusionDuration}
                className="w-full bg-gradient-to-r from-red-600 to-orange-600 rounded-full"
                data-testid="activate-exclusion-btn"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Activate Self-Exclusion"}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
};

export const RealityCheckModal = ({ open, onClose, sessionInfo }) => {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 border-white/10 max-w-sm text-center">
        <DialogHeader>
          <DialogTitle className="font-heading text-xl text-yellow-400">
            ⏰ Reality Check
          </DialogTitle>
        </DialogHeader>
        
        <div className="py-4 space-y-3">
          <p className="text-gray-400">You've been playing for</p>
          <p className="font-heading text-3xl text-white">{sessionInfo?.session_duration || 0} minutes</p>
          
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="bg-zinc-800 rounded-lg p-3">
              <p className="text-gray-400 text-sm">Total Bet</p>
              <p className="text-white font-bold">${sessionInfo?.total_bet?.toFixed(2) || '0.00'}</p>
            </div>
            <div className="bg-zinc-800 rounded-lg p-3">
              <p className="text-gray-400 text-sm">Net Result</p>
              <p className={`font-bold ${(sessionInfo?.net_result || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${sessionInfo?.net_result?.toFixed(2) || '0.00'}
              </p>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2">
          <Button
            onClick={onClose}
            className="w-full bg-gradient-to-r from-fuchsia-600 to-purple-600 rounded-full"
            data-testid="continue-playing-btn"
          >
            Continue Playing
          </Button>
          <Button
            variant="ghost"
            onClick={() => window.location.href = "/lobby"}
            className="w-full text-gray-400"
            data-testid="take-break-btn"
          >
            Take a Break
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ResponsibleGamblingModal;
