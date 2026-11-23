import { bandFromScore, computeMastery, type MasteryBand } from "@/shared/lib/mastery";

export const DEMO_EMAIL = "learner@mindgenome.ai";
export const DEMO_PASSWORD = "learn-genome-24";
export const USER_ID = "aaaaaaaa-bbbb-4ccc-8ddd-000000000001";
export const DOC_ID = "dddddddd-0000-4000-8000-000000000001";
export const JOB_ID = "jjjjjjjj-0000-4000-8000-000000000001";
export const CHUNK_ID = "cccccccc-0000-4000-8000-000000000001";

export function cid(n: number): string {
  return `cccccccc-0000-4000-8000-${String(n).padStart(12, "0")}`;
}

export const CONCEPTS = [
  { id: cid(1), name: "Supervised Learning" },
  { id: cid(2), name: "Unsupervised Learning" },
  { id: cid(3), name: "Loss Functions" },
  { id: cid(4), name: "Gradient Descent" },
  { id: cid(5), name: "Overfitting" },
  { id: cid(6), name: "Bias-Variance" },
  { id: cid(7), name: "Train-Test Split" },
  { id: cid(8), name: "Cross-Validation" },
  { id: cid(9), name: "Feature Engineering" },
  { id: cid(10), name: "Decision Trees" },
  { id: cid(11), name: "Information Gain" },
  { id: cid(12), name: "Gini Impurity" },
  { id: cid(13), name: "Pruning" },
  { id: cid(14), name: "Ensemble Learning" },
  { id: cid(15), name: "Bagging" },
  { id: cid(16), name: "Random Forests" },
  { id: cid(17), name: "Boosting" },
  { id: cid(18), name: "AdaBoost" },
  { id: cid(19), name: "Gradient Boosting" },
  { id: cid(20), name: "XGBoost" },
  { id: cid(21), name: "LightGBM" },
  { id: cid(22), name: "Regularization" },
  { id: cid(23), name: "Learning Rate" },
  { id: cid(24), name: "Weak Learners" },
  { id: cid(25), name: "Residuals" },
  { id: cid(26), name: "CART" },
  { id: cid(27), name: "Hyperparameter Tuning" },
  { id: cid(28), name: "Early Stopping" },
  { id: cid(29), name: "Feature Importance" },
  { id: cid(30), name: "Partial Dependence" },
  { id: cid(31), name: "Classification Metrics" },
  { id: cid(32), name: "ROC-AUC" },
  { id: cid(33), name: "Precision-Recall" },
  { id: cid(34), name: "Neural Networks" },
  { id: cid(35), name: "k-NN" },
  { id: cid(36), name: "SVM" },
  { id: cid(37), name: "Naive Bayes" },
  { id: cid(38), name: "Linear Regression" },
  { id: cid(39), name: "Logistic Regression" },
  { id: cid(40), name: "PCA" },
  { id: cid(41), name: "Clustering" },
  { id: cid(42), name: "k-Means" },
  { id: cid(43), name: "Model Selection" },
  { id: cid(44), name: "Calibration" },
] as const;

export const C = {
  trees: cid(10),
  ensemble: cid(14),
  boosting: cid(17),
  gb: cid(19),
  xgb: cid(20),
};

type EdgeKind = "PREREQUISITE_OF" | "RELATED_TO" | "USES" | "PART_OF";

