import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import ChatMessageList from "@/components/ChatMessageList";
import ChatInput from "@/components/ChatInput";
import SimulateResult from "@/components/SimulateResult";
import DinoLoadingGame from "@/components/DinoLoadingGame";
import SimulateErrorBoundary from "@/components/SimulateErrorBoundary";
import { simulatePolicy, SimulationResult } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { RotateCcw, AlertTriangle } from "lucide-react";
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

const toTitleCase = (text: string): string => {
  return normalizeDisplayText(text)
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
};

const simplifyImpactLabel = (label: string): string => {
  const clean = normalizeDisplayText(label).replace(/:$/, "").toLowerCase();

  if (clean.includes("gdp")) return "Economy effect";
  if (clean.includes("inflation")) return "Price effect";
  if (clean.includes("employment")) return "Jobs effect";
  if (clean.includes("middle class")) return "Middle-class effect";
  if (clean.includes("small business")) return "Small business effect";
  if (clean.includes("business")) return "Business effect";
  if (clean.includes("government")) return "Government effect";
  if (clean.includes("social")) return "Social effect";

  return toTitleCase(clean);
};

const cleanImpactLine = (line: string): string => {
  return normalizeDisplayText(line)
    .replace(/^[\-•→\d.)\s]+/, "")
    .replace(/\s+/g, " ")
    .trim();
};

