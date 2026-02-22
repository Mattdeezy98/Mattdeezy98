import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, API } from "../App";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import { toast } from "sonner";
import axios from "axios";
import { 
  ArrowLeft, Trophy, Users, Clock, DollarSign, Wallet,
  Medal, Loader2, Gamepad2
} from "lucide-react";

const TournamentsPage = () => {
  const { user, token, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(null);
  const [selectedTournament, setSelectedTournament] = useState(null);

  useEffect(() => {
    fetchTournaments();
  }, []);

  const fetchTournaments = async () => {
    try {
      const response = await axios.get(`${API}/tournaments`);
      setTournaments(response.data.tournaments || []);
    } catch (error) {
      toast.error("Failed to load tournaments");
    } finally {
      setLoading(false);
    }
  };

  const fetchTournamentDetails = async (id) => {
    try {
      const response = await axios.get(`${API}/tournaments/${id}`);
      setSelectedTournament(response.data);
    } catch (error) {
      toast.error("Failed to load tournament details");
    }
  };

  const joinTournament = async (tournamentId) => {
    setJoining(tournamentId);
    try {
      const response = await axios.post(`${API}/tournaments/${tournamentId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        toast.success(response.data.message);
        await refreshUser();
        fetchTournaments();
      } else {
        toast.error(response.data.error);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to join tournament");
    } finally {
      setJoining(null);
    }
  };

  const formatTimeRemaining = (endTime) => {
    const end = new Date(endTime);
    const now = new Date();
    const diff = end - now;
    
    if (diff <= 0) return "Ended";
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    return `${hours}h ${minutes}m`;
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
            <Trophy className="w-5 h-5 text-yellow-400" />
            <span className="font-heading text-lg font-bold">Tournaments</span>
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
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="font-heading text-3xl font-bold text-white mb-2">
            <span className="gradient-text">Compete & Win</span>
          </h1>
          <p className="text-gray-400">Join tournaments and compete for massive prize pools!</p>
        </motion.div>

        {/* Tournament List */}
        {tournaments.length === 0 ? (
          <div className="text-center py-12">
            <Trophy className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">No active tournaments right now</p>
            <p className="text-gray-500 text-sm">Check back soon for exciting competitions!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {tournaments.map((tournament, index) => (
              <motion.div
                key={tournament.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="glass rounded-xl overflow-hidden"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-heading text-xl font-bold text-white">{tournament.name}</h3>
                      <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
                        <span className="flex items-center gap-1">
                          <Gamepad2 className="w-4 h-4" />
                          {tournament.game}
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {tournament.participants?.length || 0}/{tournament.max_players}
                        </span>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      tournament.status === 'active' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {tournament.status === 'active' ? 'Live Now' : 'Upcoming'}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="bg-zinc-900/50 rounded-lg p-3 text-center">
                      <DollarSign className="w-5 h-5 text-green-400 mx-auto mb-1" />
                      <p className="text-white font-bold">${tournament.prize_pool?.toFixed(0)}</p>
                      <p className="text-gray-500 text-xs">Prize Pool</p>
                    </div>
                    <div className="bg-zinc-900/50 rounded-lg p-3 text-center">
                      <DollarSign className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                      <p className="text-white font-bold">${tournament.entry_fee}</p>
                      <p className="text-gray-500 text-xs">Entry Fee</p>
                    </div>
                    <div className="bg-zinc-900/50 rounded-lg p-3 text-center">
                      <Clock className="w-5 h-5 text-cyan-400 mx-auto mb-1" />
                      <p className="text-white font-bold">{formatTimeRemaining(tournament.end_time)}</p>
                      <p className="text-gray-500 text-xs">Time Left</p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Button
                      onClick={() => joinTournament(tournament.id)}
                      disabled={joining === tournament.id || tournament.participants?.includes(user?.id)}
                      className="flex-1 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full"
                    >
                      {joining === tournament.id ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : tournament.participants?.includes(user?.id) ? (
                        "Joined"
                      ) : (
                        `Join for $${tournament.entry_fee}`
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => fetchTournamentDetails(tournament.id)}
                      className="border-white/20 hover:bg-white/10"
                    >
                      Leaderboard
                    </Button>
                  </div>
                </div>

                {/* Leaderboard Preview */}
                {selectedTournament?.id === tournament.id && selectedTournament.leaderboard && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: "auto" }}
                    className="border-t border-white/10 bg-zinc-900/30"
                  >
                    <div className="p-4">
                      <h4 className="font-bold text-white mb-3 flex items-center gap-2">
                        <Medal className="w-4 h-4 text-yellow-400" />
                        Top Players
                      </h4>
                      {selectedTournament.leaderboard.length === 0 ? (
                        <p className="text-gray-500 text-sm">No players yet - be the first!</p>
                      ) : (
                        <div className="space-y-2">
                          {selectedTournament.leaderboard.slice(0, 5).map((entry, i) => (
                            <div key={entry.user_id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                              <div className="flex items-center gap-3">
                                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                                  i === 0 ? 'bg-yellow-500 text-black' :
                                  i === 1 ? 'bg-gray-400 text-black' :
                                  i === 2 ? 'bg-amber-700 text-white' :
                                  'bg-zinc-700 text-white'
                                }`}>
                                  {i + 1}
                                </span>
                                <span className="text-white">{entry.username}</span>
                              </div>
                              <div className="text-right">
                                <p className="text-yellow-400 font-bold">{entry.score?.toFixed(2)} pts</p>
                                <p className="text-gray-500 text-xs">{entry.spins} spins</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </div>
        )}

        {/* Prize Distribution Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 glass rounded-xl p-5"
        >
          <h3 className="font-heading font-bold text-white mb-4">Prize Distribution</h3>
          <div className="grid grid-cols-4 gap-3 text-center">
            {[
              { place: "1st", prize: "50%", color: "text-yellow-400" },
              { place: "2nd", prize: "25%", color: "text-gray-300" },
              { place: "3rd", prize: "15%", color: "text-amber-600" },
              { place: "4th", prize: "10%", color: "text-gray-400" },
            ].map((item) => (
              <div key={item.place} className="bg-zinc-900/50 rounded-lg p-3">
                <p className={`font-heading text-xl font-bold ${item.color}`}>{item.place}</p>
                <p className="text-white font-bold">{item.prize}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TournamentsPage;
