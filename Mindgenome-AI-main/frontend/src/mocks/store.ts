import type { MasteryRow } from "./seed";
import {
  C,
  CHAPTERS,
  CONCEPTS,
  DEMO_EMAIL,
  DEMO_PASSWORD,
  DOC_ID,
  DEFINITIONS,
  EDGES,
  JOB_ID,
  LESSONS,
  PASSAGE,
  QUIZZES,
  USER_ID,
  initialMastery,
} from "./seed";
import { bandFromScore, computeMastery } from "@/shared/lib/mastery";

const JOB_FLOW = [
  "queued",
  "parsing",
  "chunking",
  "embedding",
  "extracting",
  "graph_built",
  "ready",
] as const;

export type JobStatus = (typeof JOB_FLOW)[number] | "failed";

type Doc = {
  id: string;
  filename: string;
  status: "uploaded" | "processing" | "ready" | "failed" | "rejected";
  created_at: string;
  page_count: number;
  job_id: string;
  is_low_text: boolean;
};

type Job = {
  id: string;
  document_id: string;
  status: JobStatus;
  progress_pct: number;
  tick: number;
};

function uid(): string {
  return crypto.randomUUID();
}

function createStore() {
  const mastery = initialMastery();
  const answersLog: Record<string, Array<{ correct: boolean; difficulty: string; ageDays: number }>> =
    {};
  for (const row of mastery) {
    answersLog[row.concept_id] = Array.from({ length: row.evidence_n }, (_, i) => ({
      correct: i < Math.round(row.evidence_n * (row.quiz_accuracy / 100)),
      difficulty: "medium",
      ageDays: 4,
    }));
  }

  return {
    users: [
      {
        id: USER_ID,
        email: DEMO_EMAIL,
        password: DEMO_PASSWORD,
        display_name: "Asha Learner",
        roles: ["user"] as Array<"user" | "admin">,
      },
    ],
    tokens: new Map<string, { userId: string; kind: "access" | "refresh" }>(),
    mastery,
    answersLog,
    gbAttempts: 0,
    ensembleRemedial: false,
    documents: [
      {
        id: DOC_ID,
        filename: "Hands-On Machine Learning (demo excerpt).pdf",
        status: "ready" as const,
        created_at: new Date().toISOString(),
        page_count: 80,
        job_id: JOB_ID,
        is_low_text: false,
      },
    ] as Doc[],
    jobs: [
      {
        id: JOB_ID,
        document_id: DOC_ID,
        status: "ready" as JobStatus,
        progress_pct: 100,
        tick: 99,
      },
    ] as Job[],
    activity: [
      {
        id: "a1",
        at: new Date().toISOString(),
        text: "Ready: Hands-On Machine Learning (demo excerpt).pdf",
      },
    ],
    sessions: new Map<
      string,
      {
        id: string;
        mode: string;
        concept_id: string;
        current_index: number;
        understood: string[];
      }
    >(),
    quizzes: new Map<string, { concept_id: string; questionIds: string[] }>(),
  };
}

export let db = createStore();

export function resetStore(): void {
  db = createStore();
}

export function conceptName(id: string): string {
  return CONCEPTS.find((c) => c.id === id)?.name ?? id;
}

export function getMastery(id: string): MasteryRow {
  const row = db.mastery.find((m) => m.concept_id === id);
  if (!row) {
    return {
      concept_id: id,
      name: conceptName(id),
      mastery: 0,
      band: "insufficient_evidence",
      evidence_n: 0,
      quiz_accuracy: 0,
      recent_performance: 0,
      difficulty_adjusted: 0,
      retention: 0,
    };
  }
  return row;
}

export function recompute(conceptId: string): MasteryRow {
  const answers = db.answersLog[conceptId] ?? [];
  const parts = computeMastery({
    answers,
    successfulRevisions: conceptId === C.ensemble && db.ensembleRemedial ? 2 : 1,
    daysSinceLastCorrect: answers.some((a) => a.correct) ? 0 : null,
  });
  const band = bandFromScore(parts.mastery, answers.length);
  const row: MasteryRow = { ...parts, evidence_n: answers.length, band, concept_id: conceptId, name: conceptName(conceptId) };
  const idx = db.mastery.findIndex((m) => m.concept_id === conceptId);
  if (idx >= 0) db.mastery[idx] = row;
  else db.mastery.push(row);
  return row;
}