const splitImpactLines = (text: string): string[] => {
  return (text || "")
    .split(/\n+/)
    .map(cleanImpactLine)
    .filter((line) => line.length > 0)
    .slice(0, 4);
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

export const SimulatePolicyPage = () => {
  const [policyType, setPolicyType] = useState(policyTypes[0]);
  const [value, setValue] = useState(50);
  const [region, setRegion] = useState("India");
  const [duration, setDuration] = useState(12);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showIndiaWarning, setShowIndiaWarning] = useState(false);
  const [hasControversialPolicy, setHasControversialPolicy] = useState(false);
  const [emergencyAlertActive, setEmergencyAlertActive] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  const resultsRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sirenOscRef = useRef<OscillatorNode | null>(null);
  const sirenLfoRef = useRef<OscillatorNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const [apiResults, setApiResults] = useState<SimulationResult | null>(null);
  const { toast } = useToast();

  const stopEmergencyAlarm = () => {
    try {
      sirenLfoRef.current?.stop();
      sirenOscRef.current?.stop();
    } catch {
      // Ignore stop errors from already-stopped oscillators.
    }

    try {
      sirenLfoRef.current?.disconnect();
      sirenOscRef.current?.disconnect();
      gainNodeRef.current?.disconnect();
    } catch {
      // Ignore disconnect errors during teardown.
    }

    sirenLfoRef.current = null;
    sirenOscRef.current = null;
    gainNodeRef.current = null;
  };

  const startEmergencyAlarm = async () => {
    try {
      if (!audioContextRef.current) {
        const AudioCtx = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!AudioCtx) return;
        audioContextRef.current = new AudioCtx();
      }

      const audioContext = audioContextRef.current;
      if (audioContext.state === "suspended") {
        await audioContext.resume();
      }

      stopEmergencyAlarm();

      const sirenOsc = audioContext.createOscillator();
      const sirenLfo = audioContext.createOscillator();
      const sirenGain = audioContext.createGain();

      sirenOsc.type = "sawtooth";
      sirenOsc.frequency.value = 760;

      sirenLfo.type = "sine";
      sirenLfo.frequency.value = 1.75;

      sirenGain.gain.value = 0.07;

      sirenLfo.connect(sirenOsc.frequency);
      sirenOsc.connect(sirenGain);
      sirenGain.connect(audioContext.destination);

      sirenOsc.start();
      sirenLfo.start();

      sirenOscRef.current = sirenOsc;
      sirenLfoRef.current = sirenLfo;
      gainNodeRef.current = sirenGain;
    } catch (error) {
      console.error("Unable to start emergency alarm:", error);
    }
  };

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

  useEffect(() => {
    return () => {
      stopEmergencyAlarm();
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {
          // Ignore close errors during unmount.
        });
      }
      audioContextRef.current = null;
    };
  }, []);

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
    setEmergencyAlertActive(false);
    stopEmergencyAlarm();
  };

  const handleEmergencyConfirmation = () => {
    setEmergencyAlertActive(false);
    stopEmergencyAlarm();
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
    if (isControversial) {
      setEmergencyAlertActive(true);
      startEmergencyAlarm();

      const alertMsg: Message = {
        id: `emergency-${Date.now()}`,
        role: "assistant",
        content: "🚨 EMERGENCY ALERT: This policy appears highly sensitive and can potentially trigger social unrest or riots. Confirm understanding before proceeding."
      };
      setMessages(prev => prev.concat([alertMsg]));
    }

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
        } else if (error.message.toLowerCase().includes("fetch") || error.message.toLowerCase().includes("connect to backend")) {
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

  const parseNumericMidpoint = (value?: string): number => {
    const text = (value || "").toString();
    const nums = text.match(/[-+]?\d+(?:\.\d+)?/g) || [];
    if (nums.length === 0) return 0;
    if (nums.length === 1) return Number(nums[0]) || 0;
    const a = Number(nums[0]);
    const b = Number(nums[1]);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return 0;
    return (a + b) / 2;
  };

  const parseIndiaCount = (value?: string): number => {
    const text = (value || "").toLowerCase();
    const nums = text.match(/\d+(?:\.\d+)?/g) || [];
    if (nums.length === 0) return 0;
    const first = Number(nums[0]);
    const second = nums.length > 1 ? Number(nums[1]) : first;
    const mid = (first + second) / 2;
    if (text.includes("crore")) return mid * 10_000_000;
    if (text.includes("lakh")) return mid * 100_000;
    return mid;
  };

  const parseMoneyToCrores = (value?: string): number => {
    const text = (value || "").toLowerCase();
    const nums = text.match(/\d+(?:\.\d+)?/g) || [];
    if (nums.length === 0) return 0;
    const first = Number(nums[0]);
    const second = nums.length > 1 ? Number(nums[1]) : first;
    const mid = (first + second) / 2;
    if (text.includes("crore")) return mid;
    if (text.includes("lakh")) return mid / 100;
    if (text.includes("rupee") || text.includes("rs") || text.includes("inr")) return mid / 10_000_000;
    return mid;
  };

  const clampScore = (n: number): number => Math.max(0, Math.min(100, Math.round(n)));

  const derivePolicyScores = () => {
    const cards = apiResults?.frontend_cards;
    if (!cards) {
      return { economic: 50, social: 50, business: 50, government: 50 };
    }

    const gdp = parseNumericMidpoint(cards.economic_impact?.gdp_impact_percent);
    const revenue = parseNumericMidpoint(cards.economic_impact?.revenue_generated_inr_crores);
    const requiredSpendCrores = parseMoneyToCrores(cards.economic_impact?.required_public_spend_inr);
    const inflation = (cards.economic_impact?.inflation_risk || "medium").toLowerCase();
    const inflationPenalty = inflation.includes("high") ? 18 : inflation.includes("medium") ? 9 : 3;

    const risk = Number(cards.protest_risk?.risk_score_1_to_10 || 5);
    const impacted = parseIndiaCount(cards.policy_summary?.total_people_impacted_india);
    const impactedScale = Math.min(18, Math.log10(Math.max(1, impacted)) * 2.5);

    const econ = clampScore(45 + (gdp * 14) + (Math.log10(Math.max(1, revenue)) * 6) - (Math.log10(Math.max(1, requiredSpendCrores)) * 4) - inflationPenalty);
    const social = clampScore(40 + impactedScale - (risk * 4));
    const business = clampScore(42 + (Math.log10(Math.max(1, revenue)) * 7) - (risk * 2));
    const government = clampScore(65 - (risk * 5) - (Math.log10(Math.max(1, requiredSpendCrores)) * 2));

    return { economic: econ, social, business, government };
  };

  const getImpactChartData = () => {
    if (!apiResults) return [];
    const score = derivePolicyScores();
    return [
      {
        name: "Economic",
        score: score.economic,
        impact: "economic_impact"
      },
      {
        name: "Social",
        score: score.social,
        impact: "social_impact"
      },
      {
        name: "Business",
        score: score.business,
        impact: "business_impact"
      },
      {
        name: "Government",
        score: score.government,
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

    const cards = apiResults.frontend_cards;
    const gdpMid = parseNumericMidpoint(cards?.economic_impact?.gdp_impact_percent);
    const inflationRisk = (cards?.economic_impact?.inflation_risk || "medium").toLowerCase();
    const inflationBase = inflationRisk.includes("high") ? 4.4 : inflationRisk.includes("medium") ? 3.2 : 2.0;
    const timelineSpend = [
      parseMoneyToCrores(cards?.timeline?.year_1?.inr_crore_estimate),
      parseMoneyToCrores(cards?.timeline?.year_2_3?.inr_crore_estimate),
      parseMoneyToCrores(cards?.timeline?.year_5?.inr_crore_estimate),
      parseMoneyToCrores(cards?.timeline?.year_10?.inr_crore_estimate),
    ];
    const avgSpend = timelineSpend.reduce((a, b) => a + b, 0) / Math.max(1, timelineSpend.length);

    const months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"];

    return months.map((month, i) => {
      const t = i / 5;
      return {
        month,
        inflation: Math.max(1.0, inflationBase - (gdpMid * 0.22) + (Math.log10(Math.max(1, avgSpend)) * 0.06) + (t * 0.35)),
        gdp: Math.max(0.5, 2.6 + (gdpMid * 0.8) + (t * 1.4)),
        employment: 93.5 + (gdpMid * 0.75) + (t * 1.8),
      };
    });
  };

  const getDynamicComparisonData = () => {
    if (!apiResults) return [];
    const score = derivePolicyScores();
    
    return [
      { name: "Economic", value: score.economic },
      { name: "Social", value: score.social },
      { name: "Business", value: score.business },
      { name: "Government", value: score.government },
    ];
  };

  const getScoreColor = (score: number) => {
    if (score < 30) return "#ef4444"; // red
    if (score < 50) return "#eab308"; // yellow
    if (score < 70) return "#3b82f6"; // blue
    return "#10b981"; // green
  };

  const quickScoreMap = derivePolicyScores();

  return (
    <div className="flex flex-col min-h-[calc(100vh-64px)] w-full bg-background relative">
      <AnimatePresence>
        {emergencyAlertActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[220] overflow-hidden"
          >
            <motion.div
              aria-hidden="true"
              className="absolute inset-0 bg-black"
              animate={{ opacity: [0.9, 0.35, 0.85, 0.25, 0.9] }}
              transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
            />

            <motion.div
              aria-hidden="true"
              className="absolute inset-0"
              style={{
                backgroundImage: "repeating-linear-gradient(0deg, rgba(255,0,0,0.2) 0px, rgba(255,0,0,0.2) 1px, transparent 1px, transparent 4px)"
              }}
              animate={{ opacity: [0.12, 0.45, 0.15, 0.52, 0.12] }}
              transition={{ duration: 0.4, repeat: Infinity, ease: "linear" }}
            />

            <motion.div
              aria-hidden="true"
              className="absolute inset-0"
              style={{
                background: "radial-gradient(circle at center, rgba(255,28,28,0.42), rgba(35,0,0,0.85) 55%, rgba(0,0,0,0.98) 100%)"
              }}
              animate={{ opacity: [0.35, 0.9, 0.4, 1, 0.35] }}
              transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
            />

            <div className="relative z-10 h-full flex items-center justify-center px-4">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.35 }}
                className="w-full max-w-2xl border-2 border-red-500/80 bg-black/75 backdrop-blur-md p-6 md:p-8 shadow-[0_0_50px_rgba(255,0,0,0.6)]"
              >
                <div className="flex items-center gap-3 mb-4">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1], rotate: [0, -6, 6, 0] }}
                    transition={{ duration: 0.65, repeat: Infinity }}
                  >
                    <AlertTriangle className="w-8 h-8 text-red-400" />
                  </motion.div>
                  <div>
                    <p className="text-red-400 text-xs md:text-sm font-bold tracking-[0.28em] uppercase">Threat Condition Crimson</p>
                    <p className="text-red-200 text-lg md:text-2xl font-black tracking-[0.08em] uppercase">Civil Unrest Risk Detected</p>
                  </div>
                </div>

                <div className="space-y-3 border border-red-500/50 bg-red-950/20 p-4 md:p-5">
                  <p className="text-red-100 text-sm md:text-base leading-relaxed">
                    The submitted policy content contains high-risk language that may escalate communal conflict and trigger riot conditions.
                  </p>
                  <p className="text-red-200/90 text-xs md:text-sm uppercase tracking-[0.12em]">
                    Emergency protocol requires explicit acknowledgement before alarm shutdown.
                  </p>
                </div>

                <div className="mt-5 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
                  <p className="text-red-300 text-xs uppercase tracking-[0.14em]">
                    Alarm status: active
                  </p>
                  <Button
                    type="button"
                    onClick={handleEmergencyConfirmation}
                    className="h-11 px-6 text-xs md:text-sm font-extrabold uppercase tracking-[0.12em] bg-red-500 hover:bg-red-400 text-black border border-red-300"
                  >
                    I confirm understanding this policy can cause riots
                  </Button>
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
        <div className="max-w-4xl mx-auto w-full py-6 md:py-8 flex flex-col gap-6 pb-[230px] md:pb-[250px]">
          <ChatMessageList messages={messages} loading={loading} />

          <AnimatePresence>
            {loading && (
              <motion.div
                key="dino-loading-game"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10, scale: 0.985 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
              >
                <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/20">
                  <DinoLoadingGame />
                </GlowCard>
              </motion.div>
            )}
          </AnimatePresence>

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
                  <h2 className="text-sm font-display font-bold text-foreground tracking-tight">Analysis Results</h2>
                  <div className="h-px bg-gradient-to-r from-border/30 to-transparent" />
                </div>

                {/* Quick Impact Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-2 md:px-0">
                  {apiResults && [
                    { label: "Economic", score: quickScoreMap.economic, color: "from-blue-500 to-blue-400" },
                    { label: "Social", score: quickScoreMap.social, color: "from-emerald-500 to-emerald-400" },
                    { label: "Business", score: quickScoreMap.business, color: "from-purple-500 to-purple-400" },
                    { label: "Government", score: quickScoreMap.government, color: "from-amber-500 to-amber-400" },
                  ].map((r, i) => {
                    const score = r.score;
                    return (
                      <motion.div
                        key={r.label}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.1 }}
                        className="animated-card p-4 rounded-xl border border-border/30 bg-secondary/30 backdrop-blur-sm"
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
                          {splitImpactLines(section.value).map((line, lineIdx) => {
                            const [rawLabel, ...rest] = line.split(":");
                            const hasLabel = rest.length > 0;
                            const label = hasLabel ? simplifyImpactLabel(rawLabel) : "Detail";
                            const content = hasLabel ? rest.join(":").trim() : line;

                            return (
                              <div key={lineIdx} className="inner-card-surface impact-detail-card rounded-xl border border-border/20 px-3 py-2.5">
                                <p className="text-[10px] uppercase tracking-[0.14em] text-accent font-bold mb-1">{label}</p>
                                <p className="text-xs text-muted-foreground leading-relaxed">{content}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </GlowCard>

                {/* Overall Impact Chart */}
                <GlowCard hoverable={false} className="chart-panel p-6 bg-secondary/10 border-border/20">
                  <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-4">Overall Impact Score</p>
                  <div className="chart-canvas">
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={getImpactChartData()}>
                        <defs>
                          <linearGradient id="simImpactBarGradient" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stopColor="hsl(var(--chart-line-secondary))" stopOpacity={0.95} />
                            <stop offset="45%" stopColor="hsl(var(--chart-bar-positive))" stopOpacity={0.95} />
                            <stop offset="100%" stopColor="hsl(var(--chart-line-gdp))" stopOpacity={0.92} />
                            <animateTransform
                              attributeName="gradientTransform"
                              type="translate"
                              values="-1 0;1 0;-1 0"
                              dur="10s"
                              repeatCount="indefinite"
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="8 8" stroke="hsl(var(--chart-grid))" vertical={false} />
                        <XAxis dataKey="name" stroke="hsl(var(--chart-axis))" fontSize={10} tickLine={false} axisLine={false} />
                        <YAxis stroke="hsl(var(--chart-axis))" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} />
                        <Tooltip 
                          contentStyle={{
                            background: "hsl(var(--chart-tooltip-bg))",
                            border: "1px solid hsl(var(--chart-tooltip-border))",
                            borderRadius: "12px",
                            color: "hsl(var(--chart-tooltip-text))",
                            fontSize: 11,
                          }}
                          formatter={(value) => [`${value}% Positive`, "Score"]}
                        />
                        <Bar 
                          dataKey="score" 
                          fill="url(#simImpactBarGradient)" 
                          radius={[8, 8, 0, 0]}
                          animationDuration={1000}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </GlowCard>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 px-2 md:px-0">
                  <GlowCard hoverable={false} className="chart-panel p-6 bg-secondary/10 border-border/20">
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold">Trend Forecast</p>
                      <div className="flex gap-3">
                        <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-foreground"/><span className="text-[8px] text-muted-foreground uppercase">GDP</span></div>
                        <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-indigo-400"/><span className="text-[8px] text-muted-foreground uppercase">INF</span></div>
                      </div>
                    </div>
                    <div className="chart-canvas">
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={getDynamicTrendData()}>
                        <defs>
                          <linearGradient id="simGdpLineGradient" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="hsl(var(--chart-line-primary))" stopOpacity={0.95} />
                            <stop offset="100%" stopColor="hsl(var(--chart-line-secondary))" stopOpacity={0.95} />
                            <animateTransform
                              attributeName="gradientTransform"
                              type="translate"
                              values="-1 0;1 0;-1 0"
                              dur="9s"
                              repeatCount="indefinite"
                            />
                          </linearGradient>
                          <linearGradient id="simInfLineGradient" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="hsl(var(--chart-line-secondary))" stopOpacity={0.94} />
                            <stop offset="100%" stopColor="hsl(var(--chart-line-employment))" stopOpacity={0.94} />
                            <animateTransform
                              attributeName="gradientTransform"
                              type="translate"
                              values="1 0;-1 0;1 0"
                              dur="8s"
                              repeatCount="indefinite"
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="8 8" stroke="hsl(var(--chart-grid))" vertical={false} />
                        <XAxis dataKey="month" stroke="hsl(var(--chart-axis))" fontSize={9} tickLine={false} axisLine={false} tick={{dy: 8}} />
                        <YAxis stroke="hsl(var(--chart-axis))" fontSize={9} tickLine={false} axisLine={false} tick={{dx: -8}} />
                        <Tooltip
                          contentStyle={{
                            background: "hsl(var(--chart-tooltip-bg))",
                            border: "1px solid hsl(var(--chart-tooltip-border))",
                            borderRadius: "12px",
                            color: "hsl(var(--chart-tooltip-text))",
                            fontSize: 10,
                          }}
                        />
                        <Line type="monotone" dataKey="gdp" stroke="url(#simGdpLineGradient)" strokeWidth={2.7} dot={false} />
                        <Line type="monotone" dataKey="inflation" stroke="url(#simInfLineGradient)" strokeWidth={2.7} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                    </div>
                  </GlowCard>

                  <GlowCard hoverable={false} className="chart-panel p-6 bg-secondary/10 border-border/20">
                    <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold mb-4">Impact Distribution</p>
                    <div className="chart-canvas">
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={getDynamicComparisonData()}>
                        <defs>
                          <linearGradient id="simDistributionBarGradient" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stopColor="hsl(var(--chart-line-secondary))" stopOpacity={0.95} />
                            <stop offset="100%" stopColor="hsl(var(--chart-bar-positive))" stopOpacity={0.94} />
                            <animateTransform
                              attributeName="gradientTransform"
                              type="rotate"
                              values="0 0.5 0.5;360 0.5 0.5"
                              dur="14s"
                              repeatCount="indefinite"
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="8 8" stroke="hsl(var(--chart-grid))" vertical={false} />
                        <XAxis dataKey="name" stroke="hsl(var(--chart-axis))" fontSize={9} tickLine={false} axisLine={false} tick={{dy: 8}} />
                        <YAxis stroke="hsl(var(--chart-axis))" fontSize={9} tickLine={false} axisLine={false} tick={{dx: -8}} />
                        <Tooltip
                          contentStyle={{
                            background: "hsl(var(--chart-tooltip-bg))",
                            border: "1px solid hsl(var(--chart-tooltip-border))",
                            borderRadius: "12px",
                            color: "hsl(var(--chart-tooltip-text))",
                            fontSize: 10,
                          }}
                        />
                        <Bar dataKey="value" fill="url(#simDistributionBarGradient)" radius={[4, 4, 0, 0]} barSize={35} />
                      </BarChart>
                    </ResponsiveContainer>
                    </div>
                  </GlowCard>
                </div>

                {/* New Deep Analysis Cards (shown after legacy sections) */}
                <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/20">
                  <p className={labelClass + " mb-4"}>Deep Sectioned Analysis</p>
                  <SimulateErrorBoundary>
                    <SimulateResult results={apiResults} />
                  </SimulateErrorBoundary>
                </GlowCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Input Overlay */}
      <div className="fixed bottom-0 left-0 right-0 z-[100] pointer-events-none">
        <div className="max-w-3xl mx-auto w-full px-2 md:px-3 pb-3 md:pb-4 pointer-events-auto bg-gradient-to-t from-background via-background/95 to-transparent pt-10">
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
