import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import { Clock, MapPin, TrendingUp, X } from "lucide-react";
import { getHistory, SimulationResult } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface HistoryItem {
  id?: number;
  text?: string;
  region?: string;
  date?: string;
  economic_impact?: string;
  social_impact?: string;
  business_impact?: string;
  government_impact?: string;
  protest_risk?: string;
  risk_confidence?: string;
  explanation?: string;
  recommendation?: string;
}

const HistoryPage = () => {
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<HistoryItem | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getHistory();
        setHistoryData(data);
      } catch (error) {
        console.error("Failed to fetch history:", error);
        const errorMessage = error instanceof Error ? error.message : "Failed to load history";
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage,
        });
        setHistoryData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [toast]);

  return (
    <div className="container mx-auto px-8 py-20 max-w-5xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-16 text-center"
      >
        <h1 className="text-4xl md:text-5xl font-display font-bold text-gradient mb-4 tracking-tight">
          Simulation History
        </h1>
        <p className="text-secondary-foreground font-light tracking-wide max-w-xl mx-auto leading-relaxed">
          Chronological record of past policy simulations and their analyzed impacts.
        </p>
      </motion.div>

      <div className="space-y-6">
        {loading ? (
          <p className="text-center text-muted-foreground">Loading history...</p>
        ) : historyData.length === 0 ? (
          <p className="text-center text-muted-foreground">No simulations yet. Run a simulation to see it here.</p>
        ) : (
          historyData.map((item, i) => (
            <GlowCard
              key={i}
              delay={i * 0.08}
              className="cursor-pointer group p-8"
            >
              <div onClick={() => setSelected(item)} className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div className="flex-1">
                  <div className="inline-flex items-center px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-[10px] font-bold text-accent uppercase tracking-widest mb-3">
                    Policy Simulation
                  </div>
                  <div className="flex items-center gap-6 mt-1 text-xs text-muted-foreground font-medium">
                    {item.region && <span className="flex items-center gap-2"><MapPin className="w-4 h-4 opacity-50" />{item.region}</span>}
                    {item.date && <span className="flex items-center gap-2"><Clock className="w-4 h-4 opacity-50" />{item.date}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-8">
                  <div className="text-right">
                     <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1 font-semibold">Economic Impact</p>
                     <p className="text-lg font-display font-bold text-white tracking-tighter truncate max-w-xs">{item.economic_impact || "N/A"}</p>
                  </div>
                </div>
              </div>
            </GlowCard>
          ))
        )}
      </div>

      {/* Modal */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-xl p-6"
            onClick={() => setSelected(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-[#151517] border border-[#1F1F23] rounded-2xl p-10 max-w-xl w-full shadow-[0_0_50px_rgba(0,0,0,0.5)] relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent/0 via-accent/50 to-accent/0 opacity-30" />
              
              <div className="flex justify-between items-start mb-10">
                <div>
                  <h2 className="font-display font-bold text-2xl text-white tracking-tight">Policy Simulation</h2>
                  <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-muted-foreground mt-2">{selected.region || "N/A"} · {selected.date || "N/A"}</p>
                </div>
                <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-white transition-all transform hover:rotate-90 duration-300">
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                {[
                  { label: "Economic Impact", value: selected.economic_impact },
                  { label: "Social Impact", value: selected.social_impact },
                  { label: "Business Impact", value: selected.business_impact },
                  { label: "Government Impact", value: selected.government_impact },
                  { label: "Protest Risk", value: selected.protest_risk },
                  { label: "Risk Confidence", value: selected.risk_confidence },
                ].map((r) => (
                  r.value && <div key={r.label} className="flex justify-between items-start py-4 border-b border-[#1F1F23]/50 last:border-0">
                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">{r.label}</span>
                    <span className="font-display font-bold text-sm tracking-tighter text-emerald-400 text-right max-w-[50%]">
                      {r.value}
                    </span>
                  </div>
                ))}
              </div>

              {selected.explanation && (
                <div className="mt-6 pt-6 border-t border-[#1F1F23]/50">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-3">Explanation</p>
                  <p className="text-sm text-muted-foreground leading-relaxed">{selected.explanation}</p>
                </div>
              )}

              {selected.recommendation && (
                <div className="mt-4">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-3">Recommendation</p>
                  <p className="text-sm text-muted-foreground leading-relaxed">{selected.recommendation}</p>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};

export default HistoryPage;