export function applyQuiz(conceptId: string, selected: number[]): {
  correct: number;
  total: number;
  per: Array<{
    question_id: string;
    selected_index: number;
    correct_index: number;
    explanation: string;
    is_correct: boolean;
  }>;
  mastery: MasteryRow;
  deltas: Array<{ concept_id: string; name: string; before: number; after: number }>;
  next: { mode: "learn" | "remedial" | "revision" | "retest"; concept_id: string | null; concept_name?: string; because: string };
} {
  const quiz = QUIZZES[conceptId] ?? QUIZZES[C.gb];
  const before = quiz
    .flatMap((q) => q.tags.map((t) => CONCEPTS.find((c) => c.name === t)?.id))
    .filter((id): id is string => Boolean(id))
    .filter((id, i, a) => a.indexOf(id) === i)
    .map((id) => ({ id, before: getMastery(id).mastery }));

  const per = quiz.map((q, i) => {
    const selected_index = selected[i] ?? -1;
    const is_correct = selected_index === q.correct;
    return {
      question_id: q.id,
      selected_index,
      correct_index: q.correct,
      explanation: q.explanation,
      is_correct,
    };
  });
  const correct = per.filter((p) => p.is_correct).length;

  for (const q of quiz) {
    const p = per.find((x) => x.question_id === q.id);
    const log = db.answersLog[conceptId] ?? [];
    log.unshift({
      correct: Boolean(p?.is_correct),
      difficulty: q.difficulty,
      ageDays: 0,
    });
    db.answersLog[conceptId] = log.slice(0, 20);
  }
  const mastery = recompute(conceptId);

  if (conceptId === C.gb) db.gbAttempts += 1;
  if (conceptId === C.ensemble) db.ensembleRemedial = true;

  const deltas = before.map((b) => {
    const after = b.id === conceptId ? mastery.mastery : getMastery(b.id).mastery;
    return { concept_id: b.id, name: conceptName(b.id), before: b.before, after };
  });

  let next: {
    mode: "learn" | "remedial" | "revision" | "retest";
    concept_id: string | null;
    concept_name?: string;
    because: string;
  };

  const ensemble = getMastery(C.ensemble);
  if (conceptId === C.gb && correct <= 2 && ensemble.mastery < 55) {
    next = {
      mode: "remedial",
      concept_id: C.ensemble,
      concept_name: "Ensemble Learning",
      because: `You're weak in Gradient Boosting (${correct}/5). Likely missing prerequisite: Ensemble Learning.`,
    };
  } else if (conceptId === C.ensemble) {
    next = {
      mode: "retest",
      concept_id: C.gb,
      concept_name: "Gradient Boosting",
      because: "Ensemble Learning looks steadier. Retest Gradient Boosting to confirm the gap closed.",
    };
  } else if (conceptId === C.gb && correct >= 4) {
    next = {
      mode: "learn",
      concept_id: C.xgb,
      concept_name: "XGBoost",
      because: "Prerequisites for XGBoost are ready: Gradient Boosting is now in a healthier band.",
    };
  } else {
    next = {
      mode: "revision",
      concept_id: conceptId,
      concept_name: conceptName(conceptId),
      because: "Keep this concept in the revision loop before climbing the graph.",
    };
  }

  db.activity.unshift({
    id: uid(),
    at: new Date().toISOString(),
    text: `Quiz on ${conceptName(conceptId)}: ${correct}/${quiz.length}`,
  });

  return { correct, total: quiz.length, per, mastery, deltas, next };
}

export function graphPayload() {
  const nodes = [
    {
      data: {
        id: DOC_ID,
        label: "ML excerpt",
        kind: "document",
        mastery: null,
        band: null,
      },
    },
    ...CHAPTERS.map((ch) => ({
      data: {
        id: ch.id,
        label: ch.title,
        kind: "chapter",
        mastery: null,
        band: null,
        parent: DOC_ID,
      },
    })),
    ...CONCEPTS.map((c) => {
      const m = getMastery(c.id);
      return {
        data: {
          id: c.id,
          label: c.name,
          kind: "concept",
          mastery: m.mastery,
          band: m.band,
          definition: DEFINITIONS[c.id] ?? `${c.name} as used in the uploaded notes.`,
        },
      };
    }),
  ];
  const edges = [
    { data: { id: "doc-ch1", source: DOC_ID, target: "ch-1", kind: "PART_OF" } },
    { data: { id: "doc-ch2", source: DOC_ID, target: "ch-2", kind: "PART_OF" } },
    { data: { id: "doc-ch3", source: DOC_ID, target: "ch-3", kind: "PART_OF" } },
    { data: { id: "doc-ch4", source: DOC_ID, target: "ch-4", kind: "PART_OF" } },
    ...EDGES.map((e) => ({
      data: { id: e.id, source: e.source, target: e.target, kind: e.kind },
    })),
  ];
  return { nodes, edges };
}

