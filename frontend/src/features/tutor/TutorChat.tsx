import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { Citation, TutorAnswer } from "@/api/schemas";
import type { ChatMessage } from "./types";
import { MessageItem } from "./MessageItem";
import { SourceDrawer } from "./SourceDrawer";
import { Button } from "@/shared/ui/Button";
import {
  ArrowUp,
  BookOpen,
  Compass,
  CornerDownLeft,
  RotateCcw,
  Sparkles,
} from "lucide-react";

const STARTERS = [
  {
    label: "Why is Ensemble Learning the weak prerequisite for Gradient Boosting?",
    prompt: "Why is Ensemble Learning considered the weak prerequisite for Gradient Boosting in my notes?",
  },
  {
    label: "How do residuals act as the training signal in boosting?",
    prompt: "How do residuals act as the training signal in gradient boosting?",
  },
  {
    label: "Why keep trees shallow?",
    prompt: "Why are individual trees kept shallow in gradient boosting?",
  },
  {
    label: "Test ungrounded query (quantum physics)",
    prompt: "What does quantum annealing have to do with decision trees?",
  },
];

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: "welcome-1",
    sender: "tutor",
    text: "Welcome to your MindGenome Grounded Tutor. Unlike generic AI chatbots, every answer I provide is strictly tethered to the documents and papers you uploaded, verified through your Knowledge Graph.\n\nAsk me about concepts in your syllabus or select an exploration starter below.",
    timestamp: "Just now",
    grounded: true,
    confidence: "high",
    followups: [
      "Explain how gradient boosting fits residuals",
      "Why is ensemble learning a prerequisite?",
    ],
  },
];

export function TutorChat({ initialPrompt }: { initialPrompt?: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState(initialPrompt ?? "");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  // Focus input on load
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const askMutation = useMutation({
    mutationFn: (question: string) =>
      apiFetch<TutorAnswer>("/tutor/ask", {
        method: "POST",
        body: JSON.stringify({ question }),
      }),
    onMutate: (question) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        sender: "user",
        text: question,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
    },
    onSuccess: (data) => {
      // Simulate progressive token stream for a realistic AI feel
      const fullText = data.message;
      const chunks = fullText.split(" ");
      let currentText = "";
      let index = 0;

      const tutorMsgId = crypto.randomUUID();
      const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      // Add empty tutor message first
      setMessages((prev) => [
        ...prev,
        {
          id: tutorMsgId,
          sender: "tutor",
          text: "",
          timestamp,
          grounded: data.grounded,
          confidence: data.confidence,
          citations: data.citations,
          conceptIds: data.concept_ids,
          followups: data.followups,
        },
      ]);

      const interval = setInterval(() => {
        if (index < chunks.length) {
          currentText += (index > 0 ? " " : "") + chunks[index];
          index += 1;
          setMessages((prev) =>
            prev.map((m) => (m.id === tutorMsgId ? { ...m, text: currentText } : m)),
          );
        } else {
          clearInterval(interval);
          setIsStreaming(false);
        }
      }, 25);
    },
    onError: () => {
      setIsStreaming(false);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          sender: "tutor",
          text: "I encountered a communication error reaching the grounded RAG service. Please verify your connection or try again.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          grounded: false,
          confidence: "low",
        },
      ]);
    },
  });

  const handleSend = (textToSend?: string) => {
    const q = (textToSend ?? input).trim();
    if (!q || askMutation.isPending || isStreaming) return;
    setInput("");
    askMutation.mutate(q);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleOpenCitation = (c: Citation) => {
    setSelectedCitation(c);
    setDrawerOpen(true);
  };

  const handleClearHistory = () => {
    setMessages(INITIAL_MESSAGES);
  };

  return (
    <div className="flex h-full flex-col justify-between overflow-hidden rounded-card border border-line bg-canvas shadow-card">
      {/* Chat Sub-Header */}
      <div className="flex items-center justify-between border-b border-line bg-surface px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-control bg-helix/10 text-helix">
            <BookOpen className="h-4 w-4" />
          </div>
          <div>
            <span className="font-display text-sm font-bold block text-ink">
              MindGenome RAG Tutor
            </span>
            <span className="text-[11px] text-muted flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Source-Grounded Active • 1 Verified Document Ingested
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            className="text-xs text-muted hover:text-ink"
            onClick={handleClearHistory}
            title="Clear chat history"
          >
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reset Chat
          </Button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6"
        role="log"
        aria-live="polite"
      >
        {messages.map((m) => (
          <MessageItem
            key={m.id}
            message={m}
            onOpenCitation={handleOpenCitation}
            onSelectFollowup={(q) => handleSend(q)}
          />
        ))}

        {/* Loading Indicator when waiting for initial response */}
        {askMutation.isPending && !isStreaming && (
          <div className="flex gap-3 text-sm">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-helix/10 text-helix border border-helix/30">
              <Sparkles className="h-4 w-4 animate-spin" />
            </div>
            <div className="rounded-2xl rounded-tl-none border border-line bg-surface p-4 text-xs text-muted">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-helix animate-ping" />
                <span>Searching vector chunks and verifying knowledge graph grounding…</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Prompts Starters */}
      {messages.length <= 2 && (
        <div className="border-t border-line bg-surface/50 p-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5 mb-2.5">
            <Compass className="h-3.5 w-3.5 text-copper" />
            Quick Exploration Inquiries:
          </span>
          <div className="grid gap-2 sm:grid-cols-2">
            {STARTERS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(s.prompt)}
                disabled={askMutation.isPending || isStreaming}
                className="flex items-center justify-between rounded-control border border-line bg-surface p-2.5 text-left text-xs text-ink hover:border-helix hover:bg-helix/5 transition-all shadow-2xs"
              >
                <span className="font-medium line-clamp-1">{s.label}</span>
                <CornerDownLeft className="h-3.5 w-3.5 text-muted shrink-0 ml-2" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <div className="border-t border-line bg-surface p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-end rounded-control border border-line bg-canvas focus-within:border-helix focus-within:ring-1 focus-within:ring-helix"
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything grounded in your uploaded documents… (Enter to send)"
            className="w-full resize-none border-0 bg-transparent py-3 pl-4 pr-12 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-0 max-h-32 min-h-[44px]"
            disabled={askMutation.isPending || isStreaming}
          />
          <div className="absolute right-2.5 bottom-2">
            <Button
              type="submit"
              variant="primary"
              disabled={!input.trim() || askMutation.isPending || isStreaming}
              className="h-8 w-8 p-0 rounded-full flex items-center justify-center"
              aria-label="Send message"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          </div>
        </form>
        <div className="mt-2 flex items-center justify-between text-[11px] text-muted px-1">
          <span>Enter to submit • Shift+Enter for newline</span>
          <span className="font-mono">RAG Vector Verification Active</span>
        </div>
      </div>

      {/* Source Preview Drawer Dialog */}
      <SourceDrawer
        citation={selectedCitation}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </div>
  );
}
