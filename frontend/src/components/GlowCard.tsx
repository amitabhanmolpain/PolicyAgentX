import { motion } from "framer-motion";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface GlowCardProps {
  children: ReactNode;
  className?: string;
  glowColor?: "blue" | "violet" | "cyan" | "green" | "red";
  delay?: number;
  hoverable?: boolean;
}

const glowMap = {
  blue: "glow-blue",
  violet: "glow-violet",
  cyan: "glow-cyan",
  green: "glow-green",
  red: "glow-red",
};

const GlowCard = ({ children, className, glowColor = "blue", delay = 0, hoverable = true }: GlowCardProps) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay, ease: "easeOut" }}
    whileHover={hoverable ? { y: -4 } : undefined}
    className={cn(
      "glass rounded-2xl p-8 transition-all duration-300",
      hoverable && "hover:glow-card-hover hover:border-white/20",
      className
    )}
  >
    {children}
  </motion.div>
);


export default GlowCard;
