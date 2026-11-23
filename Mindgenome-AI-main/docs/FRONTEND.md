# Frontend architecture

Stack: React 18, TypeScript **strict**, Vite, Tailwind CSS, Cytoscape.js,
TanStack Query v5, Zustand (auth session + UI chrome only), React Router v6,
React Hook Form + Zod, `openapi-fetch` client generated from
`docs/openapi/openapi.yaml`.

## Folder structure (Sprint 1+)

```
frontend/
  index.html
  src/
    main.tsx
    app/
      router.tsx
      providers.tsx
    api/
      client.ts          # openapi-fetch wrapper, auth header, problem+json
      generated/         # CI-generated, gitignored
    auth/
      AuthGate.tsx
      session.ts         # Zustand: tokens in memory, refresh in httpOnly cookie preferred
    screens/
      LoginPage.tsx
      RegisterPage.tsx
      DashboardPage.tsx
      GenomePage.tsx
      UploadPage.tsx
      LearningPage.tsx
      TutorPage.tsx
      QuizPage.tsx
      MasteryPage.tsx
      PathPage.tsx
    components/
      genome/GenomeGraph.tsx   # Cytoscape adapter; no fetch inside
      citations/CitationList.tsx
      quiz/QuestionCard.tsx
      status/IngestionProgress.tsx
    design/
      tokens.css
      tailwind.css
    lib/
      a11y.ts
  tests/
```

Tokens live in memory. Refresh token: **httpOnly cookie** set by API on login
(preferred) with SPA using only the access token in memory. If cookie CORS on
Render is painful in S1, fall back to `localStorage` refresh **temporarily**
and track as a security debt in S8.

## Routes

| Path | Screen | Notes |
| --- | --- | --- |
| `/login` | Login | password + Google button |
| `/register` | Register | |
| `/auth/callback` | OAuth landing | |
| `/` | Dashboard | weak areas, jobs, path peek |
| `/genome` | Genome | Cytoscape from `GET /graph` |
| `/upload` | Upload + job poll | `GET /ingestion-jobs/{id}` |
| `/learn/:sessionId` | Learning mode | section + because |
| `/tutor` | Chat | citations required UI |
| `/quiz/:attemptId` | Quiz | no correct answers in payload |
| `/mastery` | Mastery / weak | bands + traces |
| `/path` | Learning path | because strings |

## Data fetching

- Server state: TanStack Query. Query keys include `userId`.
- Mutations invalidate mastery, graph, path, dashboard.
- Poll ingestion with `refetchInterval` while status not terminal.
- Cytoscape receives already-fetched elements; it does not own SoT.

## Design tokens (Tailwind)

| Token | Use |
| --- | --- |
| `bg-canvas` / `bg-surface` | page / cards |
| `text-primary` / `text-muted` | type |
| `accent` | primary actions |
| `band-beginner` … `band-mastered` | mastery chips |
| `danger` | errors, STRUGGLES_WITH |

Type scale: 14/16/20/24. Focus rings visible (`focus-visible:ring-2`).
Color is never the only signal (band chips also have text).

## Accessibility (WCAG 2.1 AA)

- Keyboard: all controls, Cytoscape has a list fallback of nodes/edges.
- Labels on every input; errors in `aria-live="polite"`.
- Contrast ≥ 4.5:1 for body text.
- Quiz: fieldset per question, `aria-describedby` for feedback after submit.
- Reduced motion: disable Cytoscape animation.
- Auth pages: autocomplete attributes, password managers work.

## Client-side citation rule

Do not render a tutor message as “grounded” unless `grounded===true` and
`citations.length>=1`. Low confidence shows the server `message` plus any
partial citations as “related passages”, not as proof.
