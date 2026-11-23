import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import { ThemeToggle } from "@/app/shell/ThemeToggle";
import { useSession } from "@/features/auth/session";
import { apiFetch } from "@/api/client";
import type { TokenPair } from "@/api/schemas";
import { DEMO_EMAIL, DEMO_PASSWORD } from "@/mocks/seed";
import { motion, useReducedMotion } from "framer-motion";
import {
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  GitGraph,
  Layers,
  MessageSquare,
  Route,
  Sparkles,
  Upload,
} from "lucide-react";

const STEPS = [
  {
    n: "01",
    t: "Upload & Ingest",
    icon: Upload,
    d: "Drop ML papers and lecture notes. We parse, chunk, compute embeddings, and index semantic relationships.",
    tag: "Multi-file queue",
  },
  {
    n: "02",
    t: "Graph Synthesis",
    icon: GitGraph,
    d: "Concepts, chapters, and directed dependencies become an interactive semantic knowledge graph.",
    tag: "Cytoscape engine",
  },
  {
    n: "03",
    t: "Focused Learning",
    icon: Layers,
    d: "Study bite-sized micro-sections with inline explanations, avoiding overwhelming walls of chat text.",
    tag: "Progressive flow",
  },
  {
    n: "04",
    t: "Checkpoint Quizzes",
    icon: Brain,
    d: "Concept-tagged diagnostic questions verify true understanding with immediate explainable feedback.",
    tag: "Concept-grounded",
  },
  {
    n: "05",
    t: "Remediate & Adapt",
    icon: Route,
    d: "Scored 2/5 on Gradient Boosting? The graph diagnoses Ensemble Learning as the weak link and serves a remedy.",
    tag: "Prerequisite graph",
  },
];

const FEATURES = [
  {
    title: "Interactive Knowledge Graph",
    badge: "Neo4j + Cytoscape",
    description:
      "Visualize your cognitive universe with typed relationships: PREREQUISITE_OF, USES, and PART_OF. Filter by document, mastery band, or chapter. Includes a full keyboard-accessible tree alternative for mobile devices.",
    icon: GitGraph,
  },
  {
    title: "Grounded AI Tutor",
    badge: "Zero Hallucination",
    description:
      "Ask complex technical questions. Every claim is strictly grounded with interactive [Doc · Chapter · Page] citation badges that open a context drawer highlighting the exact source passage.",
    icon: MessageSquare,
  },
  {
    title: "Transparent 40/20/20/20 Mastery",
    badge: "Explainable Metric",
    description:
      "A deterministic formula combining lifetime quiz accuracy (40%), recency decay (20%), retention curves (20%), and difficulty weights (20%). Track progress using accessible Sprout, Stem, Leaf, and Helix marks.",
    icon: Brain,
  },
  {
    title: "Adaptive Learning Roadmap",
    badge: "Backward Traversal",
    description:
      "Never get stuck. If a checkpoint quiz reveals a deficit, MindGenome walks backward through the concept graph, prescribes focused remedial lessons, re-evaluates comprehension, and visibly updates your genome.",
    icon: Route,
  },
];