export const EDGES: Array<{ id: string; source: string; target: string; kind: EdgeKind }> = [
  { id: "e1", source: cid(1), target: cid(10), kind: "PREREQUISITE_OF" },
  { id: "e2", source: cid(10), target: cid(14), kind: "PREREQUISITE_OF" },
  { id: "e3", source: cid(14), target: cid(17), kind: "PREREQUISITE_OF" },
  { id: "e4", source: cid(17), target: cid(19), kind: "PREREQUISITE_OF" },
  { id: "e5", source: cid(19), target: cid(20), kind: "PREREQUISITE_OF" },
  { id: "e6", source: cid(19), target: cid(21), kind: "PREREQUISITE_OF" },
  { id: "e7", source: cid(14), target: cid(15), kind: "PART_OF" },
  { id: "e8", source: cid(14), target: cid(17), kind: "PART_OF" },
  { id: "e9", source: cid(15), target: cid(16), kind: "PREREQUISITE_OF" },
  { id: "e10", source: cid(10), target: cid(26), kind: "RELATED_TO" },
  { id: "e11", source: cid(11), target: cid(10), kind: "USES" },
  { id: "e12", source: cid(12), target: cid(10), kind: "USES" },
  { id: "e13", source: cid(24), target: cid(17), kind: "USES" },
  { id: "e14", source: cid(25), target: cid(19), kind: "USES" },
  { id: "e15", source: cid(23), target: cid(19), kind: "USES" },
  { id: "e16", source: cid(4), target: cid(19), kind: "PREREQUISITE_OF" },
  { id: "e17", source: cid(3), target: cid(4), kind: "PREREQUISITE_OF" },
  { id: "e18", source: cid(5), target: cid(22), kind: "RELATED_TO" },
  { id: "e19", source: cid(6), target: cid(5), kind: "RELATED_TO" },
  { id: "e20", source: cid(17), target: cid(18), kind: "PART_OF" },
  { id: "e21", source: cid(22), target: cid(20), kind: "USES" },
  { id: "e22", source: cid(28), target: cid(20), kind: "USES" },
  { id: "e23", source: cid(31), target: cid(32), kind: "PART_OF" },
  { id: "e24", source: cid(31), target: cid(33), kind: "PART_OF" },
  { id: "e25", source: cid(38), target: cid(39), kind: "RELATED_TO" },
  { id: "e26", source: cid(2), target: cid(41), kind: "PREREQUISITE_OF" },
  { id: "e27", source: cid(41), target: cid(42), kind: "PART_OF" },
  { id: "e28", source: cid(40), target: cid(2), kind: "RELATED_TO" },
  { id: "e29", source: cid(13), target: cid(10), kind: "USES" },
  { id: "e30", source: cid(27), target: cid(20), kind: "USES" },
  { id: "e31", source: cid(8), target: cid(43), kind: "USES" },
  { id: "e32", source: cid(7), target: cid(8), kind: "PREREQUISITE_OF" },
];

export const DEFINITIONS: Record<string, string> = {
  [C.trees]:
    "A tree of axis-aligned splits that partitions the feature space into regions with constant predictions.",
  [C.ensemble]:
    "A family of methods that combine many base models so the committee is more stable and accurate than any member.",
  [C.boosting]:
    "An ensemble strategy that trains weak learners sequentially, each focusing on remaining errors.",
  [C.gb]:
    "Boosting that fits each new tree to the negative gradient (residuals) of a differentiable loss.",
  [C.xgb]:
    "A regularized, systems-optimized implementation of gradient boosting with sparsity-aware splits.",
};

type Answer = { correct: boolean; difficulty: string; ageDays: number };

function scoreFrom(answers: Answer[], revisions = 1) {
  const lastCorrect = answers.find((a) => a.correct);
  const parts = computeMastery({
    answers,
    successfulRevisions: revisions,
    daysSinceLastCorrect: lastCorrect ? lastCorrect.ageDays : null,
  });
  const band = bandFromScore(parts.mastery, answers.length) as MasteryBand;
  return { ...parts, evidence_n: answers.length, band };
}

function mix(n: number, correctRate: number, age = 4): Answer[] {
  return Array.from({ length: n }, (_, i) => ({
    correct: i < Math.round(n * correctRate),
    difficulty: i % 3 === 0 ? "hard" : i % 2 === 0 ? "medium" : "easy",
    ageDays: age,
  }));
}

export type MasteryRow = ReturnType<typeof scoreFrom> & { concept_id: string; name: string };

