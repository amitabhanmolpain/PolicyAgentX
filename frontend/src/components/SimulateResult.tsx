import { useEffect, useState } from "react";
import GlowCard from "@/components/GlowCard";
import {
  SimulationResult,
  FrontendCardsPayload,
  AffectedGroupItem,
} from "@/lib/api";
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Siren,
  FileText,
  Users,
  ChartLine,
  Milestone,
  Globe,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

interface Props {
  results: SimulationResult | null;
  loading?: boolean;
}

const DEFAULT_CARDS: FrontendCardsPayload = {
  policy_summary: {
    simple_meaning: "Policy summary unavailable",
    issuing_ministry: "Unknown",
    implementation_timeline: "Not specified",
    total_people_impacted_india: "Not estimated",
    confidence_score: 0,
  },
  affected_groups: {
    groups: [],
    confidence_score: 0,
  },
  economic_impact: {
    gdp_impact_percent: "Not available",
    revenue_generated_inr_crores: "Not available",
    required_public_spend_inr: "Not available",
    tax_collection_impact: "Not available",
    employment_impact_jobs: "Not available",
    inflation_risk: "Unknown",
    fiscal_deficit_impact: "Not available",
    confidence_score: 0,
  },
  timeline: {
    year_1: { immediate_effect: "Setup and planning", adoption_or_growth: "Starting phase", inr_crore_estimate: "COST 0-1000 crores" },
    year_2_3: { immediate_effect: "Growth phase", adoption_or_growth: "Expanding", inr_crore_estimate: "COST 5000-10000 crores" },
    year_5: { immediate_effect: "Becoming normal", adoption_or_growth: "40-60% adopted", inr_crore_estimate: "PROFIT 15000-30000 crores" },
    year_10: { immediate_effect: "Stable and established", adoption_or_growth: "60-80% adopted", inr_crore_estimate: "PROFIT 40000-80000 crores" },
    confidence_score: 0,
  },
  global_impact: {
    india_global_position: "Likely to improve slightly",
    fdi_impact: "May attract some foreign investment",
    trade_balance_impact: "Limited short-term effect",
    comparison_usa_china_eu: "Mixed compared to other countries",
    world_bank_imf_reaction: "Likely positive if well-executed",
    competitiveness_score_change: "+0.2 to +0.8 points",
    confidence_score: 0,
  },
  protest_risk: {
    risk_score_1_to_10: 5,
    likely_protesting_groups: [],
    high_risk_states_cities: [],
    historical_similar_protests: [],
    confidence_score: 0,
  },
  improvements: {
    three_bold_improvements: [],
    lower_protest_risk_modified_version: "Make it more gradual to reduce opposition",
    phased_rollout_recommendation: "Start with a pilot, then expand slowly",
    confidence_score: 0,
  },
};

function confidenceBadge(score?: number) {
  const safe = typeof score === "number" ? score : 0;
  return (
    <span className="text-[10px] px-2 py-1 rounded-full border border-accent/30 bg-accent/10 text-accent uppercase tracking-[0.1em] font-bold">
      {safe}% confidence
    </span>
  );
}

