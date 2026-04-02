import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

import { Award, Loader, AlertCircle } from "lucide-react";
import { getHistory, improvePolicy } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface PolicyMetrics {
  inflation_impact: number;
  gdp_growth: number;
  employment_change: number;
  sentiment_score: number;
  economic_impact: string;
  social_impact: string;
  business_impact: string;
  government_impact: string;
}

interface ComparisonData {
  original_policy: string;
  improved_policy: string;
  original_metrics: PolicyMetrics;
  improved_metrics: PolicyMetrics;
  improvements: {
    gdp_improvement: number;
    employment_improvement: number;
    inflation_improvement: number;
    sentiment_improvement: number;
  };
}

const sanitizeText = (text: string) => {
  return (text || "")
    .replace(/[\u2022\u25CF\u25A0\u2605\u2713\u2714]/g, " ")
    .replace(/[^\w\s.,:%()\-\n]/g, " ")
    .replace(/[ \t]+/g, " ")
    .trim();
};

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
  return ((text || "").match(/[a-zA-Z]+/g) || []).map(simpleStem).filter(Boolean);
};

const countStemMatches = (text: string, keywords: string[]): number => {
  const stems = tokenizeAndStem(text);
  const keywordStems = new Set(keywords.map(simpleStem));
  return stems.reduce((acc, stem) => acc + (keywordStems.has(stem) ? 1 : 0), 0);
};