export function initialMastery(): MasteryRow[] {
  return CONCEPTS.map((c, i) => {
    if (c.id === C.gb) {
      const s = scoreFrom(mix(5, 0.4, 6));
      return { ...s, concept_id: c.id, name: c.name };
    }
    if (c.id === C.ensemble) {
      const s = scoreFrom(mix(4, 0.25, 10));
      return { ...s, concept_id: c.id, name: c.name };
    }
    if (c.id === C.trees) {
      const s = scoreFrom(mix(8, 0.85, 2));
      return { ...s, concept_id: c.id, name: c.name };
    }
    if (c.id === C.boosting) {
      const s = scoreFrom(mix(5, 0.55, 8));
      return { ...s, concept_id: c.id, name: c.name };
    }
    if (c.id === C.xgb) {
      const s = scoreFrom([], 0);
      return { ...s, concept_id: c.id, name: c.name, band: "insufficient_evidence" as const };
    }
    const rate = 0.45 + ((i * 17) % 40) / 100;
    const s = scoreFrom(mix(5 + (i % 4), rate, 3 + (i % 10)));
    return { ...s, concept_id: c.id, name: c.name };
  });
}

export const PASSAGE =
  "Gradient boosting builds an additive model in a forward stage-wise fashion. At each stage, a regression tree is fit on the negative gradient of the loss with respect to the current prediction — the residual for squared error. Ensemble learning is the broader idea that many weak learners, combined, outperform a single complex tree. If boosting is unstable, inspect whether the learner understands ensembles and residual fitting before introducing shrinkage and column subsampling (as in XGBoost).";

export const LESSONS: Record<string, Array<{ id: string; title: string; body: string }>> = {
  [C.gb]: [
    {
      id: "gb-1",
      title: "Additive stage-wise fitting",
      body: "Gradient boosting starts from a constant prediction and adds a new tree that points downhill on the loss surface. Each tree is small on purpose: it is a weak learner.",
    },
    {
      id: "gb-2",
      title: "Residuals are the training signal",
      body: "For squared error, the negative gradient is simply the residual y − ŷ. Later trees therefore train on what earlier trees got wrong — not on the original labels.",
    },
    {
      id: "gb-3",
      title: "Shrinkage and complexity",
      body: "A learning rate η scales every tree. Small η plus more trees usually generalizes better than one aggressive tree. This only works if the ensemble idea already makes sense.",
    },
  ],
  [C.ensemble]: [
    {
      id: "ens-1",
      title: "Why a committee beats a star",
      body: "A single deep tree memorizes quirks. Several imperfect models, whose errors are not perfectly correlated, cancel noise. That is ensemble learning.",
    },
    {
      id: "ens-2",
      title: "Bagging vs boosting",
      body: "Bagging trains models in parallel on bootstrap samples (random forests). Boosting trains them in sequence on reweighted or residual errors. Same family, different dependence structure.",
    },
    {
      id: "ens-3",
      title: "Weak learners",
      body: "A weak learner is only slightly better than chance — a stump, a shallow tree. Boosting’s bet is that many such learners, stacked on residuals, become strong.",
    },
  ],
};

export const QUIZZES: Record<
  string,
  Array<{
    id: string;
    stem: string;
    choices: string[];
    correct: number;
    difficulty: "easy" | "medium" | "hard";
    hint: string;
    explanation: string;
    tags: string[];
  }>
