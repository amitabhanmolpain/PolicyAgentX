import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Activity, BarChart3, Brain, TrendingUp } from "lucide-react";
import GlowCard from "@/components/GlowCard";

const stats = [
  { icon: Activity, label: "Simulations Run", value: "12,847", color: "blue" as const },
  { icon: TrendingUp, label: "Policies Analyzed", value: "3,291", color: "violet" as const },
  { icon: BarChart3, label: "Regions Covered", value: "142", color: "cyan" as const },
  { icon: Brain, label: "AI Accuracy", value: "97.3%", color: "green" as const },
];

const HomePage = () => (
  <div className="relative min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center overflow-hidden bg-background">
    {/* Animated background */}
    <div className="absolute inset-0 -z-10 bg-radial-glow" />
    <div className="absolute inset-0 -z-10 bg-noise opacity-[0.03]" />

    {/* Hero */}
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="text-center px-6 max-w-3xl"
    >
      <h1 className="text-6xl md:text-8xl font-display font-bold text-gradient mb-8 tracking-tighter">
        PolicyAgentX
      </h1>
      <p className="text-xl md:text-2xl text-secondary-foreground mb-12 font-light tracking-wide max-w-2xl mx-auto leading-relaxed">
        Simulate. Analyze. Decide. The next generation of policy intelligence.
      </p>
      <Link to="/simulate-policy">
        <button className="premium-button-primary text-sm tracking-widest uppercase py-4 px-10">
          Run Policy Simulation
        </button>
      </Link>
    </motion.div>

    {/* Floating stats */}
    <div className="mt-28 px-6 w-full max-w-6xl grid grid-cols-2 md:grid-cols-4 gap-6">
      {stats.map((stat, i) => (
        <GlowCard key={stat.label} delay={0.4 + i * 0.15} className="text-center">
          <stat.icon className="w-5 h-5 mx-auto mb-4 text-accent opacity-50" />
          <p className="text-3xl font-display font-bold text-foreground mb-1 tracking-tight">{stat.value}</p>
          <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-medium">{stat.label}</p>
        </GlowCard>
      ))}
    </div>
  </div>
);


export default HomePage;