const toPolicyPoints = (text: string): string[] => {
  const lines = sanitizeText(text)
    .split("\n")
    .map((line) => line.replace(/^\s*[-*#>\d.)]+\s*/, "").trim())
    .filter((line) => line.length > 20);

  if (lines.length >= 3) {
    return Array.from(new Set(lines)).slice(0, 8);
  }

  const sentencePoints = sanitizeText(text)
    .split(/(?<=[.!?])\s+/)
    .map((line) => line.trim())
    .filter((line) => line.length > 20);

  return Array.from(new Set(sentencePoints)).slice(0, 8);
};

const toSimplePolicySummary = (text: string): string => {
  const cleaned = (text || "")
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/#+\s*/g, " ")
    .replace(/\*\*/g, " ")
    .replace(/\*/g, " ")
    .replace(/`/g, " ")
    .replace(/\btitle\s*:/gi, " ")
    .replace(/\bpolicy title\s*:/gi, " ")
    .replace(/\s+/g, " ")
    .trim();

  const plain = sanitizeText(cleaned)
    .replace(/\s+/g, " ")
    .trim();

  const sentences = plain
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 20)
    .slice(0, 2);

  if (sentences.length > 0) {
    return sentences.join(" ");
  }

  if (plain.length > 0) {
    return plain.slice(0, 220);
  }

  return "This policy explains the main goal, who is affected, and how implementation can happen in India.";
};

const getOriginalCons = (metrics: PolicyMetrics): string[] => {
  const sources = [
    metrics.economic_impact,
    metrics.social_impact,
    metrics.business_impact,
    metrics.government_impact,
  ]
    .map((text) => sanitizeText(text))
    .join(" ");

  const negativeKeywords = [
    "risk", "burden", "challenge", "cost", "decline", "inflation", "loss",
    "delay", "inequality", "unemployment", "resistance", "protest", "pressure",
  ];

  const extracted = sources
    .split(/(?<=[.!?])\s+/)
    .map((line) => line.trim())
    .filter((line) => line.length > 25)
    .filter((line) => countStemMatches(line, negativeKeywords) > 0);

  const unique = Array.from(new Set(extracted)).slice(0, 5);
  if (unique.length > 0) {
    return unique;
  }

  const fallback: string[] = [];
  if (metrics.inflation_impact > 0) {
    fallback.push("Inflation may rise and reduce household purchasing power.");
  }
  if (metrics.employment_change < 0.5) {
    fallback.push("Employment gains are limited under the current design.");
  }
  if (metrics.sentiment_score < 60) {
    fallback.push("Public sentiment may remain mixed due to unclear benefits.");
  }
  if (metrics.gdp_growth < 1) {
    fallback.push("GDP growth impact appears modest compared with potential alternatives.");
  }

  return fallback.length > 0
    ? fallback
    : ["The original policy has unclear implementation and impact trade-offs."];
};

const AnimatedValue = ({ target, suffix = "", decimals = 1 }: { target: number; suffix?: string; decimals?: number }) => {
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
  return <>{val.toFixed(decimals)}{suffix}</>;
};

const ComparePage = () => {
  const [data, setData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [geminiError, setGeminiError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const fetchAndCompare = async () => {
      try {
        setLoading(true);

        const cachedData = localStorage.getItem("policyCompareData");
        const cachedSourceText = localStorage.getItem("policyCompareSourceText") || "";
        const needsRefresh = localStorage.getItem("policyCompareNeedsRefresh") === "true";
        const latestPolicyText = localStorage.getItem("policyLatestPolicyText") || "";

        if (cachedData && !needsRefresh && cachedSourceText && cachedSourceText === latestPolicyText) {
          const parsed = JSON.parse(cachedData) as ComparisonData;
          setData(parsed);
          if ((parsed as any).gemini_error) {
            setGeminiError((parsed as any).gemini_error);
          }
          setLoading(false);
          return;
        }
        
        // Fetch last policy from history with timeout
        const historyPromise = getHistory();
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Request timeout")), 30000)
        );
        
        const history = await Promise.race([historyPromise, timeoutPromise]) as any[];
        
        console.log("Total history items:", history.length);
        
        if (!history || history.length === 0) {
          toast({
            variant: "destructive",
            title: "No policies found",
            description: "Please run a simulation first to compare policies.",
          });
          setLoading(false);
          return;
        }
        
        // Filter to India policies only
        const indiaHistory = history.filter(item => item.region === "India" || !item.region);
        
        console.log("India policies:", indiaHistory.length);
        
        if (indiaHistory.length === 0) {
          toast({
            variant: "destructive",
            title: "No India policies found",
            description: "All policies in history are for other regions.",
          });
          setLoading(false);
          return;
        }
        
        // Find the first policy with valid text
        let lastPolicy = null;
        let policyText = "";
        
        for (let i = 0; i < indiaHistory.length; i++) {
          const item = indiaHistory[i];
          const text = item.policy_text || item.text || item.policy || "";
          
          if (text && text.trim().length > 0) {
            lastPolicy = item;
            policyText = text;
            console.log(`Found valid policy at index ${i}`);
            break;
          }
        }
        
        if (!lastPolicy || !policyText.trim()) {
          console.log("Sample history item:", indiaHistory[0]);
          console.log("All history items count:", indiaHistory.length);
          toast({
            variant: "destructive",
            title: "Invalid policy",
            description: `Could not extract policy text. Checked ${indiaHistory.length} items.`,
          });
          setLoading(false);
          return;
        }
        
        console.log("Using policy:", policyText.slice(0, 100));
        
        // Generate improved version with timeout
        const improvePromise = improvePolicy(policyText);
        const improveTimeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Policy improvement timeout - request took too long")), 120000)
        );
        
        const comparisonData = await Promise.race([improvePromise, improveTimeoutPromise]);
        setData(comparisonData);

        localStorage.setItem("policyCompareData", JSON.stringify(comparisonData));
        localStorage.setItem("policyCompareSourceText", policyText);
        localStorage.setItem("policyLatestPolicyText", policyText);
        localStorage.setItem("policyCompareNeedsRefresh", "false");
        
        // Check if there was a Gemini error
        if (comparisonData.gemini_error) {
          setGeminiError(comparisonData.gemini_error);
          toast({
            variant: "destructive",
            title: "Gemini API Error",
            description: "Could not generate AI improvements due to API quota. Showing heuristic improvements instead.",
          });
        }
        
      } catch (error) {
        let errorMessage = "Failed to load comparison";
        
        if (error instanceof Error) {
          if (error.message.includes("timeout")) {
            errorMessage = "Request took too long. Please try again.";
          } else if (error.message.includes("ERR_CONNECTION_REFUSED")) {
            errorMessage = "Backend server is not responding. Please ensure the Flask server is running on http://localhost:5000";
          } else {
            errorMessage = error.message;
          }
        }
        
        console.error("Compare page error:", error);
        
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage,
        });
      } finally {
        setLoading(false);
      }
    };
    
    // Add a small delay to ensure backend is ready
    const timer = setTimeout(fetchAndCompare, 500);
    return () => clearTimeout(timer);
  }, [toast]);

  const renderPolicyCard = (
    policy: string,
    metrics: PolicyMetrics,
    label: string,
    isRecommended: boolean
  ) => (
    <GlowCard hoverable={false} className="relative p-10">
      {isRecommended && (
        <div className="absolute -top-3 left-10 flex items-center gap-2 px-4 py-1.5 rounded-full text-[10px] font-display font-bold uppercase tracking-[0.2em] bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]">
          <Award className="w-3 h-3" /> Recommended
        </div>
      )}
      <h3 className="text-xl font-display font-bold text-foreground mb-2 mt-2 tracking-tight">{label}</h3>
      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground mb-2 font-semibold">What this policy means</p>
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-4">{toSimplePolicySummary(policy)}</p>
      </div>
      
      <div className="space-y-6 mt-4">
        {[
          { label: "GDP Growth", value: metrics.gdp_growth, suffix: "%" },
          { label: "Employment Change", value: metrics.employment_change, suffix: "%" },
          { label: "Inflation Impact", value: metrics.inflation_impact, suffix: "%" },
          { label: "Sentiment", value: metrics.sentiment_score, suffix: "%" },
        ].map((item) => (
          <div key={item.label} className="group">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-[0.15em] font-semibold">{item.label}</span>
              <span className={`font-display font-bold text-xl tracking-tighter ${item.value >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                <AnimatedValue target={item.value} suffix={item.suffix} decimals={1} />
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

  if (loading) {
    return (
      <div className="container mx-auto px-8 py-20 max-w-6xl flex items-center justify-center min-h-[60vh]">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <Loader className="w-8 h-8 text-accent" />
          </motion.div>
          <p className="text-muted-foreground text-sm">Generating improved policy and comparison...</p>
        </motion.div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container mx-auto px-8 py-20 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-4xl md:text-5xl font-display font-bold text-gradient mb-4 tracking-tight">
            Policy Comparison
          </h1>
          <p className="text-secondary-foreground">No policies available for comparison. Run a simulation first.</p>
        </motion.div>
      </div>
    );
  }

  const improvedPolicyPoints = toPolicyPoints(data.improved_policy);
  const originalPolicyCons = getOriginalCons(data.original_metrics);

  const improvementChartData = [
    { name: "GDP", value: Number(data.improvements.gdp_improvement.toFixed(2)) },
    { name: "Employment", value: Number(data.improvements.employment_improvement.toFixed(2)) },
    { name: "Sentiment", value: Number(data.improvements.sentiment_improvement.toFixed(2)) },
    { name: "Inflation Stability", value: Number((-data.improvements.inflation_improvement).toFixed(2)) },
  ];

  const dynamicComparisonData = [
    {
      stage: "Original",
      gdp: Number(data.original_metrics.gdp_growth.toFixed(2)),
      employment: Number(data.original_metrics.employment_change.toFixed(2)),
      sentiment: Number(data.original_metrics.sentiment_score.toFixed(2)),
    },
    {
      stage: "Improved",
      gdp: Number(data.improved_metrics.gdp_growth.toFixed(2)),
      employment: Number(data.improved_metrics.employment_change.toFixed(2)),
      sentiment: Number(data.improved_metrics.sentiment_score.toFixed(2)),
    },
  ];

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
          AI-generated comparison of original vs improved policy framework to identify optimal socio-economic outcomes.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {renderPolicyCard(
          data.original_policy,
          data.original_metrics,
          "Original Policy",
          false
        )}
        {renderPolicyCard(
          data.improved_policy,
          data.improved_metrics,
          "Improved Policy",
          true
        )}
      </div>

      {/* API Error Warning */}
      {geminiError && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-400">API Rate Limit Exceeded</p>
            <p className="text-xs text-amber-300 mt-1">The AI policy improvement used a fallback method due to API quota limits. The comparison is based on heuristic enhancements rather than AI-generated improvements.</p>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <GlowCard hoverable={false} className="p-8 bg-secondary/10 border-emerald-500/30">
          <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-400 mb-5 font-bold">Improved Policy In Clear Points</p>
          <ul className="space-y-3">
            {improvedPolicyPoints.map((point, index) => (
              <li key={`${index}-${point.slice(0, 20)}`} className="text-sm text-emerald-100 leading-relaxed">
                {index + 1}. {point}
              </li>
            ))}
          </ul>
        </GlowCard>

        <GlowCard hoverable={false} className="p-8 bg-secondary/10 border-rose-500/30">
          <p className="text-[10px] uppercase tracking-[0.2em] text-rose-400 mb-5 font-bold">Cons Of Original Policy</p>
          <ul className="space-y-3">
            {originalPolicyCons.map((item, index) => (
              <li key={`${index}-${item.slice(0, 20)}`} className="text-sm text-rose-100 leading-relaxed">
                {index + 1}. {item}
              </li>
            ))}
          </ul>
        </GlowCard>
      </div>

      <GlowCard hoverable={false} className="p-10 mb-12 bg-secondary/10 border-border/20">
        <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-8 font-bold">Dynamic Graphs For Improved Policy</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="h-[280px]">
            <p className="text-xs text-muted-foreground mb-4">Improvement by metric</p>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={improvementChartData}>
                <CartesianGrid strokeDasharray="4 4" stroke="#2A2A31" />
                <XAxis dataKey="name" stroke="#8E8E99" fontSize={11} />
                <YAxis stroke="#8E8E99" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "#151517",
                    border: "1px solid #2A2A31",
                    borderRadius: "10px",
                    color: "#FFFFFF",
                    fontSize: 12,
                  }}
                  formatter={(value) => [`${value}%`, "Improvement"]}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="h-[280px]">
            <p className="text-xs text-muted-foreground mb-4">Original vs improved trend</p>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dynamicComparisonData}>
                <CartesianGrid strokeDasharray="4 4" stroke="#2A2A31" />
                <XAxis dataKey="stage" stroke="#8E8E99" fontSize={11} />
                <YAxis stroke="#8E8E99" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "#151517",
                    border: "1px solid #2A2A31",
                    borderRadius: "10px",
                    color: "#FFFFFF",
                    fontSize: 12,
                  }}
                />
                <Line type="monotone" dataKey="gdp" stroke="#34d399" strokeWidth={2} dot={{ r: 4 }} name="GDP" />
                <Line type="monotone" dataKey="employment" stroke="#60a5fa" strokeWidth={2} dot={{ r: 4 }} name="Employment" />
                <Line type="monotone" dataKey="sentiment" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} name="Sentiment" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </GlowCard>

      {/* Benefits Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <GlowCard hoverable={false} className="p-10 bg-secondary/10 border-border/20">
          <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-6 font-bold">Original Policy Impact</p>
          <div className="space-y-4">
            <div>
              <p className="text-[9px] text-muted-foreground uppercase mb-2">Economic Impact</p>
              <p className="text-xs text-emerald-300 leading-relaxed">{data.original_metrics.economic_impact.slice(0, 150)}...</p>
            </div>
            <div>
              <p className="text-[9px] text-muted-foreground uppercase mb-2">Social Impact</p>
              <p className="text-xs text-emerald-300 leading-relaxed">{data.original_metrics.social_impact.slice(0, 150)}...</p>
            </div>
          </div>
        </GlowCard>

        <GlowCard hoverable={false} className="p-10 bg-secondary/10 border-emerald-500/30">
          <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-400 mb-6 font-bold">✨ Improved Policy Benefits</p>
          <div className="space-y-4">
            <div>
              <p className="text-[9px] text-muted-foreground uppercase mb-2">Economic Impact</p>
              <p className="text-xs text-emerald-300 leading-relaxed">{data.improved_metrics.economic_impact.slice(0, 150)}...</p>
            </div>
            <div>
              <p className="text-[9px] text-muted-foreground uppercase mb-2">Social Impact</p>
              <p className="text-xs text-emerald-300 leading-relaxed">{data.improved_metrics.social_impact.slice(0, 150)}...</p>
            </div>
          </div>
        </GlowCard>
      </div>
    </div>
  );
};

export default ComparePage;
