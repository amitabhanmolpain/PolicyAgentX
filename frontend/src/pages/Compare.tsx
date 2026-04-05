import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import GlowCard from "@/components/GlowCard";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

import { Award, Loader, AlertCircle, AlertTriangle } from "lucide-react";
import { getHistory, improvePolicy, simulatePolicy, FrontendCardsPayload } from "@/lib/api";
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
  improved_policy_name?: string;
  original_metrics: PolicyMetrics;
  improved_metrics: PolicyMetrics;
  improvements: {
    gdp_improvement: number;
    employment_improvement: number;
    inflation_improvement: number;
    sentiment_improvement: number;
  };
  innovation_blocks?: InnovationBlock[];
  improved_policy_points?: string[];
  original_policy_cons?: string[];
  original_summary?: string;
  improved_summary?: string;
  gemini_error?: string | null;
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

const normalizeDisplayText = (text: string): string => {
  return (text || "").replace(/_/g, " ").replace(/\s+/g, " ").trim();
};

const isControversialPolicy = (text: string): boolean => {
  const controversialKeywords = [
    "removal", "expulsion", "ban", "discriminat", "religion", "communal", "riot", "violence",
    "caste", "hindu", "muslim", "christian", "sikh", "buddha", "jew", "minority", "majority",
    "ethnic", "racial", "persecution", "genocide", "massacre", "pogrom", "cleansing",
    "sectarian", "religious hatred", "religious conflict", "communal violence", "riots",
    "targeted killing", "targeted attack", "religious targeting", "faith-based discrimination",
    "anti-semitism", "islamophobia", "hinduphobia", "christianophobia", "religious intolerance"
  ];
  
  const lower = (text || "").toLowerCase();
  return controversialKeywords.some(keyword => lower.includes(keyword));
};

const getDisruptionRiskAssessment = (policy: string, metrics: PolicyMetrics): { riskLevel: "critical" | "high" | "medium" | "low"; reasons: string[] } => {
  const risks: string[] = [];
  let riskLevel: "critical" | "high" | "medium" | "low" = "low";

  if (isControversialPolicy(policy)) {
    riskLevel = "critical";
    risks.push("Contains controversial language that can trigger communal violence or riots.");
  }

  if (metrics.sentiment_score < 30) {
    if (riskLevel === "low") riskLevel = "high";
    risks.push("Extremely negative public sentiment—high risk of mass protest and social unrest.");
  } else if (metrics.sentiment_score < 50) {
    if (riskLevel === "low") riskLevel = "medium";
    risks.push("Low public sentiment—may trigger resistance and community backlash.");
  }

  if (metrics.employment_change < -5) {
    if (riskLevel === "low") riskLevel = "medium";
    risks.push("Severe job losses could spark labor strikes and economic disruption.");
  }

  if (metrics.inflation_impact > 3) {
    if (riskLevel === "low") riskLevel = "medium";
    risks.push("High inflation may cause public anger over cost-of-living increases.");
  }

  return { riskLevel, reasons: risks.length > 0 ? risks : ["Policy appears stable with manageable implementation risk."] };
};

type InnovationBlock = {
  original: string;
  upgrade: string;
  benefit: string;
};

const getDynamicBenefitText = (upgrade: string, metrics: PolicyMetrics): string => {
  const normalized = normalizeDisplayText(upgrade).toLowerCase();
  const reasons: string[] = [];

  if (/(target|eligib|focus|segment|prioriti)/.test(normalized)) {
    reasons.push("Improves targeting so benefits reach the intended group.");
  }
  if (/(monitor|track|audit|review|dashboard|compliance|verification)/.test(normalized)) {
    reasons.push("Adds accountability through measurable tracking and verification.");
  }
  if (/(digital|online|portal|platform|data|ai|automation)/.test(normalized)) {
    reasons.push("Improves delivery speed and reduces manual leakage.");
  }
  if (/(local|district|state|community|panchayat|municipal|decentral)/.test(normalized)) {
    reasons.push("Strengthens local implementation and adoption.");
  }

  if (metrics.sentiment_score >= 65) {
    reasons.push("Supports stronger public trust and acceptance.");
  }
  if (metrics.gdp_growth >= 1) {
    reasons.push("Improves macroeconomic upside versus the baseline.");
  }
  if (metrics.inflation_impact <= 0.5) {
    reasons.push("Helps keep inflation pressure under control.");
  }

  if (reasons.length > 0) {
    return reasons.slice(0, 2).join(" ");
  }

  return "Provides a clearer execution path with better outcomes than the baseline policy.";
};