> = {
  [C.gb]: [
    {
      id: "q-gb-1",
      stem: "What does each new tree in gradient boosting typically fit?",
      choices: [
        "The original labels y",
        "The negative gradient of the loss (residuals for squared error)",
        "Random bootstrap targets",
        "The principal components of X",
      ],
      correct: 1,
      difficulty: "easy",
      hint: "Think downhill on the loss, not downhill on y.",
      explanation: "Trees are fit to the negative gradient. For squared error that is the residual.",
      tags: ["Gradient Boosting", "Residuals"],
    },
    {
      id: "q-gb-2",
      stem: "Gradient boosting is best described as which kind of ensemble?",
      choices: ["Parallel bagging", "Sequential additive boosting", "A single pruned CART", "k-means voting"],
      correct: 1,
      difficulty: "easy",
      hint: "Trees arrive one after another.",
      explanation: "Boosting is sequential; bagging is parallel.",
      tags: ["Ensemble Learning", "Boosting"],
    },
    {
      id: "q-gb-3",
      stem: "Why keep individual trees shallow?",
      choices: [
        "Shallow trees are weak learners whose errors boosting can correct",
        "Deep trees cannot split on numeric features",
        "XGBoost forbids depth > 1",
        "Shallow trees maximize variance on purpose",
      ],
      correct: 0,
      difficulty: "medium",
      hint: "Weak learners, not memorizing stars.",
      explanation: "Boosting assumes weak, high-bias trees; depth would overfit early stages.",
      tags: ["Weak Learners", "Gradient Boosting"],
    },
    {
      id: "q-gb-4",
      stem: "A small learning rate η usually requires…",
      choices: [
        "Fewer trees",
        "More trees to reach the same training loss",
        "No regularization",
        "Dropping residuals",
      ],
      correct: 1,
      difficulty: "medium",
      hint: "Shrinkage slows the additive model.",
      explanation: "Each tree is scaled by η, so you need more stages for the same fit, typically with better generalization.",
      tags: ["Learning Rate"],
    },
    {
      id: "q-gb-5",
      stem: "If you miss questions about combining models, which prerequisite is most likely weak?",
      choices: ["PCA", "Ensemble Learning", "k-Means", "Calibration"],
      correct: 1,
      difficulty: "hard",
      hint: "The family above boosting.",
      explanation: "Gradient boosting is a boosting method; boosting is a kind of ensemble. Weak ensemble mastery blocks GB.",
      tags: ["Ensemble Learning", "Gradient Boosting"],
    },
  ],
  [C.ensemble]: [
    {
      id: "q-ens-1",
      stem: "The core bet of ensemble learning is that…",
      choices: [
        "One deep model always wins",
        "Uncorrelated errors of many models cancel",
        "Labels should be shuffled each epoch",
        "Features must be independent given the class",
      ],
      correct: 1,
      difficulty: "easy",
      hint: "Diversity of errors.",
      explanation: "Variance falls when errors are not perfectly correlated.",
      tags: ["Ensemble Learning"],
    },
    {
      id: "q-ens-2",
      stem: "Bagging trains base learners…",
      choices: ["Sequentially on residuals", "In parallel on bootstrap samples", "Only on misclassified rows", "With a shared hidden layer"],
      correct: 1,
      difficulty: "easy",
      hint: "Bootstrap aggregating.",
      explanation: "Bagging is parallel; boosting is sequential.",
      tags: ["Bagging"],
    },
    {
      id: "q-ens-3",
      stem: "A weak learner is…",
      choices: [
        "Slightly better than chance",
        "Always a neural net",
        "A model with zero bias",
        "Unusable in boosting",
      ],
      correct: 0,
      difficulty: "medium",
      hint: "Stumps qualify.",
      explanation: "Weak ≠ useless; boosting accumulates many weak learners.",
      tags: ["Weak Learners"],
    },
    {
      id: "q-ens-4",
      stem: "Random forests are primarily…",
      choices: ["Boosted stumps", "Bagged trees with feature randomness", "A single CART with pruning", "Gradient descent on residuals"],
      correct: 1,
      difficulty: "medium",
      hint: "Forest ≈ bagging + extra randomness.",
      explanation: "RF is bagging of trees plus split-feature sampling.",
      tags: ["Random Forests", "Bagging"],
    },
    {
      id: "q-ens-5",
      stem: "Boosting differs from bagging because models are…",
      choices: ["Independent given the bootstrap", "Dependent: each stage targets remaining error", "Trained on PCA scores only", "Averaged with equal weights always"],
      correct: 1,
      difficulty: "hard",
      hint: "Sequence vs committee vote.",
      explanation: "Boosting’s additive stages are not exchangeable bootstrap replicates.",
      tags: ["Boosting", "Ensemble Learning"],
    },
  ],
};

export const CHAPTERS = [
  { id: "ch-1", title: "Trees and splits", page_start: 12, page_end: 28 },
  { id: "ch-2", title: "Ensembles", page_start: 29, page_end: 44 },
  { id: "ch-3", title: "Gradient boosting", page_start: 45, page_end: 62 },
  { id: "ch-4", title: "XGBoost and systems tricks", page_start: 63, page_end: 80 },
];
