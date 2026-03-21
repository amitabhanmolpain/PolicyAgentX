import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import ChatMessageList from "@/components/ChatMessageList";
import ChatInput from "@/components/ChatInput";
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

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const SimulatePolicyPage = () => {
  const [policyType, setPolicyType] = useState(policyTypes[0]);
  const [value, setValue] = useState(50);
  const [region, setRegion] = useState(regions[0]);
  const [duration, setDuration] = useState(12);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-ai",
      role: "assistant",
      content: "Hello! I am your Policy Simulation Assistant. Specify a policy, region, and duration, and I'll analyze the socio-economic impacts for you."
    }
  ]);

  const resultsRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages or results change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, loading, showResults]);

  const results: ResultItem[] = [
    { label: "Inflation Impact", value: "-0.6%", change: "Decreased", positive: true },
    { label: "GDP Impact", value: "+1.1%", change: "Growth", positive: true },
    { label: "Employment Change", value: "+1.1%", change: "Improvement", positive: true },
    { label: "Public Sentiment", value: "72%", change: "Favorable", positive: true },
  ];

  const handleSendMessage = (content: string) => {
    // Add user message
    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    setMessages(prev => [...prev, userMsg]);
    setShowResults(false);
    setLoading(true);

    // Parse input (existing logic)
    const lower = content.toLowerCase();
    let extractedType = policyType;
    if (lower.includes("tax")) extractedType = "Tax Reform";
    else if (lower.includes("subsidy")) extractedType = "Subsidy Program";
    else if (lower.includes("trade")) extractedType = "Trade Policy";
    else if (lower.includes("monetary")) extractedType = "Monetary Policy";
    else if (lower.includes("environ")) extractedType = "Environmental Regulation";

    let extractedRegion = region;
    if (lower.includes("india") || lower.includes("karnataka") || lower.includes("asia")) extractedRegion = "Asia Pacific";
    else if (lower.includes("america") || lower.includes("usa")) extractedRegion = "North America";
    else if (lower.includes("europe") || lower.includes("uk")) extractedRegion = "Europe";
    else if (lower.includes("africa")) extractedRegion = "Africa";
    else if (lower.includes("middle east")) extractedRegion = "Middle East";
    else if (lower.includes("south america")) extractedRegion = "South America";

    let extractedValue = value;
    const valMatch = lower.match(/(\d+)%/);
    if (valMatch) extractedValue = parseInt(valMatch[1]);

    let extractedDuration = duration;
    const durMatch = lower.match(/(\d+)\s+month/);
    if (durMatch) extractedDuration = parseInt(durMatch[1]);

    setPolicyType(extractedType);
    setValue(extractedValue);
    setRegion(extractedRegion);
    setDuration(extractedDuration);

    setTimeout(() => {
      setLoading(false);
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Analyzing ${extractedType} policy for ${extractedRegion} with a ${extractedValue}% change over ${extractedDuration} months. Here are the simulated impacts based on our current economic models:`
      };
      setMessages(prev => [...prev, aiMsg]);
      
      setTimeout(() => {
        setShowResults(true);
      }, 500);
    }, 2000);
  };

  const labelClass = "text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-3 block";

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] w-full overflow-hidden bg-background relative">
      {/* Dynamic Header */}
      <div className="flex-none pt-8 pb-4 text-center border-b border-border/10 bg-background/50 backdrop-blur-md z-40">
        <h1 className="text-2xl md:text-3xl font-display font-bold text-gradient tracking-tight">
          Policy Agent X
        </h1>
        <p className="text-muted-foreground text-[10px] font-bold uppercase tracking-[0.2em] mt-1 opacity-60">
          Intelligent Research Assistant
        </p>
      </div>

      {/* Main Scroller Area */}
      <div 
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-4 md:px-0 scroll-smooth"
      >
        <div className="max-w-4xl mx-auto w-full py-8 md:py-12 flex flex-col gap-10 pb-[280px]">
          <ChatMessageList messages={messages} loading={loading} />

          <AnimatePresence>
            {showResults && (
              <motion.div
                ref={resultsRef}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 30 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="space-y-12 pt-12 border-t border-border/20"
              >
                <div className="flex items-center gap-4 px-4 overflow-hidden">
                   <div className="h-px bg-border/40 flex-1" />
                   <h2 className="text-[10px] font-display font-medium text-muted-foreground uppercase tracking-[0.4em]">Simulation Intelligence Model</h2>
                   <div className="h-px bg-border/40 flex-1" />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-2 md:px-0">
                  {results.map((r, i) => (
                    <GlowCard
                      key={r.label}
                      delay={i * 0.05}
                      className="text-center p-6 bg-secondary/20 border-border/30 backdrop-blur-sm"
                    >
                      <p className="text-[9px] text-muted-foreground uppercase tracking-[0.1em] mb-3 font-bold opacity-70">{r.label}</p>
                      <p className={`text-4xl font-display font-bold tracking-tighter mb-1 ${r.positive ? "text-emerald-400" : "text-rose-400"}`}>
                        {r.value}
                      </p>
                      <div className={`text-[10px] uppercase font-bold tracking-widest ${r.positive ? "text-emerald-500/60" : "text-rose-500/60"}`}>
                        {r.change}
                      </div>
                    </GlowCard>
                  ))}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 px-2 md:px-0 pb-16">
                  <GlowCard hoverable={false} className="p-8 bg-secondary/10 border-border/20">
                    <div className="flex items-center justify-between mb-8">
                      <p className={labelClass + " mb-0"}>Trend Analysis</p>
                      <div className="flex gap-4">
                        <div className="flex items-center gap-1.5 font-bold"><div className="w-1.5 h-1.5 rounded-full bg-white"/><span className="text-[9px] text-muted-foreground uppercase">GDP</span></div>
                        <div className="flex items-center gap-1.5 font-bold"><div className="w-1.5 h-1.5 rounded-full bg-accent"/><span className="text-[9px] text-muted-foreground uppercase">INF</span></div>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={trendData}>
                        <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                        <XAxis dataKey="month" stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dy: 10}} />
                        <YAxis stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dx: -10}} />
                        <Tooltip contentStyle={{ background: "#0B0B0C", border: "1px solid #1F1F23", borderRadius: "12px", fontSize: 10 }} />
                        <Line type="monotone" dataKey="gdp" stroke="#FFFFFF" strokeWidth={2.5} dot={false} />
                        <Line type="monotone" dataKey="inflation" stroke="#6366F1" strokeWidth={2.5} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </GlowCard>

                  <GlowCard hoverable={false} className="p-8 bg-secondary/10 border-border/20">
                    <p className={labelClass}>Impact Comparison</p>
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={comparisonData}>
                        <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dy: 10}} />
                        <YAxis stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dx: -10}} />
                        <Tooltip contentStyle={{ background: "#0B0B0C", border: "1px solid #1F1F23", borderRadius: "12px", fontSize: 10 }} />
                        <Bar dataKey="value" fill="#FFFFFF" radius={[4, 4, 0, 0]} barSize={40} />
                      </BarChart>
                    </ResponsiveContainer>
                  </GlowCard>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Input Overlay */}
      <div className="fixed bottom-0 left-0 right-0 z-[100] pointer-events-none">
        <div className="max-w-4xl mx-auto w-full px-4 md:px-0 pb-8 pointer-events-auto bg-gradient-to-t from-background via-background to-transparent pt-24">
          <ChatInput onSendMessage={handleSendMessage} isLoading={loading} />
        </div>
      </div>
    </div>
  );
};

export default SimulatePolicyPage;