const getSafeguardRecommendations = (improvedPolicy: string, originalPolicy: string, metrics: PolicyMetrics): { safeguards: string[]; exclusions: string[]; hasResidualRisk: boolean } => {
  const safeguards: string[] = [];
  const exclusions: string[] = [];
  let hasResidualRisk = false;

  // If original policy is controversial, add specific exclusions for improved version
  if (isControversialPolicy(originalPolicy)) {
    hasResidualRisk = isControversialPolicy(improvedPolicy);
    
    if (!hasResidualRisk) {
      exclusions.push("DO NOT revert to targeting, discriminating, or removing any religious/ethnic group.");
      exclusions.push("DO NOT include any language about communal segregation or majoritarian policies.");
      exclusions.push("DO NOT allow implementation without external oversight from minority rights bodies.");
    } else {
      exclusions.push("The improved policy STILL contains contentious language—seek legal review before implementation.");
      safeguards.push("Mandate third-party audit by constitutional experts before rollout.");
    }
  }

  // Safeguards based on metrics
  if (metrics.sentiment_score < 50) {
    safeguards.push("Conduct broad stakeholder consultation and public awareness campaigns before launch.");
    if (!exclusions.includes("Ensure transparent cost-benefit analysis is published publicly.")) {
      safeguards.push("Ensure transparent cost-benefit analysis is published publicly.");
    }
  }

  if (metrics.employment_change < -2) {
    exclusions.push("DO NOT implement without a parallel job retraining and transition support program.");
    safeguards.push("Package with labor market adjustment schemes to protect workers.");
  }

  if (metrics.inflation_impact > 2) {
    exclusions.push("DO NOT phase out existing support schemes simultaneously—stagger implementation.");
    safeguards.push("Monitor inflation weekly and adjust implementation pace to prevent price shocks.");
  }

  if (metrics.gdp_growth < 0.5) {
    safeguards.push("Build in performance review at 6-month and 12-month milestones; adjust if targets aren't met.");
    exclusions.push("DO NOT commit to multi-year implementation without interim performance gates.");
  }

  if (metrics.sentiment_score >= 75 && metrics.gdp_growth >= 2) {
    safeguards.push("This policy has strong public and economic support—fast-track implementation is viable.");
  }

  // Remove duplicates
  const uniqueSafeguards = Array.from(new Set(safeguards));
  const uniqueExclusions = Array.from(new Set(exclusions));

  return {
    safeguards: uniqueSafeguards.slice(0, 3),
    exclusions: uniqueExclusions.slice(0, 3),
    hasResidualRisk,
  };
};

