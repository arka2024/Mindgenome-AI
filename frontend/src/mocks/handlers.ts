import { http, HttpResponse, delay } from "msw";
import {
  C,
  CONCEPTS,
  CHAPTERS,
  DEFINITIONS,
  DEMO_EMAIL,
  DEMO_PASSWORD,
  EDGES,
  LESSONS,
  PASSAGE,
  QUIZZES,
  USER_ID,
} from "./seed";
import {
  advanceJob,
  applyQuiz,
  conceptName,
  dashboard,
  db,
  getMastery,
  graphPayload,
  issueTokens,
  userFromAuth,
  uid,
  resetStore,
} from "./store";
import { env } from "@/shared/lib/env";

const base = env.apiBaseUrl;

function problem(status: number, title: string, detail: string, type = "validation") {
  return HttpResponse.json(
    {
      type: `https://mindgenome.ai/problems/${type}`,
      title,
      status,
      detail,
      request_id: uid(),
    },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}

function requireUser(request: Request) {
  return userFromAuth(request.headers.get("Authorization"));
}

export const handlers = [
  http.post(`${base}/auth/login`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as { email: string; password: string };
    const user = db.users.find((u) => u.email === body.email && u.password === body.password);
    if (!user) return problem(401, "Unauthorized", "Unknown email or password.", "unauthorized");
    return HttpResponse.json(issueTokens(user.id));
  }),
  http.post(`${base}/auth/register`, async ({ request }) => {
    await delay(250);
    const body = (await request.json()) as { email: string; password: string; display_name: string };
    if (body.password.length < 12) {
      return problem(422, "Validation error", "Password must be at least 12 characters.");
    }
    if (db.users.some((u) => u.email === body.email)) {
      return problem(409, "Conflict", "An account already exists for that email.", "conflict");
    }
    const user = {
      id: uid(),
      email: body.email,
      password: body.password,
      display_name: body.display_name,
      roles: ["user"] as Array<"user" | "admin">,
    };
    db.users.push(user);
    return HttpResponse.json(issueTokens(user.id), { status: 201 });
  }),
  http.post(`${base}/auth/refresh`, async ({ request }) => {
    const body = (await request.json()) as { refresh_token: string };
    const rec = db.tokens.get(body.refresh_token);
    if (!rec || rec.kind !== "refresh") {
      return problem(401, "Unauthorized", "Refresh token expired. Sign in again.", "unauthorized");
    }
    db.tokens.delete(body.refresh_token);
    return HttpResponse.json(issueTokens(rec.userId));
  }),
  http.post(`${base}/auth/logout`, async ({ request }) => {
    const body = (await request.json()) as { refresh_token: string };
    db.tokens.delete(body.refresh_token);
    return new HttpResponse(null, { status: 204 });
  }),
  http.post(`${base}/auth/forgot`, async () => {
    await delay(300);
    return HttpResponse.json({ ok: true, message: "If that inbox exists, a reset link is on its way." });
  }),
  http.get(`${base}/auth/me`, ({ request }) => {
    const user = requireUser(request);
    if (!user) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    return HttpResponse.json({
      id: user.id,
      email: user.email,
      display_name: user.display_name,
      roles: user.roles,
    });
  }),
  http.get(`${base}/dashboard`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    return HttpResponse.json(dashboard());
  }),
  http.get(`${base}/documents`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const page_size = Number(url.searchParams.get("page_size") ?? 20);
    return HttpResponse.json({
      items: db.documents,
      page,
      page_size,
      total: db.documents.length,
    });
  }),
  http.post(`${base}/documents`, async ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    await delay(400);
    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) return problem(422, "Validation error", "file is required");
    const name = file.name.toLowerCase();
    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      return problem(415, "Upload rejected", "Only PDF and DOCX.", "upload-rejected");
    }
    if (file.size > 25 * 1024 * 1024) {
      return problem(413, "Upload rejected", "Max 25 MB.", "upload-rejected");
    }
    const document_id = uid();
    const job_id = uid();
    db.documents.unshift({
      id: document_id,
      filename: file.name,
      status: "uploaded",
      created_at: new Date().toISOString(),
      page_count: 12,
      job_id,
      is_low_text: false,
    });
    db.jobs.unshift({
      id: job_id,
      document_id,
      status: "queued",
      progress_pct: 5,
      tick: 0,
    });
    return HttpResponse.json({ document_id, job_id, status: "queued" }, { status: 202 });
  }),
  http.get(`${base}/documents/:id`, ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const doc = db.documents.find((d) => d.id === params.id);
    if (!doc) return problem(404, "Not found", "Document missing.", "not-found");
    return HttpResponse.json({ ...doc, chapters: CHAPTERS });
  }),
  http.delete(`${base}/documents/:id`, ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    db.documents = db.documents.filter((d) => d.id !== params.id);
    return new HttpResponse(null, { status: 204 });
  }),
  http.get(`${base}/ingestion-jobs/:id`, async ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    await delay(180);
    const job = db.jobs.find((j) => j.id === params.id);
    if (!job) return problem(404, "Not found", "Job missing.", "not-found");
    advanceJob(job);
    return HttpResponse.json({
      id: job.id,
      document_id: job.document_id,
      status: job.status,
      progress_pct: job.progress_pct,
      stage_detail: job.status,
      error_code: null,
      error_message: null,
    });
  }),
  http.get(`${base}/graph`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    return HttpResponse.json(graphPayload());
  }),
  http.post(`${base}/graph/edges/:id/review`, async ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const body = (await request.json()) as { decision: string };
    return HttpResponse.json({ edge_id: params.id, status: body.decision });
  }),
  http.post(`${base}/tutor/ask`, async ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const body = (await request.json()) as { question: string };
    await delay(350);
    const q = body.question.toLowerCase();
    if (q.includes("quantum") || q.includes("not in") || q.includes("weather") || q.includes("crypto")) {
      return HttpResponse.json({
        grounded: false,
        confidence: "low",
        message:
          "I cannot ground this in your uploaded material. The ingested ML textbook and notes do not discuss this topic.",
        citations: [],
        followups: [
          "What is gradient boosting in my notes?",
          "How does ensemble learning differ from bagging?",
          "Why are trees kept shallow in boosting?",
        ],
      });
    }

    if (q.includes("ensemble") || q.includes("weak learner") || q.includes("bagging")) {
      return HttpResponse.json({
        grounded: true,
        confidence: "high",
        message:
          "Ensemble learning combines multiple base models (weak learners) whose errors are not perfectly correlated. In your notes (§ Chap. 2 Ensembles), bagging builds models in parallel to cut variance, while boosting constructs them sequentially to reduce bias. Because Gradient Boosting is a sequential ensemble, weakness here directly compromises your understanding of residual fitting.",
        citations: [
          {
            document_id: db.documents[0]?.id ?? "doc-1",
            filename: db.documents[0]?.filename ?? "Hands-On Machine Learning (demo excerpt).pdf",
            chapter_title: "Ensembles",
            page_start: 29,
            page_end: 44,
            chunk_id: "cccccccc-0000-4000-8000-000000000002",
            passage:
              "Ensemble learning is the broader principle that many imperfect models, combined, outperform a single complex tree. In bagging, base estimators train independently on bootstrap replicates. In boosting, each new estimator targets the deficiencies of the previous ensemble.",
          },
        ],
        concept_ids: [C.ensemble, C.trees, C.boosting],
        followups: [
          "How does gradient boosting fit the residuals?",
          "Why is a weak learner preferred over a deep tree?",
          "How does random forest differ from boosting?",
        ],
      });
    }

    if (q.includes("tree") || q.includes("gini") || q.includes("split")) {
      return HttpResponse.json({
        grounded: true,
        confidence: "high",
        message:
          "Decision trees recursively partition the feature space into axis-aligned rectangular regions. According to Chapter 1, single unpruned trees suffer from high variance. In boosting, we deliberately restrict trees to small depths (often stumps or depth 2–4) to prevent early memorization of training noise.",
        citations: [
          {
            document_id: db.documents[0]?.id ?? "doc-1",
            filename: db.documents[0]?.filename ?? "Hands-On Machine Learning (demo excerpt).pdf",
            chapter_title: "Trees and splits",
            page_start: 12,
            page_end: 28,
            chunk_id: "cccccccc-0000-4000-8000-000000000003",
            passage:
              "A regression tree divides feature space into distinct regions with constant predictions. Unconstrained trees easily overfit. Modern boosting algorithms use shallow trees as weak learners to maintain controllable bias.",
          },
        ],
        concept_ids: [C.trees, C.ensemble],
        followups: [
          "What is information gain vs Gini impurity?",
          "How does boosting combine shallow trees?",
        ],
      });
    }

    return HttpResponse.json({
      grounded: true,
      confidence: "high",
      message:
        "Gradient boosting fits each new tree to the **negative gradient** of the loss (residuals for squared error). It is a sequential additive ensemble: each weak learner corrects remaining mistakes. If this feels slippery, the notes treat **Ensemble Learning** as the prerequisite — combining models whose errors are not perfectly correlated.",
      citations: [
        {
          document_id: db.documents[0]?.id ?? "doc-1",
          filename: db.documents[0]?.filename ?? "Hands-On Machine Learning (demo excerpt).pdf",
          chapter_title: "Gradient boosting",
          page_start: 45,
          page_end: 47,
          chunk_id: "cccccccc-0000-4000-8000-000000000001",
          passage: PASSAGE,
        },
      ],
      concept_ids: [C.gb, C.ensemble],
      followups: [
        "Why keep the trees shallow?",
        "How is this different from random forests?",
        "What should I study before XGBoost?",
      ],
    });
  }),
  http.get(`${base}/chunks/:id`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    return HttpResponse.json({
      id: paramsId(request),
      passage: PASSAGE,
      filename: db.documents[0]?.filename,
      chapter_title: "Gradient boosting",
      page_start: 45,
      page_end: 47,
    });
  }),
  http.post(`${base}/learning-sessions`, async ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const body = (await request.json()) as { mode: string; concept_id?: string };
    const concept_id = body.concept_id ?? C.gb;
    const id = uid();
    db.sessions.set(id, {
      id,
      mode: body.mode,
      concept_id,
      current_index: 0,
      understood: [],
    });
    return HttpResponse.json(sessionView(id), { status: 201 });
  }),
  http.get(`${base}/learning-sessions/:id`, ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const s = db.sessions.get(String(params.id));
    if (!s) return problem(404, "Not found", "Session missing.", "not-found");
    return HttpResponse.json(sessionView(s.id));
  }),
  http.post(`${base}/learning-sessions/:id/progress`, async ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const s = db.sessions.get(String(params.id));
    if (!s) return problem(404, "Not found", "Session missing.", "not-found");
    const body = (await request.json()) as { index?: number; understood_id?: string };
    if (typeof body.index === "number") s.current_index = body.index;
    if (body.understood_id && !s.understood.includes(body.understood_id)) {
      s.understood.push(body.understood_id);
    }
    return HttpResponse.json(sessionView(s.id));
  }),
  http.get(`${base}/quiz-attempts/:id`, ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const attempt = db.quizzes.get(String(params.id));
    const concept_id = attempt?.concept_id ?? C.gb;
    const quiz = QUIZZES[concept_id] ?? QUIZZES[C.gb];
    return HttpResponse.json({
      id: params.id,
      concept_id,
      concept_name: conceptName(concept_id),
      feedback_mode: "immediate",
      questions: quiz.map((q) => ({
        id: q.id,
        stem: q.stem,
        choices: q.choices,
        difficulty: q.difficulty,
        hint: q.hint,
        concept_tags: q.tags,
      })),
    });
  }),
  http.post(`${base}/quizzes`, async ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const body = (await request.json()) as { concept_id: string };
    const id = uid();
    const quiz = QUIZZES[body.concept_id] ?? QUIZZES[C.gb];
    db.quizzes.set(id, { concept_id: body.concept_id, questionIds: quiz.map((q) => q.id) });
    return HttpResponse.json(
      {
        id,
        attempt_id: id,
        concept_id: body.concept_id,
        concept_name: conceptName(body.concept_id),
        feedback_mode: "immediate",
        questions: quiz.map((q) => ({
          id: q.id,
          stem: q.stem,
          choices: q.choices,
          difficulty: q.difficulty,
          hint: q.hint,
          concept_tags: q.tags,
        })),
      },
      { status: 201 },
    );
  }),
  http.post(`${base}/store/reset`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    resetStore();
    return HttpResponse.json({ ok: true, message: "Store reset to initial state." });
  }),
  http.post(`${base}/quiz-attempts`, async ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const body = (await request.json()) as { concept_id: string };
    const id = uid();
    const quiz = QUIZZES[body.concept_id] ?? QUIZZES[C.gb];
    db.quizzes.set(id, { concept_id: body.concept_id, questionIds: quiz.map((q) => q.id) });
    return HttpResponse.json(
      {
        id,
        concept_id: body.concept_id,
        concept_name: conceptName(body.concept_id),
        feedback_mode: "immediate",
        questions: quiz.map((q) => ({
          id: q.id,
          stem: q.stem,
          choices: q.choices,
          difficulty: q.difficulty,
          hint: q.hint,
          concept_tags: q.tags,
        })),
      },
      { status: 201 },
    );
  }),
  http.post(`${base}/quiz-attempts/:id/submit`, async ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    await delay(280);
    const attempt = db.quizzes.get(String(params.id));
    if (!attempt) return problem(404, "Not found", "Attempt missing.", "not-found");
    const body = (await request.json()) as {
      answers: Array<{ question_id: string; selected_index: number }>;
    };
    const quiz = QUIZZES[attempt.concept_id] ?? QUIZZES[C.gb];
    const selected = quiz.map((q) => body.answers.find((a) => a.question_id === q.id)?.selected_index ?? -1);
    const result = applyQuiz(attempt.concept_id, selected);
    return HttpResponse.json({
      attempt_id: params.id,
      correct: result.correct,
      total: result.total,
      per_question: result.per,
      mastery: result.mastery,
      deltas: result.deltas,
      next: result.next,
    });
  }),
  http.get(`${base}/mastery`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    return HttpResponse.json({ items: db.mastery });
  }),
  http.get(`${base}/mastery/:id`, ({ request, params }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const row = getMastery(String(params.id));
    return HttpResponse.json({
      ...row,
      history: [
        { date: "2026-10-10", mastery: Math.max(10, row.mastery - 18) },
        { date: "2026-10-17", mastery: Math.max(12, row.mastery - 8) },
        { date: "2026-10-24", mastery: row.mastery },
      ],
    });
  }),
  http.get(`${base}/learning-path`, ({ request }) => {
    if (!requireUser(request)) return problem(401, "Unauthorized", "Sign in required.", "unauthorized");
    const ens = getMastery(C.ensemble);
    const gb = getMastery(C.gb);
    const items = [
      {
        concept_id: C.trees,
        name: "Decision Trees",
        because: "Already proficient — keep in light revision.",
        kind: "revision" as const,
        band: getMastery(C.trees).band,
      },
      {
        concept_id: C.ensemble,
        name: "Ensemble Learning",
        because:
          ens.mastery < 55
            ? "Recommended because Gradient Boosting depends on it and mastery is still low."
            : "Remedial complete — supporting GB.",
        kind: ens.mastery < 55 ? ("remedial" as const) : ("learn" as const),
        band: ens.band,
      },
      {
        concept_id: C.gb,
        name: "Gradient Boosting",
        because:
          gb.mastery < 61
            ? "Recommended next in the textbook chain; checkpoint will diagnose missing ensembles."
            : "Retest succeeded — continue to XGBoost.",
        kind: gb.mastery < 61 ? ("learn" as const) : ("retest" as const),
        band: gb.band,
      },
      {
        concept_id: C.xgb,
        name: "XGBoost",
        because: "Next concept once GB is proficient.",
        kind: "next" as const,
        band: getMastery(C.xgb).band,
      },
    ];
    return HttpResponse.json({ items });
  }),
  http.get(`${base}/health`, () => HttpResponse.json({ status: "ok" })),
];

function sessionView(id: string) {
  const s = db.sessions.get(id);
  if (!s) throw new Error("session");
  const sections = (LESSONS[s.concept_id] ?? LESSONS[C.gb]).map((sec) => ({
    ...sec,
    understood: s.understood.includes(sec.id),
  }));
  const current = sections[s.current_index] ?? sections[0];
  return {
    id: s.id,
    mode: s.mode,
    status: "active",
    concept_id: s.concept_id,
    concept_name: conceptName(s.concept_id),
    because:
      s.mode === "remedial"
        ? "Remedial because Ensemble Learning is the weak prerequisite under Gradient Boosting."
        : "Recommended because it sits on Decision Trees and ensembles in your graph.",
    current_index: s.current_index,
    sections,
    current_section: current?.title ?? "",
  };
}

function paramsId(request: Request): string {
  return new URL(request.url).pathname.split("/").pop() ?? "";
}

void CONCEPTS;
void DEFINITIONS;
void EDGES;
void DEMO_EMAIL;
void DEMO_PASSWORD;
void USER_ID;