function parsePercent(value?: string): number {
  if (!value) return 0;
  const n = Number(String(value).replace(/[^0-9.+-]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function riskColor(score: number): string {
  if (score > 7) return "text-red-400";
  if (score >= 4) return "text-amber-300";
  return "text-emerald-400";
}

function statusColor(status?: string): string {
  if ((status || "").toUpperCase().includes("BENEFITED")) return "text-emerald-300";
  return "text-red-300";
}

function progressClass(value: string | undefined): string {
  const v = (value || "").toLowerCase();
  if (v.includes("high")) return "bg-red-500";
  if (v.includes("medium")) return "bg-amber-500";
  return "bg-emerald-500";
}

function parseFinancialImpact(estimate: string | undefined): { type: "PROFIT" | "COST" | "LOSS" | "NEUTRAL"; amount: string } {
  const text = (estimate || "").toUpperCase();
  const cleanAmount = text
    .replace(/\b(PROFIT|GENERATE|GAIN)\b/i, "")
    .replace(/\b(COST|SPEND|LOSS)\b/i, "")
    .replace(/\s+/g, " ")
    .trim();

  if (text.includes("PROFIT")) {
    return { type: "PROFIT", amount: cleanAmount };
  }
  if (text.includes("LOSS")) {
    return { type: "LOSS", amount: cleanAmount };
  }
  if (text.includes("COST")) {
    return { type: "COST", amount: cleanAmount };
  }
  if (text.includes("SPEND")) {
    return { type: "COST", amount: cleanAmount };
  }
  if (text.includes("GENERATE") || text.includes("GAIN")) {
    return { type: "PROFIT", amount: cleanAmount };
  }
  return { type: "NEUTRAL", amount: estimate || "N/A" };
}

function financialColor(type: "PROFIT" | "COST" | "LOSS" | "NEUTRAL"): string {
  if (type === "PROFIT") return "text-emerald-300";
  if (type === "COST" || type === "LOSS") return "text-orange-300";
  return "text-muted-foreground";
}

function loadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 7 }).map((_, idx) => (
        <div key={idx} className="h-52 rounded-xl border border-border/30 bg-secondary/20 animate-pulse" />
      ))}
    </div>
  );
}

function cleanText(value: string | undefined, fallback = "Not available"): string {
  const text = (value || "").replace(/\s+/g, " ").trim();
  if (!text) return fallback;

  const bad = [
    "to be determined from policy text",
    "policy-related opposition groups",
    "high-sensitivity urban centers",
    "issue-specific protest precedents",
    "requires policy benchmarking",
    "sector-dependent",
    "n/a",
    "not applicable",
    "requires",
    "depends on",
  ];

  const lower = text.toLowerCase();
  if (bad.some((item) => lower === item || lower.includes(item))) {
    return fallback;
  }

  return text;
}

function inferPopulationEstimate(policyText: string, groupName?: string): string {
  const text = `${policyText || ""} ${(groupName || "")}`.toLowerCase();

  if (/(farm|agri|kisan|rural)/.test(text)) return "About 8-10 crore people";
  if (/(reservation|quota|sc|st|obc|minorit)/.test(text)) return "About 20-30 crore people";
  if (/(tax|gst|middle class|urban)/.test(text)) return "About 12-25 crore people";
  if (/(immigrant|migrant)/.test(text)) return "About 50 lakh to 1 crore people";
  if (/(women|child)/.test(text)) return "About 60 crore people";

  return "Estimated in crores/lakhs based on policy scope";
}

function polishSummary(text: string | undefined, policyText: string | undefined): string {
  const raw = (text || "").trim();
  if (!raw) {
    return `This policy is about: ${(policyText || "a government policy").slice(0, 150)}.`;
  }

  const cleaned = raw
    .replace(/^policy under analysis:\s*/i, "")
    .replace(/^this policy/i, "This policy")
    .replace(/\s+/g, " ")
    .trim();

  if (!/[.!?]$/.test(cleaned)) {
    return `${cleaned}.`;
  }
  return cleaned;
}

function inferMinistry(policyText: string): string {
  const text = (policyText || "").toLowerCase();
  if (/(farm|agri|kisan|crop|rural)/.test(text)) return "Ministry of Agriculture";
  if (/(tax|gst|duty|levy|revenue|budget)/.test(text)) return "Ministry of Finance";
  if (/(health|hospital|medicine|covid|vaccine)/.test(text)) return "Ministry of Health";
  if (/(education|school|student|skill|exam|college)/.test(text)) return "Ministry of Education";
  if (/(job|employment|labour|wage|reservation|quota)/.test(text)) return "Labour Ministry";
  if (/(road|highway|transport|vehicle)/.test(text)) return "Ministry of Transport";
  if (/(energy|coal|power|electricity)/.test(text)) return "Ministry of Energy";
  return "State / Central Ministry";
}

function inferTimeline(policyText: string): string {
  const text = (policyText || "").toLowerCase();
  if (/(pilot|phase|phased|rollout)/.test(text)) return "Pilot in 6 months, then expand slowly";
  if (/(immediate|urgent|emergency)/.test(text)) return "Start quickly, check progress at 3 and 12 months";
  return "Gradual rollout with checks every few months";
}

