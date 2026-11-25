import { z } from "zod";

export const problemSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number(),
  detail: z.string().optional(),
  instance: z.string().optional(),
  request_id: z.string().optional(),
});

export const tokenPairSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.literal("bearer"),
  expires_in: z.number(),
});

export const userSchema = z.object({
  id: z.string(),
  email: z.string(),
  display_name: z.string(),
  roles: z.array(z.enum(["user", "admin"])),
});

export const masteryBandSchema = z.enum([
  "insufficient_evidence",
  "beginner",
  "developing",
  "proficient",
  "mastered",
]);

export const masteryScoreSchema = z.object({
  concept_id: z.string(),
  name: z.string().optional(),
  mastery: z.number(),
  band: masteryBandSchema,
  evidence_n: z.number(),
  quiz_accuracy: z.number(),
  recent_performance: z.number(),
  difficulty_adjusted: z.number(),
  retention: z.number(),
  component_trace: z.record(z.unknown()).optional(),
});

export const ingestionJobSchema = z.object({
  id: z.string(),
  document_id: z.string(),
  status: z.enum([
    "queued",
    "parsing",
    "chunking",
    "embedding",
    "extracting",
    "graph_built",
    "ready",
    "failed",
  ]),
  progress_pct: z.number(),
  stage_detail: z.string().nullable().optional(),
  error_code: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
});

export const documentSchema = z.object({
  id: z.string(),
  filename: z.string(),
  status: z.enum(["uploaded", "processing", "ready", "failed", "rejected"]),
  is_low_text: z.boolean().optional(),
  low_text_warning: z.string().nullable().optional(),
  page_count: z.number().nullable().optional(),
  created_at: z.string(),
  job_id: z.string().optional(),
  chapters: z
    .array(
      z.object({
        id: z.string(),
        title: z.string(),
        page_start: z.number(),
        page_end: z.number(),
      }),
    )
    .optional(),
});

export const dashboardSchema = z.object({
  overall_mastery: z.number(),
  band_counts: z.record(z.number()),
  weak_concepts: z.array(masteryScoreSchema),
  recommended: z.object({
    concept_id: z.string(),
    name: z.string(),
    because: z.string(),
  }),
  growth: z.array(z.object({ date: z.string(), mastery: z.number() })),
  due_revisions: z.number(),
  revision_list: z.array(z.object({ concept_id: z.string(), name: z.string(), due: z.string() })),
  activity: z.array(z.object({ id: z.string(), at: z.string(), text: z.string() })),
  active_jobs: z.array(ingestionJobSchema),
});

export const graphPayloadSchema = z.object({
  nodes: z.array(z.record(z.unknown())),
  edges: z.array(z.record(z.unknown())),
});

export const citationSchema = z.object({
  document_id: z.string(),
  filename: z.string(),
  chapter_title: z.string().nullable().optional(),
  page_start: z.number(),
  page_end: z.number(),
  chunk_id: z.string(),
  passage: z.string().optional(),
});

export const tutorAnswerSchema = z.object({
  grounded: z.boolean(),
  confidence: z.enum(["high", "medium", "low"]),
  message: z.string(),
  citations: z.array(citationSchema),
  concept_ids: z.array(z.string()).optional(),
  followups: z.array(z.string()).optional(),
});

export const learningSessionSchema = z.object({
  id: z.string(),
  mode: z.string(),
  status: z.string(),
  concept_id: z.string(),
  concept_name: z.string(),
  because: z.string(),
  current_index: z.number(),
  sections: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      body: z.string(),
      understood: z.boolean(),
    }),
  ),
  current_section: z.string(),
});

export const quizAttemptSchema = z.object({
  id: z.string(),
  concept_id: z.string(),
  concept_name: z.string(),
  feedback_mode: z.enum(["immediate", "end"]),
  questions: z.array(
    z.object({
      id: z.string(),
      stem: z.string(),
      choices: z.array(z.string()),
      difficulty: z.enum(["easy", "medium", "hard"]),
      hint: z.string(),
      concept_tags: z.array(z.string()),
    }),
  ),
});

export const quizResultSchema = z.object({
  attempt_id: z.string(),
  correct: z.number(),
  total: z.number(),
  per_question: z.array(
    z.object({
      question_id: z.string(),
      selected_index: z.number(),
      correct_index: z.number(),
      explanation: z.string(),
      is_correct: z.boolean(),
    }),
  ),
  mastery: masteryScoreSchema,
  deltas: z.array(
    z.object({
      concept_id: z.string(),
      name: z.string(),
      before: z.number(),
      after: z.number(),
    }),
  ),
  next: z.object({
    mode: z.enum(["learn", "remedial", "revision", "retest"]),
    concept_id: z.string().nullable(),
    concept_name: z.string().optional(),
    because: z.string(),
  }),
});

export const learningPathSchema = z.object({
  items: z.array(
    z.object({
      concept_id: z.string(),
      name: z.string(),
      because: z.string(),
      kind: z.enum(["learn", "remedial", "retest", "revision", "next"]),
      band: masteryBandSchema.optional(),
    }),
  ),
});

export type Problem = z.infer<typeof problemSchema>;
export type TokenPair = z.infer<typeof tokenPairSchema>;
export type User = z.infer<typeof userSchema>;
export type MasteryScore = z.infer<typeof masteryScoreSchema>;
export type IngestionJob = z.infer<typeof ingestionJobSchema>;
export type DocumentRecord = z.infer<typeof documentSchema>;
export type Dashboard = z.infer<typeof dashboardSchema>;
export type GraphPayload = z.infer<typeof graphPayloadSchema>;
export type TutorAnswer = z.infer<typeof tutorAnswerSchema>;
export type Citation = z.infer<typeof citationSchema>;
export type LearningSession = z.infer<typeof learningSessionSchema>;
export type QuizAttemptView = z.infer<typeof quizAttemptSchema>;
export type QuizResult = z.infer<typeof quizResultSchema>;
export type LearningPath = z.infer<typeof learningPathSchema>;
