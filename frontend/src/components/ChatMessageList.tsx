import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatMessageListProps {
  messages: Message[];
  loading?: boolean;
}

const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages, loading }) => {
  return (
    <div className="flex flex-col gap-6 py-4">
      <AnimatePresence initial={false}>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.3 }}
            className={cn(
              "flex w-full mb-2",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div className={cn(
              "flex items-start gap-3 md:gap-4 max-w-[85%] md:max-w-[70%]",
              message.role === "user" ? "flex-row-reverse" : "flex-row"
            )}>
              <Avatar className="w-8 h-8 border border-border mt-0.5 shrink-0">
                <AvatarFallback className={cn(
                  "text-[10px] font-bold",
                  message.role === "user" ? "bg-accent text-white" : "bg-card text-muted-foreground"
                )}>
                  {message.role === "user" ? "U" : "AI"}
                </AvatarFallback>
              </Avatar>
              
              <div className={cn(
                "rounded-2xl px-5 py-3 shadow-sm transition-all duration-300",
                message.role === "user" 
                  ? "bg-accent/15 border border-accent/30 text-white rounded-tr-none hover:bg-accent/20" 
                  : "bg-card/80 backdrop-blur-md border border-border text-secondary-foreground rounded-tl-none shadow-md hover:bg-card"
              )}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          </motion.div>
        ))}
        
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-4"
          >
            <Avatar className="w-8 h-8 border border-border mt-0.5">
              <AvatarFallback className="text-[10px] font-bold bg-card text-muted-foreground">AI</AvatarFallback>
            </Avatar>
            <div className="bg-card border border-border rounded-2xl px-5 py-4 rounded-tl-none shadow-md">
              <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                    className="w-1.5 h-1.5 bg-muted-foreground rounded-full"
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatMessageList;
