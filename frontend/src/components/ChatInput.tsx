import React, { useState, useEffect, useRef } from "react";
import { Send } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import UploadButton from "./UploadButton";
import { cn } from "@/lib/utils";

const placeholders = [
  "Increase fuel tax by 5% in Karnataka for 12 months",
  "Subsidy on agriculture by 10% in India",
  "Reduce GST by 2% for 6 months",
];

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [value, setValue] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (value.trim() && !isLoading) {
      onSendMessage(value.trim());
      setValue("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex-none p-4 md:p-8 pt-0 w-full max-w-4xl mx-auto">
      <div 
        className={cn(
          "relative bg-secondary/80 border-border border rounded-3xl p-3 pt-4 transition-all duration-300",
          isFocused ? "shadow-[0_0_20px_rgba(255,255,255,0.05)] border-accent/60 bg-secondary" : "shadow-xl"
        )}
      >
        <div className="relative">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            rows={2}
            className="w-full bg-transparent border-none focus-visible:ring-0 focus-visible:ring-offset-0 text-white placeholder-transparent resize-none py-1 px-4 leading-relaxed font-light"
          />
          
          <AnimatePresence mode="wait">
            {!value && (
              <motion.div
                key={placeholderIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 0.4, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.5 }}
                className="absolute inset-x-0 top-1 left-4 pointer-events-none text-muted-foreground text-sm font-light select-none whitespace-nowrap overflow-hidden text-ellipsis"
              >
                {placeholders[placeholderIndex]}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center justify-between mt-3 px-2">
          <div className="flex items-center gap-1">
            <UploadButton disabled={isLoading} />
            <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold ml-2">PDF Enabled</span>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!value.trim() || isLoading}
            size="icon"
            className={cn(
              "rounded-xl w-10 h-10 transition-all duration-300", 
              value.trim() ? "bg-accent hover:bg-accent/80 text-white scale-100" : "bg-secondary text-muted-foreground scale-95 opacity-50"
            )}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
      <p className="text-center text-[10px] text-muted-foreground mt-4 uppercase tracking-[0.2em] font-semibold opacity-50">
        AI ASSISTANT POWERED BY POLICYAGENTX CORE
      </p>
    </div>
  );
};

export default ChatInput;
