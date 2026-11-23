export const qk = {
  me: ["me"] as const,
  dashboard: ["dashboard"] as const,
  documents: ["documents"] as const,
  document: (id: string) => ["documents", id] as const,
  job: (id: string) => ["ingestion-jobs", id] as const,
  graph: ["graph"] as const,
  mastery: ["mastery"] as const,
  masteryOne: (id: string) => ["mastery", id] as const,
  path: ["learning-path"] as const,
  session: (id: string) => ["learning-sessions", id] as const,
  quiz: (id: string) => ["quiz-attempts", id] as const,
};