const getInnovationBlocks = (originalText: string, improvedText: string, metrics: PolicyMetrics): InnovationBlock[] => {
  const lines = sanitizeText(improvedText)
    .split(/\n+/)
    .map((line) => line.replace(/^\s*[-*#>\d.)]+\s*/, "").trim())
    .filter((line) => line.length > 25);

  const blocks: InnovationBlock[] = [];
  let current: InnovationBlock | null = null;

  for (const line of lines) {
    const originalMatch = line.match(/^Original\s*:\s*(.+)$/i);
    const upgradeMatch = line.match(/^Upgrade\s*:\s*(.+)$/i);
    const benefitMatch = line.match(/^Benefit\s*:\s*(.+)$/i);

    if (originalMatch) {
      if (current && (current.original || current.upgrade || current.benefit)) {
        blocks.push(current);
      }
      current = {
        original: normalizeDisplayText(originalMatch[1]),
        upgrade: "",
        benefit: "",
      };
      continue;
    }

    if (upgradeMatch && current) {
      current.upgrade = normalizeDisplayText(upgradeMatch[1]);
      continue;
    }

    if (benefitMatch && current) {
      current.benefit = normalizeDisplayText(benefitMatch[1]);
      continue;
    }

    if (/^policy name\s*:/i.test(line) || /^execution blueprint\s*:/i.test(line) || /^expected measurable outcomes\s*:/i.test(line) || /^tech\/ai edge\s*:/i.test(line)) {
      continue;
    }

    if (current && !current.upgrade) {
      current.upgrade = normalizeDisplayText(line);
    } else if (current && !current.benefit) {
      current.benefit = normalizeDisplayText(line);
    }
  }

  if (current && (current.original || current.upgrade || current.benefit)) {
    blocks.push(current);
  }

  const parsed = blocks
    .map((block) => ({
      original: block.original,
      upgrade: block.upgrade,
      benefit: block.benefit || getDynamicBenefitText(block.upgrade, metrics),
    }))
    .filter((block) => block.upgrade.length > 0)
    .slice(0, 3);

  if (parsed.length > 0) {
    return parsed;
  }

  const originalPoints = toPolicyPoints(originalText);
  const improvedPoints = toPolicyPoints(improvedText);
  const maxCount = Math.max(1, Math.min(3, Math.max(originalPoints.length, improvedPoints.length)));

  return Array.from({ length: maxCount }).map((_, index) => {
    const sourceOriginal = originalPoints[index] || originalPoints[0] || normalizeDisplayText(toSimplePolicySummary(originalText));
    const sourceUpgrade = improvedPoints[index] || improvedPoints[0] || normalizeDisplayText(toSimplePolicySummary(improvedText));

    return {
      original: normalizeDisplayText(sourceOriginal),
      upgrade: normalizeDisplayText(sourceUpgrade),
      benefit: getDynamicBenefitText(sourceUpgrade, metrics),
    };
  });
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

  const unique = Array.from(new Set(extracted.map(simplifyCriticalCons))).slice(0, 5);
  if (unique.length > 0) {
    return unique;
  }

  const fallback: string[] = [];
  if (metrics.inflation_impact > 0) {
    fallback.push("Prices can rise and hurt poor families first.");
  }
  if (metrics.employment_change < 0.5) {
    fallback.push("Jobs can fall or stay flat in the affected sector.");
  }
  if (metrics.sentiment_score < 60) {
    fallback.push("People may not trust the policy if benefits are unclear.");
  }
  if (metrics.gdp_growth < 1) {
    fallback.push("The policy is too weak to create strong growth.");
  }

  return fallback.length > 0
    ? fallback
    : ["The policy is too weak and may not deliver real results."];
};

const renderInnovationText = (text: string): string => {
  return normalizeDisplayText(text || "No specific upgrade provided.");
};

const simplifyCriticalCons = (text: string): string => {
  const lower = normalizeDisplayText(text).toLowerCase();

  if (lower.includes("inflation")) return "Prices can rise and hurt poor families first.";
  if (lower.includes("employment") || lower.includes("job")) return "Jobs can fall in the affected sector.";
  if (lower.includes("small business") || lower.includes("msme") || lower.includes("business")) return "Small businesses can face higher costs and pressure.";
  if (lower.includes("farmer") || lower.includes("agricultur") || lower.includes("rural")) return "Farmers may still lose money if support is not targeted well.";
  if (lower.includes("inequality") || lower.includes("poor") || lower.includes("income")) return "Poor households may gain less than expected.";
  if (lower.includes("delay") || lower.includes("implementation")) return "Slow rollout can block real benefits.";
  if (lower.includes("leakage") || lower.includes("corruption") || lower.includes("middleman")) return "Money can leak before reaching the real beneficiary.";
  if (lower.includes("risk") || lower.includes("burden") || lower.includes("cost")) return "The policy can create extra cost without enough gain.";
  return "The policy is too weak and may not deliver real results.";
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
  const [sectionDiffLoading, setSectionDiffLoading] = useState(false);
  const [sectionDiff, setSectionDiff] = useState<{ original: FrontendCardsPayload; improved: FrontendCardsPayload } | null>(null);
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
        
        // Generate improved version with a longer timeout; backend compare can take time.
        const comparisonData = await improvePolicy(policyText, { timeoutMs: 420000 });
        setData(comparisonData);

        try {
          setSectionDiffLoading(true);
          const [originalSim, improvedSim] = await Promise.all([
            simulatePolicy({ text: policyText, region: "India" }),
            simulatePolicy({ text: comparisonData.improved_policy || policyText, region: "India" }),
          ]);
          setSectionDiff({
            original: (originalSim.frontend_cards || {}) as FrontendCardsPayload,
            improved: (improvedSim.frontend_cards || {}) as FrontendCardsPayload,
          });
        } catch (sectionErr) {
          console.error("Failed to fetch section diff data:", sectionErr);
        } finally {
          setSectionDiffLoading(false);
        }

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
            errorMessage = "Comparison is taking too long. Please retry in a moment, or simplify policy text for a faster run.";
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
  ) => {
    const disruption = getDisruptionRiskAssessment(policy, metrics);
    const riskBgColors = {
      critical: "bg-red-950/30 border-red-500/30",
      high: "bg-orange-950/30 border-orange-500/30",
      medium: "bg-amber-950/30 border-amber-500/30",
      low: "bg-green-950/30 border-green-500/30",
    };

    return (
    <GlowCard hoverable={false} className="relative p-10">
      {isRecommended && (
        <div className="absolute -top-3 left-10 flex items-center gap-2 px-4 py-1.5 rounded-full text-[10px] font-display font-bold uppercase tracking-[0.2em] bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]">
          <Award className="w-3 h-3" /> Recommended
        </div>
      )}
      {!isRecommended && disruption.riskLevel !== "low" && (
        <div className="absolute -top-3 right-10 flex items-center gap-1 px-3 py-1 rounded-full text-[8px] font-bold uppercase tracking-widest border border-red-500/40 bg-red-950/20">
          <span className="text-red-400">⚠️ {disruption.riskLevel.toUpperCase()} RISK</span>
        </div>
      )}
      <h3 className="text-xl font-display font-bold text-foreground mb-2 mt-2 tracking-tight">{label}</h3>
      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground mb-2 font-semibold">
          {isRecommended ? "What We Innovated And Why It Benefits" : "Original Policy Baseline"}
        </p>
        {isRecommended ? (
          <div className="space-y-4">
            {(data?.innovation_blocks && data.innovation_blocks.length > 0
              ? data.innovation_blocks
              : getInnovationBlocks(data?.original_policy || "", policy, metrics)
            ).map((block, idx) => (
              <div key={`${idx}-${block.original.slice(0, 20)}`} className="rounded-xl border border-border/30 bg-black/20 p-4 space-y-2">
                <p className="text-xs text-muted-foreground leading-relaxed"><span className="text-white font-semibold">Issue:</span> {renderInnovationText(block.original)}</p>
                <p className="text-xs text-white leading-relaxed"><span className="font-semibold">Fix:</span> {renderInnovationText(block.upgrade)}</p>
                <p className="text-xs text-cyan-300 leading-relaxed"><span className="font-semibold">Impact:</span> {renderInnovationText(block.why_it_wins)}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground leading-relaxed">{normalizeDisplayText(toSimplePolicySummary(policy))}</p>
            {disruption.riskLevel !== "low" && (
              <div className={`rounded-lg border p-3 ${riskBgColors[disruption.riskLevel]}`}>
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-400" />
                  <div className="text-xs space-y-1">
                    <p className="font-semibold text-white">Disruption Risk Alert</p>
                    {disruption.reasons.map((reason, idx) => (
                      <p key={idx} className="text-muted-foreground leading-relaxed">{reason}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
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
  };

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

  const improvedPolicyPoints = (data.improved_policy_points && data.improved_policy_points.length > 0)
    ? data.improved_policy_points.map((p) => normalizeDisplayText(p)).filter((p) => p.length > 10)
    : toPolicyPoints(data.improved_policy);
  const originalPolicyCons = (data.original_policy_cons && data.original_policy_cons.length > 0)
    ? data.original_policy_cons.map((c) => normalizeDisplayText(c)).filter((c) => c.length > 10)
    : getOriginalCons(data.original_metrics);
  const originalPolicyDisruption = getDisruptionRiskAssessment(data.original_policy, data.original_metrics);
  const hideImprovedPolicy = originalPolicyDisruption.riskLevel !== "low";

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

  const sectionKeys: Array<keyof FrontendCardsPayload> = [
    "policy_summary",
    "affected_groups",
    "economic_impact",
    "timeline",
    "global_impact",
    "protest_risk",
    "improvements",
  ];

  const sectionTitle = (key: keyof FrontendCardsPayload) => {
    return key.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
  };

  const hasChanged = (a: unknown, b: unknown) => {
    return JSON.stringify(a || {}) !== JSON.stringify(b || {});
  };

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
        {hideImprovedPolicy ? (
          <GlowCard hoverable={false} className="p-10 border-red-500/30 bg-red-950/10">
            <p className="text-[10px] uppercase tracking-[0.2em] text-red-300 mb-4 font-bold">Improved Policy Hidden</p>
            <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-4">
              <p className="text-sm text-red-200 font-semibold mb-2">Conflict Risk Detected</p>
              <p className="text-xs text-red-100 leading-relaxed mb-3">
                This policy may cause social conflict or unrest. Improved policy suggestions are intentionally withheld for safety.
              </p>
              <div className="space-y-1">
                {originalPolicyDisruption.reasons.slice(0, 3).map((reason, idx) => (
                  <p key={idx} className="text-xs text-red-200 leading-relaxed">{idx + 1}. {reason}</p>
                ))}
              </div>
            </div>
          </GlowCard>
        ) : (
          renderPolicyCard(
            data.improved_policy,
            data.improved_metrics,
            data.improved_policy_name || "Improved Policy",
            true
          )
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

      <GlowCard hoverable={false} className="p-8 mb-12 bg-secondary/10 border-border/20">
        <div className="flex items-center justify-between mb-6">
          <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">7-Section Side-by-Side Diff</p>
          {sectionDiffLoading && <span className="text-xs text-muted-foreground animate-pulse">Loading section diff...</span>}
        </div>

        {!sectionDiff && !sectionDiffLoading && (
          <p className="text-sm text-muted-foreground">Section diff unavailable for this run.</p>
        )}

        {sectionDiff && (
          <div className="space-y-4">
            {sectionKeys.map((key) => {
              const originalSection = sectionDiff.original?.[key] || {};
              const improvedSection = sectionDiff.improved?.[key] || {};
              const changed = hasChanged(originalSection, improvedSection);

              return (
                <div key={key} className={`rounded-lg border p-4 ${changed ? "border-emerald-500/40 bg-emerald-500/5" : "border-border/30 bg-black/10"}`}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs uppercase tracking-[0.15em] font-bold text-white">{sectionTitle(key)}</p>
                    {changed && <span className="text-[10px] text-emerald-300 uppercase tracking-[0.12em]">Changed</span>}
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                    <div className="rounded-md border border-border/25 bg-black/25 p-3">
                      <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground mb-2">Original</p>
                      <pre className="text-xs whitespace-pre-wrap break-words text-muted-foreground">{JSON.stringify(originalSection, null, 2)}</pre>
                    </div>
                    <div className={`rounded-md border p-3 ${changed ? "border-emerald-500/30 bg-emerald-500/10" : "border-border/25 bg-black/25"}`}>
                      <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground mb-2">Improved</p>
                      <pre className={`text-xs whitespace-pre-wrap break-words ${changed ? "text-emerald-200" : "text-muted-foreground"}`}>{JSON.stringify(improvedSection, null, 2)}</pre>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </GlowCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {!hideImprovedPolicy && (
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
        )}

        <GlowCard hoverable={false} className={`p-8 bg-secondary/10 border-rose-500/30 ${hideImprovedPolicy ? "md:col-span-2" : ""}`}>
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

      {!hideImprovedPolicy && (
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
      )}

      {/* Benefits Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <GlowCard hoverable={false} className="p-10 bg-secondary/10 border-border/20">
          <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-6 font-bold">Original Policy Impact</p>
          <div className="space-y-4">
            <div>
              <p className="text-[9px] text-muted-foreground uppercase mb-2">Economic Impact</p>
              <p className="text-xs text-emerald-300 leading-relaxed">
                {normalizeDisplayText(data.original_summary || data.original_metrics.economic_impact).slice(0, 220)}
              </p>
            </div>
            <div>
              <p className="text-[9px] text-muted-foreground uppercase mb-2">Social Impact</p>
              <p className="text-xs text-emerald-300 leading-relaxed">{normalizeDisplayText(data.original_metrics.social_impact).slice(0, 220)}</p>
            </div>
          </div>
        </GlowCard>

        {!hideImprovedPolicy && (
          <GlowCard hoverable={false} className="p-10 bg-secondary/10 border-emerald-500/30">
            <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-400 mb-6 font-bold">✨ Improved Policy Benefits</p>
            <div className="space-y-4">
              <div>
                <p className="text-[9px] text-muted-foreground uppercase mb-2">Economic Impact</p>
                <p className="text-xs text-emerald-300 leading-relaxed">
                  {normalizeDisplayText(data.improved_summary || data.improved_metrics.economic_impact).slice(0, 220)}
                </p>
              </div>
              <div>
                <p className="text-[9px] text-muted-foreground uppercase mb-2">Social Impact</p>
                <p className="text-xs text-emerald-300 leading-relaxed">{normalizeDisplayText(data.improved_metrics.social_impact).slice(0, 220)}</p>
              </div>
            </div>
          </GlowCard>
        )}
      </div>
    </div>
  );
};

export default ComparePage;
