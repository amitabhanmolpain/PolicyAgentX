import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, FileUp, RotateCcw, Sparkles } from "lucide-react";
import GlowCard from "@/components/GlowCard";
import ChatInput from "@/components/ChatInput";
import ChatMessageList from "@/components/ChatMessageList";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { chatWithRag, resetRagStore, uploadPDF } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const storageKeys = {
  messages: "policyagentx-rag-chat-messages",
  fileName: "policyagentx-rag-chat-file",
};

const introMessage: Message = {
  id: "rag-intro",
  role: "assistant",
  content: "Upload a PDF policy document, then ask questions about it. I’ll retrieve relevant chunks from ChromaDB and answer with Gemini.",
};

const RagChatPage = () => {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([introMessage]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  useEffect(() => {
    const savedMessages = localStorage.getItem(storageKeys.messages);
    const savedFileName = localStorage.getItem(storageKeys.fileName);

    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
        }
      } catch {
        setMessages([introMessage]);
      }
    }

    if (savedFileName) {
      setUploadedFileName(savedFileName);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(storageKeys.messages, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (uploadedFileName) {
      localStorage.setItem(storageKeys.fileName, uploadedFileName);
    } else {
      localStorage.removeItem(storageKeys.fileName);
    }
  }, [uploadedFileName]);

  const statusText = useMemo(() => {
    if (uploading) return "Indexing document into ChromaDB...";
    if (loading) return "Retrieving context and querying Gemini...";
    if (uploadedFileName) return `Indexed: ${uploadedFileName}`;
    return "Ready to ingest a PDF";
  }, [loading, uploading, uploadedFileName]);

  const pushAssistantMessage = (content: string) => {
    setMessages((prev) => prev.concat([{ id: `${Date.now()}-assistant`, role: "assistant", content }]));
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: Message = { id: `${Date.now()}-user`, role: "user", content: message };
    const pendingId = `${Date.now()}-pending`;

    setLoading(true);
    setMessages((prev) => prev.concat([userMessage, { id: pendingId, role: "assistant", content: "Searching the indexed document..." }]));

    try {
      const result = await chatWithRag({ question: message, top_k: 4 });
      setMessages((prev) => prev.filter((entry) => entry.id !== pendingId).concat([{ id: `${Date.now()}-answer`, role: "assistant", content: result.answer || "No answer returned." }]));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unable to answer the question.";
      setMessages((prev) => prev.filter((entry) => entry.id !== pendingId).concat([{ id: `${Date.now()}-error`, role: "assistant", content: `Error: ${errorMessage}` }]));
      toast({
        variant: "destructive",
        title: "Chat failed",
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const result = await uploadPDF(file);
      setUploadedFileName(result.filename || file.name);
      pushAssistantMessage(`Indexed ${result.chunks_indexed ?? 0} chunks from ${result.filename || file.name}. You can ask questions now.`);
      toast({
        title: "Document indexed",
        description: result.message || "PDF uploaded successfully.",
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Upload failed.";
      toast({
        variant: "destructive",
        title: "Upload failed",
        description: errorMessage,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleReset = async () => {
    try {
      const result = await resetRagStore();
      setMessages([introMessage]);
      setUploadedFileName(null);
      localStorage.removeItem(storageKeys.messages);
      localStorage.removeItem(storageKeys.fileName);
      toast({
        title: "Vector store reset",
        description: result.message,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Reset failed.";
      toast({
        variant: "destructive",
        title: "Reset failed",
        description: errorMessage,
      });
    }
  };

  const handleNewChat = () => {
    setMessages([introMessage]);
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-background">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_40%),radial-gradient(circle_at_20%_80%,rgba(14,165,233,0.18),transparent_25%),radial-gradient(circle_at_80%_20%,rgba(16,185,129,0.12),transparent_25%)]" />
      <div className="absolute inset-0 -z-10 opacity-[0.04] bg-[linear-gradient(transparent_0_95%,rgba(255,255,255,0.15)_95%)] bg-[length:100%_18px]" />

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 pb-40 pt-8 md:px-6">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col gap-4 rounded-3xl border border-border/60 bg-card/70 p-6 shadow-2xl backdrop-blur-xl md:flex-row md:items-center md:justify-between"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-accent" />
              <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">Policy Assistant</h1>
            </div>
            <p className="max-w-2xl text-sm text-muted-foreground">
              Upload a PDF, index it once in ChromaDB, then ask questions that are answered from retrieved document context through Gemini.
            </p>
            <div className="flex flex-wrap items-center gap-2 pt-1 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              <span className="rounded-full border border-border/60 bg-background/60 px-3 py-1">{statusText}</span>
              <span className="rounded-full border border-border/60 bg-background/60 px-3 py-1">{uploadedFileName ? "Document ready" : "No document indexed"}</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={handleNewChat} className="gap-2">
              <RotateCcw className="h-4 w-4" />
              New Chat
            </Button>
            <Button type="button" variant="outline" onClick={handleReset} className="gap-2 border-red-500/30 text-red-300 hover:bg-red-500/10 hover:text-red-200">
              <AlertCircle className="h-4 w-4" />
              Reset Index
            </Button>
          </div>
        </motion.div>

        <GlowCard hoverable={false} className="border border-border/60 bg-card/30 p-4 md:p-6">
          <ChatMessageList messages={messages} loading={loading || uploading} />
        </GlowCard>

        <AnimatePresence>
          {uploadedFileName && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
            >
              <GlowCard hoverable={false} className="flex items-center justify-between gap-4 border border-border/60 bg-card/50 px-4 py-3">
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <FileUp className="h-4 w-4 text-accent" />
                  <span>Indexed document: {uploadedFileName}</span>
                </div>
                <Button type="button" variant="ghost" size="sm" onClick={handleReset} className="text-xs uppercase tracking-[0.15em]">
                  Clear vector store
                </Button>
              </GlowCard>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-30 pointer-events-none">
        <div className="mx-auto w-full max-w-5xl px-4 pb-4 pointer-events-auto">
          <ChatInput onSendMessage={handleSendMessage} onUpload={handleUpload} isLoading={loading || uploading} />
        </div>
      </div>
    </div>
  );
};

export default RagChatPage;