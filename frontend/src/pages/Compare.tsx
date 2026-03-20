import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Award } from "lucide-react";

interface PolicyResult {
  name: string;
  inflation: number;
  gdp: number;
  employment: number;
  sentiment: number;
}

const policyA: PolicyResult = { name: "Tax Reform", inflation: -0.6, gdp: 1.1, employment: 1.1, sentiment: 72 };
const policyB: PolicyResult = { name: "Subsidy Program", inflation: -0.2, gdp: 0.8, employment: 1.5, sentiment: 68 };

const AnimatedValue = ({ target, suffix = "" }: { target: number; suffix?: string }) => {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / 40;
    const interval = setInterval(() => {
      start += step;
      if ((step > 0 && start >= target) || (step < 0 && start <= target)) {
        setVal(target);
        clearInterval(interval);
      } else {
        setVal(start);
      }
    }, 30);
    return () => clearInterval(interval);
  }, [target]);
  return <>{val.toFixed(1)}{suffix}</>;
};

const chartData = [
  { metric: "Inflation", A: Math.abs(policyA.inflation), B: Math.abs(policyB.inflation) },
  { metric: "GDP", A: policyA.gdp, B: policyB.gdp },
  { metric: "Employment", A: policyA.employment, B: policyB.employment },
];

const ComparePage = () => {
  const recommended = policyA.gdp + policyA.employment > policyB.gdp + policyB.employment ? "A" : "B";

  const renderPolicyCard = (policy: PolicyResult, label: string, isRecommended: boolean) => (
    <GlowCard hoverable={false} className="relative p-10">
      {isRecommended && (
        <div className="absolute -top-3 left-10 flex items-center gap-2 px-4 py-1.5 rounded-full text-[10px] font-display font-bold uppercase tracking-[0.2em] bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]">
          <Award className="w-3 h-3" /> Recommended
        </div>
      )}
      <h3 className="text-xl font-display font-bold text-foreground mb-8 mt-2 tracking-tight">{label}: {policy.name}</h3>
      <div className="space-y-6 mt-4">
        {[
          { label: "Inflation", value: policy.inflation, suffix: "%" },
          { label: "GDP Growth", value: policy.gdp, suffix: "%" },
          { label: "Employment", value: policy.employment, suffix: "%" },
          { label: "Sentiment", value: policy.sentiment, suffix: "%" },
        ].map((item) => (
          <div key={item.label} className="group">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-[0.15em] font-semibold">{item.label}</span>
              <span className={`font-display font-bold text-xl tracking-tighter ${item.value >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                <AnimatedValue target={item.value} suffix={item.suffix} />
              </span>
            </div>
            <div className="h-1 w-full bg-secondary rounded-full overflow-hidden">
               <motion.div 
                 initial={{ width: 0 }}
                 animate={{ width: `${Math.min(100, Math.abs(item.value) * 10 + 20)}%` }}
                 transition={{ duration: 1.5, ease: "circOut" }}
                 className={`h-full rounded-full ${item.value >= 0 ? "bg-emerald-500/30" : "bg-rose-500/30"}`}
               />
            </div>
          </div>
        ))}
      </div>
    </GlowCard>
  );

  return (
    <div className="container mx-auto px-8 py-20 max-w-6xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-16 text-center"
      >
        <h1 className="text-4xl md:text-5xl font-display font-bold text-gradient mb-4 tracking-tight">
          Policy Comparison
        </h1>
        <p className="text-secondary-foreground font-light tracking-wide max-w-xl mx-auto leading-relaxed">
          Heuristic analysis comparing multiple policy frameworks to identify optimal socio-economic outcomes.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {renderPolicyCard(policyA, "Policy A", recommended === "A")}
        {renderPolicyCard(policyB, "Policy B", recommended === "B")}
      </div>

      <GlowCard hoverable={false} className="p-10">
        <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-10 font-bold">Side-by-Side Impact Metrics</p>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
            <XAxis dataKey="metric" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} tick={{dy: 15}} />
            <YAxis stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} />
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
            <Legend 
              wrapperStyle={{ fontSize: 10, paddingTop: 40, textTransform: 'uppercase', letterSpacing: '0.15em', fontWeight: 600 }} 
              verticalAlign="bottom" 
              align="center" 
              iconType="circle"
              iconSize={8}
            />
            <Bar dataKey="A" name="Policy A" fill="#FFFFFF" radius={[6, 6, 0, 0]} barSize={40} animationDuration={1500} />
            <Bar dataKey="B" name="Policy B" fill="#8B5CF6" radius={[6, 6, 0, 0]} barSize={40} animationDuration={2000} />
          </BarChart>
        </ResponsiveContainer>
      </GlowCard>
    </div>
  );
};

export default ComparePage;
