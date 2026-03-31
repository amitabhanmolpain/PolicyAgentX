import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import ChatMessageList from "@/components/ChatMessageList";
import ChatInput from "@/components/ChatInput";
import { simulatePolicy, SimulationResult } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";
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
  const [showIndiaWarning, setShowIndiaWarning] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  const resultsRef = useRef<HTMLDivElement>(null);
  const [apiResults, setApiResults] = useState<SimulationResult | null>(null);
  const { toast } = useToast();

  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem("policySimulationChat");
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch {
        // If parsing fails, use default message
        setMessages([
          {
            id: "initial-ai",
            role: "assistant",
            content: "Hello! I am your Policy Simulation Assistant. Specify a policy, region, and duration, and I'll analyze the socio-economic impacts for you."
          }
        ]);
      }
    } else {
      setMessages([
        {
          id: "initial-ai",
          role: "assistant",
          content: "Hello! I am your Policy Simulation Assistant. Specify a policy, region, and duration, and I'll analyze the socio-economic impacts for you."
        }
      ]);
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("policySimulationChat", JSON.stringify(messages));
  }, [messages]);

  const handleNewChat = () => {
    localStorage.removeItem("policySimulationChat");
    setMessages([
      {
        id: "initial-ai",
        role: "assistant",
        content: "Hello! I am your Policy Simulation Assistant. Specify a policy, region, and duration, and I'll analyze the socio-economic impacts for you."
      }
    ]);
    setShowResults(false);
    setApiResults(null);
  };

  const handleSendMessage = async (content: string) => {
    setShowResults(false);
    setLoading(true);

    // Add user message
    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    setMessages(prev => [...prev, userMsg]);

    // Add thinking indicator
    const thinkingMsg: Message = {
      id: `thinking-${Date.now()}`,
      role: "assistant",
      content: "🔄 Analyzing policy with AI agents..."
    };
    setMessages(prev => [...prev, thinkingMsg]);

    // Check if policy is for India
    const indiaKeywords = [
      "india", "indian", "delhi", "mumbai", "bangalore", "karnataka", 
      "maharashtra", "tamil nadu", "west bengal", "uttar pradesh",
      "delhi ncr", "kolkata", "hyderabad", "pune", "rupee", "crore",
      "lakh", "gst", "pib", "ministry", "parliament", "lok sabha",
      "rajya sabha", "indian government", "indian economy", "indian rupee",
      "reserve bank", "rbi", "nifty", "sensex", "india budget",
      "indian policy", "central government", "state government"
    ];
    
    const lower = content.toLowerCase();
    const isIndiaPolicy = indiaKeywords.some(keyword => lower.includes(keyword));

    if (!isIndiaPolicy) {
      setLoading(false);
      setShowIndiaWarning(true);
      
      const warningMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "⚠️ PolicyAgentX is specifically designed for Indian government policies only. Please provide an Indian policy for analysis (e.g., policies related to India, Indian states, or Indian economic indicators)."
      };
      setMessages(prev => [...prev, warningMsg]);
      
      setTimeout(() => setShowIndiaWarning(false), 5000);
      return;
    }

    // Parse input (existing logic)
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

    try {
      // Call backend API
      console.log("Sending policy simulation request...");
      const result = await simulatePolicy({
        text: content,
        region: extractedRegion,
      });

      if (!result) {
        throw new Error("No response received from server");
      }

      setApiResults(result);
      setLoading(false);
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `✅ Analysis Complete!\nAnalyzing ${extractedType} policy for ${extractedRegion}. Here are the simulated impacts:`
      };
      setMessages(prev => prev.filter(m => !m.id.startsWith("thinking-")).concat([aiMsg]));
      
      setTimeout(() => {
        setShowResults(true);
      }, 500);
    } catch (error) {
      setLoading(false);
      
      let errorMessage = "Failed to simulate policy. Please try again.";
      
      if (error instanceof Error) {
        if (error.message.includes("PolicyAgentX is specifically designed for Indian")) {
          errorMessage = "⚠️ " + error.message;
        } else if (error.message.includes("fetch")) {
          errorMessage = "Backend connection failed. Is the Flask server running on http://localhost:5000?";
        } else if (error.message.includes("JSON")) {
          errorMessage = "Backend returned invalid response. Check server logs.";
        } else if (error.message.includes("HTTP Error")) {
          errorMessage = `Server error: ${error.message}`;
        } else {
          errorMessage = error.message;
        }
      }

      console.error("Policy simulation error:", errorMessage);
      
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage,
      });
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `❌ Error: ${errorMessage}`
      };
      setMessages(prev => prev.filter(m => !m.id.startsWith("thinking-")).concat([errorMsg]));
    }
  };

  const labelClass = "text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-3 block";

  return (
    <div className="flex flex-col min-h-[calc(100vh-64px)] w-full bg-background relative">
      {/* Dynamic Header */}
      <div className="flex-none pt-8 pb-4 text-center bg-background/50 backdrop-blur-md z-40">
        <div className="flex items-center justify-center gap-3 mb-2">
          <h1 className="text-2xl md:text-3xl font-display font-bold text-gradient tracking-tight">
            Policy Agent X
          </h1>
          <span className="px-3 py-1 rounded-full bg-orange-500/20 border border-orange-500/50 text-orange-400 text-[10px] font-bold uppercase tracking-[0.1em]">
            🇮🇳 India Only
          </span>
          <Button
            onClick={handleNewChat}
            variant="outline"
            size="sm"
            className="ml-auto mr-4 flex items-center gap-2"
            title="Start new chat"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="hidden sm:inline text-[10px]">New Chat</span>
          </Button>
        </div>
        <p className="text-muted-foreground text-[10px] font-bold uppercase tracking-[0.2em] mt-1 opacity-60">
          Intelligent Research Assistant for Indian Policies
        </p>
      </div>

      {/* Main Scroller Area */}
      <div className="flex-1 px-4 md:px-0">
        <div className="max-w-4xl mx-auto w-full py-8 md:py-12 flex flex-col gap-10 pb-[150px]">
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
                  {apiResults && [
                    { label: "Economic Impact", value: apiResults.economic_impact || "N/A", positive: true },
                    { label: "Social Impact", value: apiResults.social_impact || "N/A", positive: true },
                    { label: "Business Impact", value: apiResults.business_impact || "N/A", positive: true },
                    { label: "Government Impact", value: apiResults.government_impact || "N/A", positive: true },
                  ].map((r, i) => (
                    <GlowCard
                      key={r.label}
                      delay={i * 0.05}
                      className="text-center p-6 bg-secondary/20 border-border/30 backdrop-blur-sm"
                    >
                      <p className="text-[9px] text-muted-foreground uppercase tracking-[0.1em] mb-3 font-bold opacity-70">{r.label}</p>
                      <p className={`text-2xl md:text-4xl font-display font-bold tracking-tighter mb-1 text-emerald-400 break-words`}>
                        {r.value}
                      </p>
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
        <div className="max-w-3xl mx-auto w-full px-2 md:px-3 pb-2 md:pb-3 pointer-events-auto bg-gradient-to-t from-background to-transparent pt-8">
          <ChatInput 
            onSendMessage={handleSendMessage}
            isLoading={loading} 
          />
        </div>
      </div>
    </div>
  );
};

export default SimulatePolicyPage;
