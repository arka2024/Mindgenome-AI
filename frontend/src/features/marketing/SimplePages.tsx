import { useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Field, Input } from "@/shared/ui/Input";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import { Stepper } from "@/shared/ui/Stepper";
import { Tabs } from "@/shared/ui/Tabs";
import { Dialog } from "@/shared/ui/Dialog";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useToasts } from "@/shared/ui/Toast";
import { Badge } from "@/shared/ui/Badge";
import { Sparkles, Terminal, Bell } from "lucide-react";

export function PricingPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <div className="text-center">
        <h1 className="font-display text-4xl sm:text-5xl">Transparent Learning Tiers</h1>
        <p className="mt-3 text-lg text-muted">
          Ground your knowledge genome with full algorithmic transparency. No hidden paywalls during the demo preview.
        </p>
      </div>

      <div className="mt-12 grid gap-6 md:grid-cols-2">
        <Card className="flex flex-col justify-between border-helix/40 shadow-lg">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl">Scholar Free</h2>
              <Badge>Current Preview</Badge>
            </div>
            <p className="mt-4 text-4xl font-bold font-display">$0 <span className="text-sm font-sans font-normal text-muted">/ month</span></p>
            <ul className="mt-6 space-y-3 text-sm text-muted">
              <li>✓ Ingest up to 10 PDF/DOCX textbooks & papers</li>
              <li>✓ Interactive Cytoscape knowledge graph</li>
              <li>✓ Concept-grounded RAG AI tutor</li>
              <li>✓ Automated prerequisite diagnostic quizzes</li>
              <li>✓ 40/20/20/20 mastery tracking & roadmap</li>
            </ul>
          </div>
          <Link className="mt-8 block" to="/register">
            <Button className="w-full">Get Started Free</Button>
          </Link>
        </Card>

        <Card className="flex flex-col justify-between opacity-80">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl">Lab & Research Pro</h2>
              <Badge>Coming Soon</Badge>
            </div>
            <p className="mt-4 text-4xl font-bold font-display">$29 <span className="text-sm font-sans font-normal text-muted">/ month</span></p>
            <ul className="mt-6 space-y-3 text-sm text-muted">
              <li>✓ Unlimited multi-gigabyte document corpora</li>
              <li>✓ Custom multi-agent fine-tuned graph embeddings</li>
              <li>✓ Multi-user shared cohort genome maps</li>
              <li>✓ Exportable Anki/spaced-repetition sync</li>
              <li>✓ Dedicated private Neo4j & Qdrant cluster</li>
            </ul>
          </div>
          <Button disabled variant="secondary" className="mt-8 w-full">
            Waitlist Only
          </Button>
        </Card>
      </div>
    </div>
  );
}

export function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="font-display text-4xl sm:text-5xl">About MindGenome AI</h1>
      <p className="mt-4 text-xl text-muted leading-relaxed">
        We move from AI that merely understands documents to AI that understands the learner.
      </p>
      <div className="mt-8 space-y-6 text-ink/90 leading-relaxed">
        <p>
          Generic chatbot wrappers treat human learning like a search problem. But real mastery is hierarchical:
          you cannot comprehend <strong>Gradient Boosting</strong> if your foundations in <strong>Decision Trees</strong> and
          <strong>Ensemble Variance Reduction</strong> are porous.
        </p>
        <p>
          MindGenome maps your raw reading material into a rich semantic graph. Every time you take a checkpoint quiz,
          our deterministic 40/20/20/20 engine inspects lifetime accuracy, recency decay, question difficulty, and
          retention curves. When you score 2/5, we do not simply repeat the same paragraph—we walk backward through the
          prerequisite graph, identify the missing cognitive link, and serve targeted remedial micro-lessons.
        </p>
      </div>
      <div className="mt-10">
        <Link to="/app">
          <Button>Enter the Genome Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}

