export const MASTERY_BANDS = ["beginner", "developing", "proficient", "mastered"] as const;

export type MasteryBand = (typeof MASTERY_BANDS)[number] | "insufficient_evidence";

export function bandFromScore(score: number | null, evidenceN: number): MasteryBand {
  if (evidenceN < 3 || score === null) return "insufficient_evidence";
  if (score <= 30) return "beginner";
  if (score <= 60) return "developing";
  if (score <= 80) return "proficient";
  return "mastered";
}

export function bandLabel(band: MasteryBand): string {
  switch (band) {
    case "beginner":
      return "Beginner";
    case "developing":
      return "Developing";
    case "proficient":
      return "Proficient";
    case "mastered":
      return "Mastered";
    default:
      return "Not enough evidence";
  }
}

export function bandRange(band: MasteryBand): string {
  switch (band) {
    case "beginner":
      return "0–30";
    case "developing":
      return "31–60";
    case "proficient":
      return "61–80";
    case "mastered":
      return "81–100";
    default:
      return "n < 3";
  }
}

const DIFFICULTY: Record<string, number> = { easy: 0.7, medium: 1, hard: 1.3 };

export function computeMastery(args: {
  answers: Array<{ correct: boolean; difficulty: string; ageDays: number }>;
  successfulRevisions: number;
  daysSinceLastCorrect: number | null;
}): {
  mastery: number;
  quiz_accuracy: number;
  recent_performance: number;
  difficulty_adjusted: number;
  retention: number;
} {
  const { answers, successfulRevisions, daysSinceLastCorrect } = args;
  const n = answers.length;
  if (n === 0) {
    return {
      mastery: 0,
      quiz_accuracy: 0,
      recent_performance: 0,
      difficulty_adjusted: 0,
      retention: 0,
    };
  }
  const acc = (100 * answers.filter((a) => a.correct).length) / n;
  const lambda = Math.LN2 / 14;
  const recNum = answers.reduce(
    (s, a) => s + Math.exp(-lambda * a.ageDays) * (a.correct ? 1 : 0),
    0,
  );
  const recDen = answers.reduce((s, a) => s + Math.exp(-lambda * a.ageDays), 0);
  const rec = recDen === 0 ? 0 : (100 * recNum) / recDen;
  const dapNum = answers.reduce(
    (s, a) => s + (a.correct ? 1 : 0) * (DIFFICULTY[a.difficulty] ?? 1),
    0,
  );
  const dapDen = answers.reduce((s, a) => s + (DIFFICULTY[a.difficulty] ?? 1), 0);
  const dap = dapDen === 0 ? 0 : (100 * dapNum) / dapDen;
  const stability = Math.min(60, 7 * (1 + 0.5 * successfulRevisions));
  const ret =
    daysSinceLastCorrect === null ? 0 : 100 * Math.exp(-daysSinceLastCorrect / stability);
  const mastery = 0.4 * acc + 0.2 * rec + 0.2 * dap + 0.2 * ret;
  return {
    mastery: round1(mastery),
    quiz_accuracy: round1(acc),
    recent_performance: round1(rec),
    difficulty_adjusted: round1(dap),
    retention: round1(ret),
  };
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

export function validateUpload(file: File): string | null {
  const allowed = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];
  const nameOk = /\.(pdf|docx)$/i.test(file.name);
  if (!nameOk && !allowed.includes(file.type)) {
    return "Only PDF and DOCX files are accepted.";
  }
  if (file.size > 25 * 1024 * 1024) {
    return "File must be 25 MB or smaller.";
  }
  return null;
}