export function dashboard() {
  const scored = db.mastery.filter((m) => m.band !== "insufficient_evidence");
  const overall =
    scored.reduce((s, m) => s + m.mastery, 0) / Math.max(1, scored.length);
  const band_counts: Record<string, number> = {
    beginner: 0,
    developing: 0,
    proficient: 0,
    mastered: 0,
    insufficient_evidence: 0,
  };
  for (const m of db.mastery) band_counts[m.band] = (band_counts[m.band] ?? 0) + 1;
  const weak = [...db.mastery]
    .filter((m) => m.band === "beginner" || m.band === "developing")
    .sort((a, b) => a.mastery - b.mastery)
    .slice(0, 6);
  const gb = getMastery(C.gb);
  const ens = getMastery(C.ensemble);
  const recommended =
    gb.mastery < 61 && ens.mastery < 55
      ? {
          concept_id: C.gb,
          name: "Gradient Boosting",
          because:
            "Next in the ML chain after Decision Trees. Ensemble Learning is still weak — a checkpoint will surface that gap.",
        }
      : ens.mastery < 55
        ? {
            concept_id: C.ensemble,
            name: "Ensemble Learning",
            because: "Weak prerequisite blocking Gradient Boosting.",
          }
        : gb.mastery < 61
          ? {
              concept_id: C.gb,
              name: "Gradient Boosting",
              because: "Retest after the Ensemble remedial.",
            }
          : {
              concept_id: C.xgb,
              name: "XGBoost",
              because: "Gradient Boosting is healthy enough to learn the systems layer.",
            };
  const growth = Array.from({ length: 8 }, (_, i) => ({
    date: new Date(Date.now() - (7 - i) * 86400000).toISOString().slice(0, 10),
    mastery: Math.max(20, overall - 12 + i * 2 + (db.gbAttempts >= 2 ? 8 : 0)),
  }));
  return {
    overall_mastery: Math.round(overall * 10) / 10,
    band_counts,
    weak_concepts: weak,
    recommended,
    growth,
    due_revisions: 3,
    revision_list: [
      { concept_id: C.trees, name: "Decision Trees", due: "today" },
      { concept_id: cidSafe(4), name: "Gradient Descent", due: "tomorrow" },
      { concept_id: cidSafe(5), name: "Overfitting", due: "in 3 days" },
    ],
    activity: db.activity.slice(0, 8),
    active_jobs: db.jobs.filter((j) => j.status !== "ready" && j.status !== "failed"),
  };
}

function cidSafe(n: number): string {
  return `cccccccc-0000-4000-8000-${String(n).padStart(12, "0")}`;
}

export function advanceJob(job: Job): Job {
  if (job.status === "ready" || job.status === "failed") return job;
  job.tick += 1;
  const idx = Math.min(JOB_FLOW.length - 1, Math.floor(job.tick / 1));
  job.status = JOB_FLOW[idx] ?? "ready";
  job.progress_pct = Math.min(100, Math.round((idx / (JOB_FLOW.length - 1)) * 100));
  if (job.status === "ready") {
    const doc = db.documents.find((d) => d.id === job.document_id);
    if (doc) doc.status = "ready";
    db.activity.unshift({
      id: uid(),
      at: new Date().toISOString(),
      text: `Graph ready for ${doc?.filename ?? "document"}`,
    });
  } else {
    const doc = db.documents.find((d) => d.id === job.document_id);
    if (doc) doc.status = "processing";
  }
  return job;
}

export function issueTokens(userId: string) {
  const access = `acc_${uid()}`;
  const refresh = `ref_${uid()}`;
  db.tokens.set(access, { userId, kind: "access" });
  db.tokens.set(refresh, { userId, kind: "refresh" });
  return {
    access_token: access,
    refresh_token: refresh,
    token_type: "bearer" as const,
    expires_in: 900,
  };
}

export function userFromAuth(header: string | null) {
  if (!header?.startsWith("Bearer ")) return null;
  const token = header.slice(7);
  const rec = db.tokens.get(token);
  if (!rec || rec.kind !== "access") return null;
  return db.users.find((u) => u.id === rec.userId) ?? null;
}

export { PASSAGE, CHAPTERS, LESSONS, QUIZZES, CONCEPTS, C, uid };
