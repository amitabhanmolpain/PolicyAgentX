import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import { Clock, MapPin, TrendingUp, X } from "lucide-react";

interface HistoryItem {
  id: number;
  policyType: string;
  region: string;
  date: string;
  inflation: string;
  gdp: string;
  employment: string;
  sentiment: string;
  value: number;
  duration: number;
}

const historyData: HistoryItem[] = [
  { id: 1, policyType: "Tax Reform", region: "North America", date: "2026-03-18", inflation: "-0.6%", gdp: "+1.1%", employment: "+1.1%", sentiment: "72%", value: 50, duration: 12 },
  { id: 2, policyType: "Subsidy Program", region: "Europe", date: "2026-03-17", inflation: "-0.2%", gdp: "+0.8%", employment: "+1.5%", sentiment: "68%", value: 35, duration: 24 },
  { id: 3, policyType: "Trade Policy", region: "Asia Pacific", date: "2026-03-15", inflation: "+0.3%", gdp: "+0.4%", employment: "-0.2%", sentiment: "55%", value: 70, duration: 6 },
  { id: 4, policyType: "Monetary Policy", region: "Middle East", date: "2026-03-12", inflation: "-1.2%", gdp: "+0.9%", employment: "+0.3%", sentiment: "61%", value: 45, duration: 18 },
  { id: 5, policyType: "Environmental Regulation", region: "South America", date: "2026-03-10", inflation: "+0.1%", gdp: "-0.3%", employment: "+0.7%", sentiment: "78%", value: 60, duration: 36 },
];

const HistoryPage = () => {
  const [selected, setSelected] = useState<HistoryItem | null>(null);

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
        {historyData.map((item, i) => (
          <GlowCard
            key={item.id}
            delay={i * 0.08}
            className="cursor-pointer group p-8"
          >
            <div onClick={() => setSelected(item)} className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="flex-1">
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-[10px] font-bold text-accent uppercase tracking-widest mb-3">
                  {item.policyType}
                </div>
                <div className="flex items-center gap-6 mt-1 text-xs text-muted-foreground font-medium">
                  <span className="flex items-center gap-2"><MapPin className="w-4 h-4 opacity-50" />{item.region}</span>
                  <span className="flex items-center gap-2"><Clock className="w-4 h-4 opacity-50" />{item.date}</span>
                </div>
              </div>
              <div className="flex items-center gap-8">
                <div className="text-right">
                   <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1 font-semibold">GDP Impact</p>
                   <p className="text-xl font-display font-bold text-white tracking-tighter">{item.gdp}</p>
                </div>
                <div className="text-right min-w-[100px]">
                   <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1 font-semibold">Sentiment</p>
                   <p className={`text-xl font-display font-bold tracking-tighter ${parseInt(item.sentiment) >= 65 ? "text-emerald-400" : "text-rose-400"}`}>
                     {item.sentiment}
                   </p>
                </div>
              </div>
            </div>
          </GlowCard>
        ))}
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
                  <h2 className="font-display font-bold text-2xl text-white tracking-tight">{selected.policyType}</h2>
                  <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-muted-foreground mt-2">{selected.region} · {selected.date}</p>
                </div>
                <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-white transition-all transform hover:rotate-90 duration-300">
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-6 mb-10">
                <div className="p-6 rounded-2xl bg-[#111113] border border-[#1F1F23]">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-2 font-bold">Policy Value</p>
                  <p className="font-display font-bold text-2xl text-white tracking-tighter">{selected.value}%</p>
                </div>
                <div className="p-6 rounded-2xl bg-[#111113] border border-[#1F1F23]">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-2 font-bold">Duration</p>
                  <p className="font-display font-bold text-2xl text-white tracking-tighter">{selected.duration} mo</p>
                </div>
              </div>

              <div className="space-y-4">
                {[
                  { label: "Inflation Impact", value: selected.inflation },
                  { label: "GDP Impact", value: selected.gdp },
                  { label: "Employment Change", value: selected.employment },
                  { label: "Public Sentiment", value: selected.sentiment },
                ].map((r) => {
                   const isPositive = r.value.startsWith("+") || (r.label === "Public Sentiment" && parseInt(r.value) >= 65);
                   const isNegative = r.value.startsWith("-");
                   return (
                    <div key={r.label} className="flex justify-between items-center py-4 border-b border-[#1F1F23]/50 last:border-0">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">{r.label}</span>
                      <span className={`font-display font-bold text-lg tracking-tighter ${isPositive ? "text-emerald-400" : isNegative ? "text-rose-400" : "text-white"}`}>
                        {r.value}
                      </span>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};

export default HistoryPage;
