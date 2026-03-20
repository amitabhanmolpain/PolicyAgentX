import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const policyTypes = ["Tax Reform", "Subsidy Program", "Trade Policy", "Monetary Policy", "Environmental Regulation"];
const regions = ["North America", "Europe", "Asia Pacific", "Middle East", "Africa", "South America"];

const trendData = [
  { month: "Jan", inflation: 2.1, gdp: 3.2, employment: 95.1 },
  { month: "Feb", inflation: 2.3, gdp: 3.0, employment: 95.3 },
  { month: "Mar", inflation: 2.0, gdp: 3.5, employment: 95.0 },
  { month: "Apr", inflation: 1.8, gdp: 3.8, employment: 95.6 },
  { month: "May", inflation: 1.6, gdp: 4.1, employment: 96.0 },
  { month: "Jun", inflation: 1.5, gdp: 4.3, employment: 96.2 },
];

const comparisonData = [
  { name: "Inflation", value: -0.6 },
  { name: "GDP", value: 1.1 },
  { name: "Employment", value: 1.1 },
  { name: "Sentiment", value: 0.8 },
];

interface ResultItem {
  label: string;
  value: string;
  change: string;
  positive: boolean;
}

const SimulatePolicyPage = () => {
  const [policyType, setPolicyType] = useState(policyTypes[0]);
  const [value, setValue] = useState(50);
  const [region, setRegion] = useState(regions[0]);
  const [duration, setDuration] = useState(12);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const results: ResultItem[] = [
    { label: "Inflation Impact", value: "-0.6%", change: "Decreased", positive: true },
    { label: "GDP Impact", value: "+1.1%", change: "Growth", positive: true },
    { label: "Employment Change", value: "+1.1%", change: "Improvement", positive: true },
    { label: "Public Sentiment", value: "72%", change: "Favorable", positive: true },
  ];

  const handleSimulate = () => {
    setLoading(true);
    setShowResults(false);
    setTimeout(() => {
      setLoading(false);
      setShowResults(true);
    }, 2000);
  };

  const labelClass = "text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-3 block";

  return (
    <div className="container mx-auto px-8 py-20 max-w-6xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-16 text-center"
      >
        <h1 className="text-4xl md:text-5xl font-display font-bold text-gradient mb-4 tracking-tight">
          Policy Simulation
        </h1>
        <p className="text-secondary-foreground font-light tracking-wide max-w-xl mx-auto leading-relaxed">
          Configure parameters to simulate complex socio-economic impacts across diverse regions.
        </p>
      </motion.div>

      {/* Form */}
      <GlowCard hoverable={false} className="max-w-4xl mx-auto mb-24 p-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div>
            <label className={labelClass}>Policy Type</label>
            <select value={policyType} onChange={(e) => setPolicyType(e.target.value)} className="premium-input w-full appearance-none">
              {policyTypes.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Region</label>
            <select value={region} onChange={(e) => setRegion(e.target.value)} className="premium-input w-full appearance-none">
              {regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Policy Value: <span className="text-white ml-2">{value}%</span></label>
            <input
              type="range"
              min={0}
              max={100}
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
              className="w-full accent-white h-1.5 bg-secondary rounded-lg cursor-pointer"
            />
          </div>
          <div>
            <label className={labelClass}>Duration (months)</label>
            <input
              type="number"
              min={1}
              max={120}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="premium-input w-full"
            />
          </div>
        </div>

        <button
          onClick={handleSimulate}
          disabled={loading}
          className="mt-12 w-full premium-button-primary disabled:opacity-50 tracking-[0.2em] py-4 text-xs font-bold uppercase transition-all"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-3">
              <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              Processing...
            </span>
          ) : (
            "Run Simulation"
          )}
        </button>
      </GlowCard>

      {/* Results */}
      <AnimatePresence>
        {showResults && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            transition={{ duration: 0.8, ease: "circOut" }}
          >
            <div className="flex items-center gap-4 mb-12 overflow-hidden">
               <div className="h-px bg-border flex-1" />
               <h2 className="text-xs font-display font-medium text-muted-foreground uppercase tracking-[0.3em]">Simulation Results</h2>
               <div className="h-px bg-border flex-1" />
            </div>

            {/* Result cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
              {results.map((r, i) => (
                <GlowCard
                  key={r.label}
                  delay={i * 0.1}
                  className="text-center p-8"
                >
                  <p className="text-[10px] text-muted-foreground uppercase tracking-[0.15em] mb-4 font-semibold">{r.label}</p>
                  <p className={`text-4xl font-display font-bold tracking-tighter mb-2 ${r.positive ? "text-emerald-400" : "text-rose-400"}`}>
                    {r.value}
                  </p>
                  <div className={`text-[10px] uppercase font-bold tracking-widest ${r.positive ? "text-emerald-500/80" : "text-rose-500/80"}`}>
                    {r.change}
                  </div>
                </GlowCard>
              ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <GlowCard hoverable={false} className="p-8">
                <div className="flex items-center justify-between mb-8">
                  <p className={labelClass + " mb-0"}>Trend Analysis</p>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-white"/><span className="text-[10px] text-muted-foreground uppercase">GDP</span></div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#8B5CF6]"/><span className="text-[10px] text-muted-foreground uppercase">INF</span></div>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                    <XAxis dataKey="month" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} tick={{dy: 10}} />
                    <YAxis stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} tick={{dx: -10}} />
                    <Tooltip
                      contentStyle={{
                        background: "#151517",
                        border: "1px solid #1F1F23",
                        borderRadius: "16px",
                        boxShadow: "0 20px 40px -10px rgba(0,0,0,0.5)",
                        color: "#FFFFFF",
                        fontSize: 11,
                        padding: "12px 16px",
                        fontWeight: 500,
                      }}
                      itemStyle={{ padding: "2px 0" }}
                      cursor={{ stroke: '#1F1F23', strokeWidth: 2 }}
                    />
                    <Line type="monotone" dataKey="gdp" stroke="#FFFFFF" strokeWidth={2.5} dot={false} animationDuration={2000} />
                    <Line type="monotone" dataKey="inflation" stroke="#8B5CF6" strokeWidth={2.5} dot={false} animationDuration={2500} />
                    <Line type="monotone" dataKey="employment" stroke="#6366F1" strokeWidth={2.5} dot={false} animationDuration={3000} />
                  </LineChart>
                </ResponsiveContainer>
              </GlowCard>

              <GlowCard hoverable={false} className="p-8">
                <p className={labelClass}>Impact Comparison</p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                    <XAxis dataKey="name" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} tick={{dy: 10}} />
                    <YAxis stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} tick={{dx: -10}} />
                    <Tooltip
                      contentStyle={{
                        background: "#151517",
                        border: "1px solid #1F1F23",
                        borderRadius: "16px",
                        boxShadow: "0 20px 40px -10px rgba(0,0,0,0.5)",
                        color: "#FFFFFF",
                        fontSize: 11,
                        padding: "12px 16px",
                        fontWeight: 500,
                      }}
                      cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                    />
                    <Bar dataKey="value" fill="#FFFFFF" radius={[6, 6, 0, 0]} barSize={40} animationDuration={1500} />
                  </BarChart>
                </ResponsiveContainer>
              </GlowCard>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SimulatePolicyPage;