const FAQ = [
  {
    q: "How does MindGenome differ from generic document chatbots?",
    a: "Standard chatbots treat your notes as a flat text retrieval problem and answer questions without measuring whether you actually understand anything. MindGenome constructs a hierarchical knowledge graph, tracks your individual concept mastery mathematically, diagnoses weak prerequisites when you fail a quiz, and guides you through an adaptive learning roadmap.",
  },
  {
    q: "How is concept mastery calculated?",
    a: "We adhere strictly to our explainable 40/20/20/20 formula: Lifetime Quiz Accuracy (40%), Exponential Recency with a 14-day half-life (20%), Question Difficulty Adjustment (20%), and Exponential Memory Retention (20%). Scores map into 4 semantic bands: Beginner (0–30), Developing (31–60), Proficient (61–80), and Mastered (81–100).",
  },
  {
    q: "Can I inspect the exact sources behind AI tutor answers?",
    a: "Yes. Every tutor answer contains interactive inline citation chips formatted as [Document · Chapter · Page]. Clicking any citation slides open a Source Preview Drawer that highlights the exact passage from your uploaded material and spotlights the concept in the graph.",
  },
  {
    q: "Is MindGenome usable on mobile screens?",
    a: "Absolutely. On devices under 768px, the knowledge graph automatically provides an ergonomic hierarchical tree and card list mode with full search and prerequisite inspection, ensuring smooth learning on any screen size.",
  },
  {
    q: "How does the weak-prerequisite diagnosis work?",
    a: "When you take a checkpoint quiz (for example, scoring 2/5 on Gradient Boosting), the engine checks directed dependency edges in the graph. If your prerequisite concepts (like Ensemble Learning or Decision Trees) have low scores or stale retention, the system flags the root cause and provides a targeted remedial micro-lesson before retesting.",
  },
];

