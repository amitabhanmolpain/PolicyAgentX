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
const regions = ["India"];

const simpleStem = (word: string): string => {
  let token = (word || "").toLowerCase().replace(/[^a-z]/g, "");
  const suffixes = ["ingly", "edly", "ment", "tion", "sion", "ance", "ence", "ing", "ed", "ly", "es", "s"];
  for (const suffix of suffixes) {
    if (token.endsWith(suffix) && token.length > suffix.length + 2) {
      token = token.slice(0, -suffix.length);
      break;
    }
  }
  return token;
};

const tokenizeAndStem = (text: string): string[] => {
  return (text.match(/[a-zA-Z]+/g) || []).map(simpleStem).filter(Boolean);
};

const countStemMatches = (text: string, keywords: string[]): number => {
  const stems = tokenizeAndStem(text || "");
  const keywordStems = new Set(keywords.map(simpleStem));
  return stems.reduce((acc, stem) => acc + (keywordStems.has(stem) ? 1 : 0), 0);
};

const normalizeDisplayText = (text: string): string => {
  return (text || "").replace(/_/g, " ").replace(/\s+/g, " ").trim();
};

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
  const [region, setRegion] = useState("India");
  const [duration, setDuration] = useState(12);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showIndiaWarning, setShowIndiaWarning] = useState(false);
  const [hasControversialPolicy, setHasControversialPolicy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  const resultsRef = useRef<HTMLDivElement>(null);
  const [apiResults, setApiResults] = useState<SimulationResult | null>(null);
  const { toast } = useToast();

  // Load messages and results from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem("policySimulationChat");
    const savedResults = localStorage.getItem("policySimulationResults");
    const savedShowResults = localStorage.getItem("policySimulationShowResults");
    const savedControversial = localStorage.getItem("policySimulationControversial");

    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch {
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

    if (savedResults) {
      try {
        setApiResults(JSON.parse(savedResults));
      } catch {
        // fallback if parsing fails
      }
    }

    if (savedShowResults) {
      try {
        setShowResults(JSON.parse(savedShowResults));
      } catch {
        // fallback
      }
    }

    if (savedControversial) {
      try {
        setHasControversialPolicy(JSON.parse(savedControversial));
      } catch {
        // fallback
      }
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("policySimulationChat", JSON.stringify(messages));
  }, [messages]);

  // Save results to localStorage whenever they change
  useEffect(() => {
    if (apiResults) {
      localStorage.setItem("policySimulationResults", JSON.stringify(apiResults));
    }
  }, [apiResults]);

  // Save showResults state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("policySimulationShowResults", JSON.stringify(showResults));
  }, [showResults]);

  // Save controversial policy flag to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("policySimulationControversial", JSON.stringify(hasControversialPolicy));
  }, [hasControversialPolicy]);

  const handleNewChat = () => {
    localStorage.removeItem("policySimulationChat");
    localStorage.removeItem("policySimulationResults");
    localStorage.removeItem("policySimulationShowResults");
    localStorage.removeItem("policySimulationControversial");
    localStorage.removeItem("policyCompareData");
    localStorage.removeItem("policyCompareSourceText");
    localStorage.setItem("policyCompareNeedsRefresh", "true");
    setMessages([
      {
        id: "initial-ai",
        role: "assistant",
        content: "Hello! I am your Policy Simulation Assistant. Specify a policy, region, and duration, and I'll analyze the socio-economic impacts for you."
      }
    ]);
    setShowResults(false);
    setApiResults(null);
    setHasControversialPolicy(false);
  };

  const detectControversialPolicy = (text: string): boolean => {
    const controversialKeywords = [
      "removal", "expulsion", "ban", "discriminat", "religion", "communal", "riot", "violence",
      "caste", "hindu", "muslim", "christian", "sikh", "buddha", "jew", "minority", "majority",
      "ethnic", "racial", "persecution", "genocide", "massacre", "pogrom", "cleansing",
      "sectarian", "religious hatred", "religious conflict", "communal violence", "riots",
      "targeted killing", "targeted attack", "religious targeting", "faith-based discrimination",
      "anti-semitism", "islamophobia", "hinduphobia", "christianophobia", "religious intolerance"
    ];
    
    const lower = text.toLowerCase();
    return controversialKeywords.some(keyword => lower.includes(keyword));
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
// Check for controversial policy
    const isControversial = detectControversialPolicy(content);
    setHasControversialPolicy(isControversial);

    // Check if policy is explicitly for NON-India countries (default to India)
    const nonIndiaKeywords = [
      "usa", "america", "us", "united states", "american",
      "europe", "european", "uk", "united kingdom", "british",
      "china", "chinese", "japan", "japanese", "south korea", "korean",
      "africa", "african", "australia", "australian", "canada", "canadian",
      "brazil", "mexican", "mexico", "russia", "middle east", "arab",
      "singapore", "thailand", "vietnam", "malaysia"
    ];
    
    const lower = content.toLowerCase();
    const isNonIndiaPolicy = nonIndiaKeywords.some(keyword => lower.includes(keyword));

    if (isNonIndiaPolicy) {
      setLoading(false);
      setShowIndiaWarning(true);
      
      const warningMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "⚠️ PolicyAgentX is specifically designed for Indian policies only. The policy you mentioned appears to be for another country. Please provide an Indian policy for analysis."
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
      if (result?.policy_text) {
        localStorage.setItem("policyLatestPolicyText", result.policy_text);
      }
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

  const analyzeImpactSentiment = (text: string): number => {
    if (!text) return 0;
    const positive = countStemMatches(text, ["benefits", "positive", "increase", "boost", "improve", "growth", "strength"]);
    const negative = countStemMatches(text, ["decrease", "loss", "decline", "harm", "reduce", "negative", "worsen"]);
    const neutral = countStemMatches(text, ["unchanged", "stable", "maintain"]);
    const total = positive + negative + neutral;
    if (total === 0) return 50;
    return Math.round((positive / total) * 100);
  };

  const getImpactChartData = () => {
    if (!apiResults) return [];
    return [
      {
        name: "Economic",
        score: analyzeImpactSentiment(apiResults.economic_impact),
        impact: "economic_impact"
      },
      {
        name: "Social",
        score: analyzeImpactSentiment(apiResults.social_impact),
        impact: "social_impact"
      },
      {
        name: "Business",
        score: analyzeImpactSentiment(apiResults.business_impact),
        impact: "business_impact"
      },
      {
        name: "Government",
        score: analyzeImpactSentiment(apiResults.government_impact),
        impact: "government_impact"
      },
    ];
  };

  const getDynamicTrendData = () => {
    if (!apiResults) {
      const months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"];
      return months.map((month, i) => ({
        month,
        inflation: 2.5 - (i * 0.2),
        gdp: 3.5 + (i * 0.3),
        employment: 95 + (i * 0.25),
      }));
    }
    
    const months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"];
    const economicScore = analyzeImpactSentiment(apiResults.economic_impact);
    const baseSentiment = (economicScore - 50) / 50; // -1 to 1
    
    return months.map((month, i) => {
      const monthIndex = (i + 1) / 6;
      return {
        month,
        inflation: Math.max(1.0, 2.5 - (i * 0.25) - (baseSentiment * 0.5)),
        gdp: 3.0 + (i * 0.4) + (baseSentiment * 0.8),
        employment: 94.5 + (i * 0.3) + (baseSentiment * 0.5),
      };
    });
  };

  const getDynamicComparisonData = () => {
    if (!apiResults) return [];
    
    const economicScore = analyzeImpactSentiment(apiResults.economic_impact);
    const socialScore = analyzeImpactSentiment(apiResults.social_impact);
    const businessScore = analyzeImpactSentiment(apiResults.business_impact);
    const governmentScore = analyzeImpactSentiment(apiResults.government_impact);
    
    return [
      { name: "Economic", value: economicScore },
      { name: "Social", value: socialScore },
      { name: "Business", value: businessScore },
      { name: "Government", value: governmentScore },
    ];
  };

  const getScoreColor = (score: number) => {
    if (score < 30) return "#ef4444"; // red
    if (score < 50) return "#eab308"; // yellow
    if (score < 70) return "#3b82f6"; // blue
    return "#10b981"; // green
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-64px)] w-full bg-background relative">
      {/* Controversial Policy Alert */}
      <AnimatePresence>
        {hasControversialPolicy && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full bg-red-950/80 border-b-2 border-red-500 py-4 px-4 backdrop-blur-sm"
          >
            <div className="max-w-4xl mx-auto flex items-center gap-4">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.8, repeat: Infinity }}
                className="w-4 h-4 rounded-full bg-red-600 shadow-lg shadow-red-600/50 flex-shrink-0"
              />
              <div className="flex-1">
                <p className="text-red-400 font-bold text-sm uppercase tracking-wide">⚠️ HIGH RISK ALERT</p>
                <p className="text-red-300 text-xs mt-1">This policy contains contentious content that could potentially lead to social unrest, communal tensions, or rioting. Please review with extreme caution and consult domain experts.</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Dynamic Header */}
      <div className="flex-none px-4 md:px-0 pt-5 pb-4 bg-background/50 backdrop-blur-md z-40 border-b border-border/10">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-display font-bold text-gradient tracking-tight">
              Policy Agent X
            </h1>
            <span className="px-2 py-0.5 rounded-full bg-orange-500/20 border border-orange-500/50 text-orange-400 text-[8px] font-bold uppercase tracking-[0.1em]">
              🇮🇳 India Only
            </span>
          </div>
          <Button
            onClick={handleNewChat}
            variant="outline"
            size="sm"
            className="flex items-center gap-1.5 h-8 text-xs"
            title="Start new chat"
          >
            <RotateCcw className="w-3 h-3" />
            <span>New Chat</span>
          </Button>
        </div>
      </div>

      {/* Main Scroller Area */}
      <div className="flex-1 px-4 md:px-0">
        <div className="max-w-4xl mx-auto w-full py-6 md:py-8 flex flex-col gap-6 pb-[140px]">
          <ChatMessageList messages={messages} loading={loading} />

          <AnimatePresence>
            {showResults && (
              <motion.div
                ref={resultsRef}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 30 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="space-y-6 pt-8 border-t border-border/20"
              >
                {/* Section Header */}
                <div className="space-y-4 px-2 md:px-0">
                  <h2 className="text-sm font-display font-bold text-white tracking-tight">Analysis Results</h2>
                  <div className="h-px bg-gradient-to-r from-border/30 to-transparent" />
                </div>

                {/* Quick Impact Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-2 md:px-0">
                  {apiResults && [
                    { label: "Economic", value: apiResults.economic_impact, color: "from-blue-500 to-blue-400" },
                    { label: "Social", value: apiResults.social_impact, color: "from-emerald-500 to-emerald-400" },
                    { label: "Business", value: apiResults.business_impact, color: "from-purple-500 to-purple-400" },
                    { label: "Government", value: apiResults.government_impact, color: "from-amber-500 to-amber-400" },
                  ].map((r, i) => {
                    const score = analyzeImpactSentiment(r.value);
                    return (
                      <motion.div
                        key={r.label}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.1 }}
                        className="p-4 rounded-xl border border-border/30 bg-secondary/30 backdrop-blur-sm"
                      >
                        <p className="text-[9px] text-muted-foreground uppercase tracking-[0.1em] mb-2 font-bold">{r.label}</p>
                        <div className="mb-2">
                          <span className={`text-xl font-bold bg-gradient-to-r ${r.color} bg-clip-text text-transparent`}>{score}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-secondary/50 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${score}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className={`h-full rounded-full bg-gradient-to-r ${r.color}`}
                          />
                        </div>
                      </motion.div>
                    );
                  })}
                </div>

                {/* Detailed Impact Analysis */}
                <GlowCard hoverable={false} className="p-8 bg-secondary/10 border-border/20">
                  <p className={labelClass + " mb-0"}>Impact Details</p>
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                    {apiResults && [
                      { label: "Economic & Social", value: apiResults.economic_impact + "\n" + apiResults.social_impact },
                      { label: "Business & Government", value: apiResults.business_impact + "\n" + apiResults.government_impact },
                    ].map((section, idx) => (
                      <div key={idx} className="space-y-4">
                        <p className="text-[9px] text-muted-foreground uppercase tracking-[0.15em] font-bold">{section.label}</p>
                        <div className="space-y-2">
                          {section.value.split('\n').slice(0, 4).map((line, lineIdx) => {
                            const cleanLine = line.trim();
                            if (!cleanLine || cleanLine.length < 10) return null;
                            return (
                              <div key={lineIdx} className="flex gap-2">
                                <span className="text-accent font-bold text-xs flex-shrink-0 mt-0.5">→</span>
                                <p className="text-xs text-muted-foreground leading-relaxed">{normalizeDisplayText(cleanLine).slice(0, 100)}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </GlowCard>

                {/* Overall Impact Chart */}
                <GlowCard hoverable={false} className="p-6 bg-secondary/10 border-border/20">
                  <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-4">Overall Impact Score</p>
                  <div>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={getImpactChartData()}>
                        <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} />
                        <YAxis stroke="#71717A" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} />
                        <Tooltip 
                          contentStyle={{ background: "#0B0B0C", border: "1px solid #1F1F23", borderRadius: "12px", fontSize: 11 }}
                          formatter={(value) => [`${value}% Positive`, "Score"]}
                        />
                        <Bar 
                          dataKey="score" 
                          fill="#10b981" 
                          radius={[8, 8, 0, 0]}
                          animationDuration={1000}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </GlowCard>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 px-2 md:px-0">
                  <GlowCard hoverable={false} className="p-6 bg-secondary/10 border-border/20">
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold">Trend Forecast</p>
                      <div className="flex gap-3">
                        <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-white"/><span className="text-[8px] text-muted-foreground uppercase">GDP</span></div>
                        <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-indigo-400"/><span className="text-[8px] text-muted-foreground uppercase">INF</span></div>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={getDynamicTrendData()}>
                        <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                        <XAxis dataKey="month" stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dy: 8}} />
                        <YAxis stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dx: -8}} />
                        <Tooltip contentStyle={{ background: "#0B0B0C", border: "1px solid #1F1F23", borderRadius: "12px", fontSize: 10 }} />
                        <Line type="monotone" dataKey="gdp" stroke="#FFFFFF" strokeWidth={2.5} dot={false} />
                        <Line type="monotone" dataKey="inflation" stroke="#6366F1" strokeWidth={2.5} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </GlowCard>

                  <GlowCard hoverable={false} className="p-6 bg-secondary/10 border-border/20">
                    <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-4">Impact Distribution</p>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={getDynamicComparisonData()}>
                        <CartesianGrid strokeDasharray="8 8" stroke="#1F1F23" vertical={false} />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dy: 8}} />
                        <YAxis stroke="#71717A" fontSize={9} tickLine={false} axisLine={false} tick={{dx: -8}} />
                        <Tooltip contentStyle={{ background: "#0B0B0C", border: "1px solid #1F1F23", borderRadius: "12px", fontSize: 10 }} />
                        <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} barSize={35} />
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