export function StyleGuidePage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("buttons");
  const pushToast = useToasts((s) => s.push);

  return (
    <div className="mx-auto max-w-5xl space-y-12 px-4 py-12">
      <div>
        <Badge>Living Design System</Badge>
        <h1 className="mt-2 font-display text-4xl sm:text-5xl">Design System & Primitives</h1>
        <p className="mt-2 text-muted">
          "Helix Lab at Dusk" — Precision tokens, accessible Radix primitives, and semantic mastery components.
        </p>
      </div>

      {/* Color Tokens */}
      <section className="space-y-4">
        <h2 className="font-display text-2xl border-b border-line pb-2">Color Tokens</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 md:grid-cols-6">
          <div className="space-y-1.5">
            <div className="h-16 w-full rounded-card bg-canvas border border-line shadow-inner" />
            <p className="text-xs font-semibold">Canvas</p>
            <p className="text-[10px] font-mono text-muted">Light: #F4F0E8<br />Dark: #101614</p>
          </div>
          <div className="space-y-1.5">
            <div className="h-16 w-full rounded-card bg-surface border border-line" />
            <p className="text-xs font-semibold">Surface</p>
            <p className="text-[10px] font-mono text-muted">Elevated card</p>
          </div>
          <div className="space-y-1.5">
            <div className="h-16 w-full rounded-card bg-helix text-white flex items-center justify-center font-bold text-xs">
              Primary
            </div>
            <p className="text-xs font-semibold">Helix Accent</p>
            <p className="text-[10px] font-mono text-muted">#0F6E6B / #4ECDC4</p>
          </div>
          <div className="space-y-1.5">
            <div className="h-16 w-full rounded-card bg-copper text-white flex items-center justify-center font-bold text-xs">
              Accent
            </div>
            <p className="text-xs font-semibold">Copper</p>
            <p className="text-[10px] font-mono text-muted">#B86B3D / #E09A6A</p>
          </div>
          <div className="space-y-1.5">
            <div className="h-16 w-full rounded-card bg-proficient text-white flex items-center justify-center font-bold text-xs">
              Proficient
            </div>
            <p className="text-xs font-semibold">Teal</p>
            <p className="text-[10px] font-mono text-muted">61–80 Mastery</p>
          </div>
          <div className="space-y-1.5">
            <div className="h-16 w-full rounded-card bg-danger text-white flex items-center justify-center font-bold text-xs">
              Danger
            </div>
            <p className="text-xs font-semibold">Alert / Weak</p>
            <p className="text-[10px] font-mono text-muted">Action required</p>
          </div>
        </div>
      </section>

      {/* Typography Tokens */}
      <section className="space-y-4">
        <h2 className="font-display text-2xl border-b border-line pb-2">Typography Hierarchy</h2>
        <div className="space-y-3">
          <div>
            <span className="text-xs font-mono text-muted">font-display (Fraunces optical size)</span>
            <p className="font-display text-3xl sm:text-4xl">Adaptive Semantic Knowledge Graph</p>
          </div>
          <div>
            <span className="text-xs font-mono text-muted">font-sans (Source Sans 3 UI body)</span>
            <p className="text-base text-ink">
              Learners retain 4× more knowledge when gaps are remediated immediately through prerequisite traversal.
            </p>
          </div>
          <div>
            <span className="text-xs font-mono text-muted">font-mono (IBM Plex Mono citation & code)</span>
            <p className="font-mono text-sm text-helix bg-surface p-2 rounded-control border border-line inline-block">
              [Elements of Statistical Learning § Chap. 10.1 · p. 337]
            </p>
          </div>
        </div>
      </section>

      {/* Mastery Semantic Chips */}
      <section className="space-y-4">
        <h2 className="font-display text-2xl border-b border-line pb-2">Semantic Mastery Bands (Icon + Label + Value)</h2>
        <p className="text-sm text-muted">Complies with WCAG accessibility guidelines by never communicating score solely via color.</p>
        <div className="flex flex-wrap gap-3">
          <MasteryChip band="beginner" score={24} />
          <MasteryChip band="developing" score={52} />
          <MasteryChip band="proficient" score={78} />
          <MasteryChip band="mastered" score={96} />
          <MasteryChip band="insufficient_evidence" />
        </div>
      </section>

      {/* Interactive Tabs for Components */}
      <section className="space-y-4">
        <h2 className="font-display text-2xl border-b border-line pb-2">Component Gallery</h2>
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          tabs={[
            {
              value: "buttons",
              label: "Buttons & Badges",
              content: (
                <div className="space-y-6">
                  <div className="flex flex-wrap items-center gap-3">
                    <Button variant="primary">Primary Helix</Button>
                    <Button variant="secondary">Secondary Outline</Button>
                    <Button variant="ghost">Ghost Action</Button>
                    <Button variant="danger">Danger Destructive</Button>
                    <Button disabled>Disabled</Button>
                    <Button variant="primary">
                      <Sparkles className="h-4 w-4" /> With Icon
                    </Button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge>Default Badge</Badge>
                    <Badge tone="helix">Helix Badge</Badge>
                    <Badge tone="copper">Copper Badge</Badge>
                  </div>
                </div>
              ),
            },
            {
              value: "forms",
              label: "Form Controls",
              content: (
                <div className="grid max-w-lg gap-4">
                  <Field label="Standard Concept Name">
                    <Input placeholder="e.g. Extreme Gradient Boosting (XGBoost)" />
                  </Field>
                  <Field label="With Validation Error" error="This concept name is already indexed in your genome.">
                    <Input defaultValue="Gradient Boosting" className="border-danger" />
                  </Field>
                </div>
              ),
            },
            {
              value: "feedback",
              label: "Feedback & Dialogs",
              content: (
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <Button
                      variant="secondary"
                      onClick={() =>
                        pushToast(
                          "Genome Updated",
                          "Remedial lesson completed. Ensemble Learning scored 4/5.",
                        )
                      }
                    >
                      <Bell className="h-4 w-4" /> Trigger Toast Notification
                    </Button>
                    <Button variant="primary" onClick={() => setDialogOpen(true)}>
                      Open Accessible Dialog
                    </Button>
                  </div>
                  <Dialog open={dialogOpen} onOpenChange={setDialogOpen} title="Concept Details">
                    <p className="text-sm text-muted">
                      Gradient boosting is an ensemble machine learning technique for regression and classification problems,
                      which produces a prediction model in the form of an ensemble of weak prediction models.
                    </p>
                    <div className="mt-4 flex justify-end">
                      <Button onClick={() => setDialogOpen(false)}>Close Inspector</Button>
                    </div>
                  </Dialog>
                </div>
              ),
            },
            {
              value: "stepper",
              label: "Document Stepper",
              content: (
                <div className="space-y-6">
                  <div>
                    <span className="text-xs font-semibold text-muted">State: Embedding (Step 4 of 7)</span>
                    <div className="mt-2">
                      <Stepper status="embedding" />
                    </div>
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-muted">State: Graph Built / Ready</span>
                    <div className="mt-2">
                      <Stepper status="ready" />
                    </div>
                  </div>
                </div>
              ),
            },
            {
              value: "skeletons",
              label: "Skeletons & Empty States",
              content: (
                <div className="space-y-6">
                  <div className="space-y-2">
                    <Skeleton className="h-6 w-1/3" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6" />
                  </div>
                  <EmptyState
                    title="No documents uploaded yet"
                    body="Drop your ML research papers or course notes to begin constructing your personal knowledge genome."
                    action="Upload Document"
                    onAction={() => pushToast("Upload clicked", "Opening file dropzone...")}
                  />
                </div>
              ),
            },
          ]}
        />
      </section>

      <div className="border-t border-line pt-6 flex items-center justify-between text-xs text-muted">
        <span className="font-mono">MindGenome UI Kit v0.1.0</span>
        <div className="flex items-center gap-1">
          <Terminal className="h-3.5 w-3.5" />
          <span>Tested with Vitest & Radix UI</span>
        </div>
      </div>
    </div>
  );
}