export function LandingPage() {
  const reduce = useReducedMotion();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleDemoLogin = async () => {
    setDemoLoading(true);
    try {
      const tokens = await apiFetch<TokenPair>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
      });
      useSession
        .getState()
        .setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
      navigate("/app");
    } catch {
      navigate("/login");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-ink transition-colors duration-200">
      {/* Navigation Header */}
      <header className="sticky top-0 z-30 border-b border-line/80 bg-surface/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-control bg-helix text-white font-bold font-display text-lg">
              M
            </div>
            <div>
              <span className="font-display text-xl font-bold tracking-tight">MindGenome</span>
              <span className="ml-1 text-[10px] font-mono uppercase text-copper font-semibold">AI</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              to="/styleguide"
              className="hidden text-xs font-semibold text-muted hover:text-ink sm:inline"
            >
              Styleguide
            </Link>
            <Link
              to="/about"
              className="hidden text-xs font-semibold text-muted hover:text-ink sm:inline"
            >
              About
            </Link>
            <Link
              to="/pricing"
              className="hidden text-xs font-semibold text-muted hover:text-ink sm:inline"
            >
              Pricing
            </Link>
            <ThemeToggle />
            <Link to="/login">
              <Button variant="ghost" className="text-xs sm:text-sm">
                Sign In
              </Button>
            </Link>
            <Button
              variant="primary"
              className="text-xs sm:text-sm"
              onClick={handleDemoLogin}
              disabled={demoLoading}
            >
              {demoLoading ? "Entering..." : "Instant Demo"}
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="mx-auto max-w-6xl px-4 pt-12 pb-16 sm:px-6 md:pt-20 md:pb-24">
        <div className="grid items-center gap-12 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <Badge tone="copper" className="mb-4">
              <Sparkles className="mr-1.5 h-3 w-3 inline" />
              Graph-Augmented Adaptive Learning
            </Badge>
            <h1 className="font-display text-4xl font-normal leading-[1.12] sm:text-5xl md:text-6xl">
              From AI that understands documents to AI that{" "}
              <span className="text-helix italic">understands the learner.</span>
            </h1>
            <p className="mt-5 max-w-xl text-base text-muted sm:text-lg leading-relaxed">
              Upload your research papers and study notes. MindGenome synthesizes an interconnected
              concept graph, diagnoses weak prerequisites when you stumble, and delivers grounded
              micro-lessons that visibly elevate your mastery.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Button
                variant="primary"
                className="px-6 py-2.5 text-base shadow-sm"
                onClick={handleDemoLogin}
                disabled={demoLoading}
              >
                Launch Demo Lab <ChevronRight className="h-4 w-4" />
              </Button>
              <Link to="/register">
                <Button variant="secondary" className="px-5 py-2.5 text-base">
                  Create Account
                </Button>
              </Link>
            </div>
            <div className="mt-8 flex items-center gap-6 text-xs text-muted">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-helix" />
                Zero Hallucinations
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-helix" />
                Explainable 40/20/20/20 Formula
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-helix" />
                Prerequisite Diagnosis
              </span>
            </div>
          </div>

          {/* Interactive Mini-Genome Visual */}
          <div className="lg:col-span-5">
            <InteractiveHeroGraph reduce={Boolean(reduce)} />
          </div>
        </div>
      </section>

      {/* 5-Step Loop Walkthrough ("How it Works") */}
      <section className="border-y border-line bg-surface/50 py-16" id="how-it-works">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <Badge tone="helix">Continuous Feedback Loop</Badge>
              <h2 className="mt-2 font-display text-3xl sm:text-4xl">How MindGenome Works</h2>
              <p className="mt-2 text-muted text-sm sm:text-base max-w-xl">
                A closed feedback cycle designed around human cognitive science rather than passive text consumption.
              </p>
            </div>
            <span className="text-xs font-mono text-muted">Step {activeStep + 1} of 5</span>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((s, idx) => {
              const Icon = s.icon;
              const isActive = activeStep === idx;
              return (
                <div
                  key={s.n}
                  onClick={() => setActiveStep(idx)}
                  className={`cursor-pointer rounded-card border p-4 transition-all duration-200 ${
                    isActive
                      ? "border-helix bg-surface shadow-card ring-1 ring-helix/30"
                      : "border-line bg-canvas hover:border-helix/40 hover:bg-surface/60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-copper">{s.n}</span>
                    <Icon className={`h-4 w-4 ${isActive ? "text-helix" : "text-muted"}`} />
                  </div>
                  <h3 className="mt-3 font-display text-lg font-semibold">{s.t}</h3>
                  <p className="mt-2 text-xs text-muted leading-relaxed">{s.d}</p>
                  <div className="mt-3">
                    <span className="inline-block rounded-control bg-canvas px-2 py-0.5 text-[10px] font-mono text-muted">
                      {s.tag}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <div className="text-center max-w-2xl mx-auto">
          <Badge tone="copper">Architecture Pillars</Badge>
          <h2 className="mt-2 font-display text-3xl sm:text-4xl">Engineered for Deep Retention</h2>
          <p className="mt-3 text-muted text-sm sm:text-base">
            Every screen connects back to the knowledge graph and your measurable mastery state.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {FEATURES.map((feat) => {
            const Icon = feat.icon;
            return (
              <Card key={feat.title} className="p-6 transition hover:border-helix/50">
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-control bg-helix/10 text-helix">
                    <Icon className="h-5 w-5" />
                  </div>
                  <Badge tone="neutral">{feat.badge}</Badge>
                </div>
                <h3 className="mt-4 font-display text-2xl">{feat.title}</h3>
                <p className="mt-2 text-sm text-muted leading-relaxed">{feat.description}</p>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Live-looking Product Preview Window */}
      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <Card className="overflow-hidden p-0 border border-line shadow-card">
          <div className="flex items-center justify-between border-b border-line bg-canvas px-4 py-2.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-proficient/70" />
              <span className="ml-2 font-mono text-[11px] text-muted">
                app.mindgenome.ai/genome?focus=concept-gb
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full bg-proficient animate-pulse" />
              <span className="font-mono text-[10px] text-muted">Graph Synchronized</span>
            </div>
          </div>

          <div className="grid gap-6 p-6 lg:grid-cols-12 bg-surface">
            {/* Left preview: Concept Inspector */}
            <div className="lg:col-span-5 space-y-4 rounded-card border border-line bg-canvas p-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted">Active Node Focus</span>
                  <h4 className="font-display text-xl font-bold">Gradient Boosting</h4>
                </div>
                <MasteryChip band="beginner" score={24} />
              </div>
              <p className="text-xs text-muted leading-relaxed">
                An ensemble meta-algorithm that builds trees sequentially, each minimizing the pseudo-residuals of the prior model.
              </p>
              <div className="rounded-control border border-danger/30 bg-danger/10 p-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-danger">
                  <span>Prerequisite Gap Detected</span>
                </div>
                <p className="mt-1 text-[11px] text-ink/80">
                  Checkpoint score: <strong>2/5</strong>. Likely missing prerequisite: <strong>Ensemble Learning</strong>.
                </p>
              </div>
              <div className="flex gap-2 pt-1">
                <Button variant="primary" className="text-xs flex-1">
                  Remedial Lesson
                </Button>
                <Button variant="secondary" className="text-xs">
                  Inspect Lineage
                </Button>
              </div>
            </div>

            {/* Right preview: Adaptive Path Sequence */}
            <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-copper">
                    Adaptive Remedial Sequence
                  </span>
                  <span className="text-xs font-mono text-muted">Decision Trees → XGBoost</span>
                </div>
                <div className="mt-4 space-y-2.5">
                  <div className="flex items-center justify-between rounded-control border border-mastered/40 bg-mastered/5 p-3 text-xs">
                    <span className="font-semibold">1. Decision Trees & Impurity</span>
                    <MasteryChip band="mastered" score={94} />
                  </div>
                  <div className="flex items-center justify-between rounded-control border border-developing/50 bg-developing/5 p-3 text-xs ring-1 ring-developing">
                    <div>
                      <span className="font-semibold">2. Ensemble Learning (Remedial Focus)</span>
                      <p className="text-[11px] text-muted">Recommended: Bagging vs Boosting concepts</p>
                    </div>
                    <MasteryChip band="developing" score={48} />
                  </div>
                  <div className="flex items-center justify-between rounded-control border border-line bg-canvas p-3 text-xs opacity-80">
                    <span className="font-semibold">3. Retest: Gradient Boosting</span>
                    <span className="text-muted font-mono text-[11px]">Retest Scheduled</span>
                  </div>
                </div>
              </div>
              <div className="border-t border-line pt-3 flex items-center justify-between text-xs text-muted">
                <span>The Elements of Statistical Learning (Hastie et al.)</span>
                <span className="font-mono text-helix">Cited § Chap. 10</span>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* FAQ Section */}
      <section className="mx-auto max-w-3xl px-4 pb-20 sm:px-6">
        <div className="text-center">
          <Badge tone="neutral">Questions & Clarity</Badge>
          <h2 className="mt-2 font-display text-3xl">Frequently Asked Questions</h2>
        </div>
        <div className="mt-8 divide-y divide-line rounded-card border border-line bg-surface">
          {FAQ.map((item, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={item.q} className="p-4 sm:p-5">
                <button
                  type="button"
                  className="flex w-full items-center justify-between text-left font-semibold text-sm sm:text-base"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                >
                  <span>{item.q}</span>
                  <ChevronDown
                    className={`h-4 w-4 text-muted transition-transform duration-200 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {isOpen ? (
                  <p className="mt-3 text-xs sm:text-sm text-muted leading-relaxed">{item.a}</p>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="border-t border-line bg-surface py-16">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6">
          <h2 className="font-display text-3xl sm:text-4xl">
            Grow a permanent knowledge genome, not an ephemeral chat log.
          </h2>
          <p className="mt-3 text-muted text-sm sm:text-base max-w-xl mx-auto">
            Experience the full Machine Learning demo curriculum: Decision Trees, Ensemble Learning,
            Gradient Boosting, and XGBoost.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Button
              variant="primary"
              className="px-6 py-2.5 text-base"
              onClick={handleDemoLogin}
              disabled={demoLoading}
            >
              Start Learning Now
            </Button>
            <Link to="/register">
              <Button variant="secondary" className="px-6 py-2.5 text-base">
                Create Free Account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-line bg-canvas py-8 text-xs text-muted">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <span className="font-display font-semibold text-ink">MindGenome AI</span>
            <span>© 2026. Built with React 18, Cytoscape & FastAPI.</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/about" className="hover:text-ink">
              About
            </Link>
            <Link to="/pricing" className="hover:text-ink">
              Pricing
            </Link>
            <Link to="/styleguide" className="hover:text-ink">
              Design System
            </Link>
            <Link to="/login" className="hover:text-ink">
              Sign In
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function InteractiveHeroGraph({ reduce }: { reduce: boolean }) {
  const [selectedNode, setSelectedNode] = useState<string>("gb");

  const nodes = [
    {
      id: "dt",
      x: 75,
      y: 110,
      label: "Decision Trees",
      short: "Trees",
      score: 94,
      band: "mastered" as const,
    },
    {
      id: "ens",
      x: 175,
      y: 55,
      label: "Ensemble Learning",
      short: "Ensemble",
      score: 48,
      band: "developing" as const,
    },
    {
      id: "gb",
      x: 275,
      y: 115,
      label: "Gradient Boosting",
      short: "Boosting",
      score: 24,
      band: "beginner" as const,
    },
    {
      id: "xgb",
      x: 355,
      y: 60,
      label: "Extreme Boosting",
      short: "XGBoost",
      score: 0,
      band: "insufficient_evidence" as const,
    },
  ];

  const active = nodes.find((n) => n.id === selectedNode) ?? nodes[2];

  return (
    <div className="space-y-3">
      <div className="relative rounded-sheet border border-line bg-surface p-4 shadow-card overflow-hidden">
        <div className="flex items-center justify-between pb-2 text-[10px] font-mono text-muted border-b border-line">
          <span>Interactive Mini-Genome Canvas</span>
          <span className="text-copper">Click nodes to inspect</span>
        </div>

        <svg
          viewBox="0 0 420 180"
          className="w-full select-none"
          role="img"
          aria-label="Interactive mini knowledge genome visual"
        >
          {/* Directed Dependency Edges */}
          <line
            x1="90"
            y1="100"
            x2="160"
            y2="65"
            stroke="var(--mg-line)"
            strokeWidth="1.5"
            strokeDasharray="3 3"
          />
          <line
            x1="190"
            y1="65"
            x2="260"
            y2="105"
            stroke="var(--mg-copper)"
            strokeWidth="2"
          />
          <line
            x1="290"
            y1="105"
            x2="340"
            y2="70"
            stroke="var(--mg-line)"
            strokeWidth="1.5"
            strokeDasharray="3 3"
          />

          {/* Nodes */}
          {nodes.map((n, i) => {
            const isSelected = n.id === selectedNode;
            return (
              <g
                key={n.id}
                className="cursor-pointer"
                onClick={() => setSelectedNode(n.id)}
              >
                <motion.circle
                  cx={n.x}
                  cy={n.y}
                  r={isSelected ? "22" : "18"}
                  fill="var(--mg-canvas)"
                  stroke={isSelected ? "var(--mg-copper)" : "var(--mg-helix)"}
                  strokeWidth={isSelected ? "3" : "2"}
                  animate={
                    reduce
                      ? undefined
                      : {
                          scale: isSelected ? [1, 1.06, 1] : 1,
                        }
                  }
                  transition={{ repeat: Infinity, duration: 2.5, delay: i * 0.2 }}
                />
                <text
                  x={n.x}
                  y={n.y + 4}
                  textAnchor="middle"
                  fontSize="8.5"
                  fontWeight="600"
                  fill="var(--mg-ink)"
                >
                  {n.short}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Mini-Inspector */}
        <div className="mt-2 flex items-center justify-between rounded-control border border-line bg-canvas px-3 py-2 text-xs">
          <div>
            <span className="font-semibold text-ink">{active.label}</span>
            <span className="ml-2 text-[10px] text-muted font-mono">id: {active.id}</span>
          </div>
          <MasteryChip band={active.band} score={active.score} />
        </div>
      </div>
    </div>
  );
}