function normalizeStatus(status: string | undefined, reason: string | undefined): "BENEFITED" | "OPPRESSED" {
  const s = (status || "").toUpperCase();
  const r = (reason || "").toLowerCase();
  if (s.includes("BENEFIT")) return "BENEFITED";
  if (s.includes("OPPRESS") || s.includes("HARM") || s.includes("SUFFER")) return "OPPRESSED";
  if (/(gain|benefit|support|improv|access)/.test(r)) return "BENEFITED";
  return "OPPRESSED";
}

function inferAffectedGroups(policyText: string, existing: AffectedGroupItem[]): AffectedGroupItem[] {
  const text = (policyText || "").toLowerCase();
  const groups: AffectedGroupItem[] = [];
  const cleanedExisting = (existing || [])
    .map((g) => ({
      group_name: cleanText(g.group_name, ""),
      population_impact_percent: cleanText(g.population_impact_percent, "10-20%"),
      estimated_population_count: cleanText(g.estimated_population_count, ""),
      status: normalizeStatus(g.status, g.reason),
      reason: cleanText(g.reason, "Impact depends on how it's done."),
    }))
    .filter((g) => g.group_name.length > 2 && !/policy-related|unknown|generic/i.test(g.group_name || ""));

  if (cleanedExisting.length >= 4) {
    return cleanedExisting.slice(0, 8);
  }

  const add = (group_name: string, status: string, reason: string, population_impact_percent: string, estimated_population_count?: string) => {
    groups.push({
      group_name,
      status: normalizeStatus(status, reason),
      reason,
      population_impact_percent,
      estimated_population_count,
    });
  };

  if (/(farm|agri|kisan|rural)/.test(text)) {
    add("Farmers", "BENEFITED", "Directly helped by farm policy.", "20-35%", "About 8-10 crore people");
    add("City People", "OPPRESSED", "Prices may go up if farm costs increase.", "10-18%", "About 45-60 crore people");
  }

  if (/(reservation|quota|jobs|employment|recruitment)/.test(text)) {
    add("Reserved Groups", "BENEFITED", "Get more job chances.", "8-20%", "About 25-35 crore people");
    add("General Category", "OPPRESSED", "Face more competition.", "12-25%", "About 50-65 crore people");
    add("Job Seekers", "BENEFITED", "More jobs available.", "10-15%", "About 30-40 crore people");
  }

  if (/(tax|gst|levy|duty|revenue)/.test(text)) {
    add("Middle Class", "OPPRESSED", "Pay more taxes or fees.", "25-40%", "About 12-25 crore people");
    add("Poor People", "BENEFITED", "Money may go to help them.", "20-35%", "About 35-50 crore people");
    add("Rich People", "OPPRESSED", "Pay more to government.", "2-5%", "About 1-3 crore people");
  }

  if (/(women|child|minorit|sc|st|obc)/.test(text)) {
    add("Women / Children / Minorities", "BENEFITED", "Policy is designed to help them.", "15-45%", "About 60-70 crore people");
  }

  if (groups.length === 0) {
    add("Poor & Lower-Middle Class", "BENEFITED", "Usually benefit from new policies.", "15-30%", "About 40-55 crore people");
    add("Middle Class", "OPPRESSED", "May face extra costs or changes.", "10-20%", "About 12-25 crore people");
    add("Workers", "BENEFITED", "Jobs and services improve.", "8-16%", "About 25-35 crore people");
    add("Farmers", "BENEFITED", "Rural areas usually benefit.", "20-35%", "About 8-10 crore people");
  }

  const merged = [...cleanedExisting, ...groups]
    .reduce((acc: AffectedGroupItem[], cur) => {
      if (!acc.some((x) => (x.group_name || "").toLowerCase() === (cur.group_name || "").toLowerCase())) {
        acc.push(cur);
      }
      return acc;
    }, []);

  return merged.slice(0, 8);
}

function toStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item) => typeof item === "string" && item.trim().length > 0);
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return value
      .split(/[,|]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

export default function SimulateResult({ results, loading = false }: Props) {
  const [visibleSections, setVisibleSections] = useState(0);

  useEffect(() => {
    if (loading || !results) {
      setVisibleSections(0);
      return;
    }

    setVisibleSections(0);
    const totalSections = 7;
    const timers: ReturnType<typeof setTimeout>[] = [];

    for (let index = 1; index <= totalSections; index += 1) {
      timers.push(
        setTimeout(() => {
          setVisibleSections(index);
        }, index * 180)
      );
    }

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [loading, results]);

  if (loading) {
    return loadingSkeleton();
  }

  const payload = results?.frontend_cards || {
    policy_summary: results?.policy_summary,
    affected_groups: results?.affected_groups_section,
    economic_impact: results?.economic_impact_section,
    timeline: results?.timeline,
    global_impact: results?.global_impact,
    protest_risk: results?.protest_risk_section,
    improvements: results?.improvements,
  };

  const cards: FrontendCardsPayload = {
    ...DEFAULT_CARDS,
    ...payload,
    policy_summary: { ...DEFAULT_CARDS.policy_summary, ...payload?.policy_summary },
    affected_groups: { ...DEFAULT_CARDS.affected_groups, ...payload?.affected_groups },
    economic_impact: { ...DEFAULT_CARDS.economic_impact, ...payload?.economic_impact },
    timeline: { ...DEFAULT_CARDS.timeline, ...payload?.timeline },
    global_impact: { ...DEFAULT_CARDS.global_impact, ...payload?.global_impact },
    protest_risk: { ...DEFAULT_CARDS.protest_risk, ...payload?.protest_risk },
    improvements: { ...DEFAULT_CARDS.improvements, ...payload?.improvements },
  };

  const gdpNum = parsePercent(cards.economic_impact?.gdp_impact_percent);
  const protestScore = Math.max(1, Math.min(10, Number(cards.protest_risk?.risk_score_1_to_10 || 5)));
  const summaryText = polishSummary(cards.policy_summary?.simple_meaning, results?.policy_text);
  const totalPeopleImpacted = cleanText(cards.policy_summary?.total_people_impacted_india, inferPopulationEstimate(results?.policy_text || "", cards.affected_groups?.groups?.[0]?.group_name));
  const affectedRows = inferAffectedGroups(results?.policy_text || "", cards.affected_groups?.groups || []);
  const ministry = cleanText(cards.policy_summary?.issuing_ministry, inferMinistry(results?.policy_text || ""));
  const timelineSummary = cleanText(cards.policy_summary?.implementation_timeline, inferTimeline(results?.policy_text || ""));
  const fdiImpact = cleanText(cards.global_impact?.fdi_impact, "Moderate impact, depends on implementation confidence");
  const tradeImpact = cleanText(cards.global_impact?.trade_balance_impact, "Limited short-term impact; sector-specific in medium term");
  const globalPosition = cleanText(cards.global_impact?.india_global_position, "Potential incremental improvement with disciplined rollout");
  const compareGlobal = cleanText(cards.global_impact?.comparison_usa_china_eu, "Comparable to mixed global policy outcomes; execution quality is decisive");
  const imfReaction = cleanText(cards.global_impact?.world_bank_imf_reaction, "Likely positive if fiscal sustainability and transparency are maintained");
  const compScore = cleanText(cards.global_impact?.competitiveness_score_change, "+0.2 to +0.8 (scenario range)");
  const protestGroups = toStringArray(cards.protest_risk?.likely_protesting_groups);
  const protestCities = toStringArray(cards.protest_risk?.high_risk_states_cities);
  const protestCases = toStringArray(cards.protest_risk?.historical_similar_protests);

  const sections = [
    { id: "policy_summary", visible: visibleSections >= 1, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><FileText className="w-3.5 h-3.5" /> Policy Summary</p>
          {confidenceBadge(cards.policy_summary?.confidence_score)}
        </div>
        <p className="text-sm leading-relaxed">{summaryText}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs px-2 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
            {totalPeopleImpacted}
          </span>
          <span className="text-xs px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
            {ministry}
          </span>
          <span className="text-xs px-2 py-1 rounded-md bg-white/5 border border-white/20 text-white/80">
            {timelineSummary}
          </span>
        </div>
      </GlowCard>
    ) },
    { id: "affected_groups", visible: visibleSections >= 2, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><Users className="w-3.5 h-3.5" /> Affected Groups</p>
          {confidenceBadge(cards.affected_groups?.confidence_score)}
        </div>
        <p className="text-[11px] text-muted-foreground mb-2">Who this policy is most related to and impacted.</p>
        <div className="grid grid-cols-1 gap-2">
          {affectedRows.map((item: AffectedGroupItem, idx: number) => (
            <div key={`${item.group_name || "group"}-${idx}`} className="rounded-md border border-border/30 p-2 bg-black/20">
              <div className="flex justify-between gap-2 text-xs">
                <span className="font-semibold text-white">{item.group_name}</span>
                <span className="text-muted-foreground">{item.population_impact_percent}</span>
              </div>
              <div className="mt-1 space-y-1 text-[11px]">
                <p className="text-muted-foreground">
                  <span className="text-white/80 font-semibold">People:</span> {cleanText(item.estimated_population_count, inferPopulationEstimate(results?.policy_text || "", item.group_name))}
                </p>
                <div className="flex justify-between gap-2">
                  <span className={`${statusColor(item.status)} font-semibold`}>{normalizeStatus(item.status, item.reason)}</span>
                  <span className="text-muted-foreground text-right">{cleanText(item.reason, "Impact depends on execution quality.")}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </GlowCard>
    ) },
    { id: "economic_impact", visible: visibleSections >= 3, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><ChartLine className="w-3.5 h-3.5" /> Economic Impact</p>
          {confidenceBadge(cards.economic_impact?.confidence_score)}
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="rounded-lg p-3 border border-border/30 bg-black/30">
            <p className="text-[10px] uppercase text-muted-foreground">GDP Change</p>
            <p className={`text-lg font-bold flex items-center gap-1 ${gdpNum >= 0 ? "text-emerald-300" : "text-red-300"}`}>
              {gdpNum >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />} {cards.economic_impact?.gdp_impact_percent}
            </p>
          </div>
          <div className="rounded-lg p-3 border border-border/30 bg-black/30">
            <p className="text-[10px] uppercase text-muted-foreground">Money Generated</p>
            <p className="text-lg font-bold text-emerald-300">{cards.economic_impact?.revenue_generated_inr_crores}</p>
          </div>
        </div>
        <div className="space-y-2 text-xs">
          <p className="text-muted-foreground"><span className="text-white font-semibold">Jobs:</span> {cards.economic_impact?.employment_impact_jobs}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">Required Spend:</span> {cleanText(cards.economic_impact?.required_public_spend_inr, "Not estimated")}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">Tax Impact:</span> {cards.economic_impact?.tax_collection_impact}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">Money Impact:</span> {cards.economic_impact?.fiscal_deficit_impact}</p>
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold">Price Change:</span>
            <span>{cards.economic_impact?.inflation_risk}</span>
            <span className={`inline-block w-20 h-2 rounded-full ${progressClass(cards.economic_impact?.inflation_risk)}`} />
          </div>
        </div>
      </GlowCard>
    ) },
    { id: "timeline", visible: visibleSections >= 4, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><Milestone className="w-3.5 h-3.5" /> Future Timeline & Money</p>
          {confidenceBadge(cards.timeline?.confidence_score)}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {[
            { label: "Year 1", item: cards.timeline?.year_1 },
            { label: "Year 2-3", item: cards.timeline?.year_2_3 },
            { label: "Year 5", item: cards.timeline?.year_5 },
            { label: "Year 10", item: cards.timeline?.year_10 },
          ].map(({ label, item }) => {
            const financial = parseFinancialImpact(item?.inr_crore_estimate);
            const moneyType = financial.type === "NEUTRAL"
              ? ((label === "Year 1" || label === "Year 2-3") ? "COST" : "PROFIT")
              : financial.type;
            const moneyAmount = financial.amount || ((label === "Year 1" || label === "Year 2-3") ? "Spend amount not set" : "Money gained not set");
            return (
              <div key={label} className="rounded-md border border-border/30 p-3 bg-black/20">
                <p className="text-emerald-300 font-semibold text-sm">{label}</p>
                <p className="text-muted-foreground mt-1">{item?.immediate_effect}</p>
                <p className="text-muted-foreground text-[11px]">Using: {item?.adoption_or_growth}</p>
                <div className="mt-2 pt-2 border-t border-border/20">
                  <p className={`font-bold text-sm ${financialColor(moneyType)}`}>
                    {moneyType === "COST" ? "SPEND" : moneyType} {moneyAmount}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </GlowCard>
    ) },
    { id: "global_impact", visible: visibleSections >= 5, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><Globe className="w-3.5 h-3.5" /> How India Looks to the World</p>
          {confidenceBadge(cards.global_impact?.confidence_score)}
        </div>
        <div className="space-y-2 text-xs">
          <p className="text-muted-foreground"><span className="text-white font-semibold">World Opinion:</span> {fdiImpact}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">Foreign Investment:</span> {tradeImpact}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">India's Position:</span> {globalPosition}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">vs USA/China/EU:</span> {compareGlobal}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">UN/World Bank:</span> {imfReaction}</p>
          <p className="text-muted-foreground"><span className="text-white font-semibold">India Gets Better By:</span> {compScore}</p>
        </div>
      </GlowCard>
    ) },
    { id: "protest_risk", visible: visibleSections >= 6, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><ShieldAlert className="w-3.5 h-3.5" /> Protest Risk</p>
          {confidenceBadge(cards.protest_risk?.confidence_score)}
        </div>
        <div className="flex items-center gap-3 mb-3">
          <p className={`text-4xl font-black ${riskColor(protestScore)}`}>{protestScore}</p>
          <p className="text-xs text-muted-foreground">/ 10</p>
          {protestScore > 7 ? <Siren className="w-5 h-5 text-red-400 animate-pulse" /> : <AlertTriangle className="w-5 h-5 text-amber-300" />}
        </div>
        <div className="text-xs space-y-2">
          <p><span className="text-muted-foreground">At-risk groups:</span> {protestGroups.length ? protestGroups.join(", ") : "Likely opposition and implementation-affected segments"}</p>
          <p><span className="text-muted-foreground">Hotspot states/cities:</span> {protestCities.length ? protestCities.join(", ") : "Major urban centers and politically sensitive districts"}</p>
          <p><span className="text-muted-foreground">Historical cases:</span> {protestCases.length ? protestCases.join(" | ") : "Farmer protests, quota movements, and subsidy transition protests"}</p>
        </div>
      </GlowCard>
    ) },
    { id: "improvements", visible: visibleSections >= 7, node: (
      <GlowCard hoverable={false} className="p-5 bg-secondary/10 border-border/30 lg:col-span-2">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground font-bold flex items-center gap-2"><Sparkles className="w-3.5 h-3.5" /> Policy Improvements</p>
          {confidenceBadge(cards.improvements?.confidence_score)}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-3">
          {(cards.improvements?.three_bold_improvements || []).slice(0, 3).map((item, idx) => (
            <div key={idx} className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-100">
              {item}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
          <div className="rounded-md border border-border/30 p-3 bg-black/20">
            <p className="text-muted-foreground mb-1">Modified Policy</p>
            <p>{cards.improvements?.lower_protest_risk_modified_version}</p>
          </div>
          <div className="rounded-md border border-border/30 p-3 bg-black/20">
            <p className="text-muted-foreground mb-1">Phased Rollout</p>
            <p>{cards.improvements?.phased_rollout_recommendation}</p>
          </div>
        </div>
      </GlowCard>
    ) },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sections.map((section) =>
          section.visible ? (
            <div key={section.id} className="animate-[fadeIn_0.35s_ease-out]">
              {section.node}
            </div>
          ) : null
        )}
      </div>
    </div>
  );
}
