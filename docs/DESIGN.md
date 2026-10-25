# MindGenome AI — Phase 0 design system

## Design brief — “Helix lab at dusk”

Calm scientific instrument, not a purple AI template. Warm paper in light mode,
deep ink-green in dark mode, teal helix + copper annotation as the only accents.

| Layer | Choice |
| --- | --- |
| Mood | Quiet lab, living map, earned mastery |
| Light canvas | `#F4F0E8` paper; surface `#FFFBF5`; ink `#1C2321` |
| Dark canvas | `#101614`; surface `#18201D`; ink `#E8EDE9` |
| Helix (accent) | `#0F6E6B` light / `#4ECDC4` dark |
| Copper (secondary) | `#B86B3D` / `#E09A6A` |
| Display | Fraunces (optical size 9–144, 500/650) |
| Body / UI | Source Sans 3 (400/600) |
| Citations / code | IBM Plex Mono |
| Spacing | 4px base: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 |
| Radius | 6px controls, 12px cards, 20px sheets |
| Shadow | Single soft umbra, copper-tinted 8% — no stacked glow |
| Motion | 180ms ease-out; graph layout may take longer; honor `prefers-reduced-motion` |

Mastery bands (icon + label required; color is secondary):

| Band | Range | Mark |
| --- | --- | --- |
| Beginner | 0–30 | Sprout |
| Developing | 31–60 | Stem |
| Proficient | 61–80 | Leaf |
| Mastered | 81–100 | Helix |

Insufficient evidence is a fifth API band; UI shows “Not enough quizzes yet”.

## Information architecture

- **Public:** story, proof, pricing placeholder, about placeholder, sign-in.
- **App:** Genome home is the default. Documents feed the graph. Learn / quiz /
  tutor / path are actions on concepts, not separate products.
- **Command palette** is the power-user IA: jump to concept, document, or action.

## Sitemap

```
/                         marketing
/pricing                  placeholder
/about                    placeholder
/login /register /forgot
/styleguide               design system
/app                      dashboard (genome home)
/app/documents            library + upload
/app/documents/:id        processing + chapters
/app/genome               graph explorer
/app/tutor                grounded chat
/app/learn/:sessionId     sectional lesson
/app/quiz/:attemptId      checkpoint
/app/mastery              table + heatmap
/app/path                 adaptive roadmap
/app/settings             account + preferences
```

## User flows (happy path demo)

1. Register or demo login → empty-ish dashboard with recommended upload.
2. Upload ML PDF → stepper queued→…→ready (poll).
3. Open genome → Gradient Boosting node (beginner) → Learn this.
4. Finish sections → checkpoint quiz → 2/5.
5. Diagnosis: weak prerequisite Ensemble Learning → remedial lesson → retest 4/5.
6. Dashboard + graph colors update; path advances to XGBoost.

## Screen layouts (wireframe-level)

- **Landing:** full-bleed hero (display headline + SVG mini-graph), 5-step loop
  as a horizontal scroller on mobile, four feature bands, product preview frame,
  FAQ accordion, copper CTA bar, footer.
- **Dashboard:** 12-col. Left 8: mastery ring, band counts, growth chart, mini
  graph. Right 4: recommended next, weak list, revisions, activity. Mobile:
  recommended first, then ring, then lists; mini graph behind a “Open map” button.
- **Graph:** canvas + left filter rail (collapses to sheet) + right inspector.
  Mobile: Map | List tabs; inspector is a bottom sheet.
- **Tutor:** message column, citation chips, source drawer; suggested questions
  under composer.
- **Learn:** progress bar, section prose, mark understood, ask tutor, checkpoint CTA.
- **Quiz:** one stem, radio fieldset, hint, footer next; results: score, deltas,
  diagnosis card, remedial CTA.
- **Upload:** dropzone + queue; document page is a vertical stepper + chapter list.

## Folder structure (frontend)

Feature slices under `frontend/src/features/*`, primitives under `shared/ui`,
API + env under `shared/lib` and `api`, routes under `app/`.

## Defaults locked with this build

- Hosting: Vercel (SPA) + Render API (`infra/render.yaml`).
- Auth: access token in memory; refresh in `sessionStorage` until httpOnly
  cookies work on the API host (ADR-012).
- Mocks on by default (`VITE_USE_MOCKS=true`) so the UI demos without FastAPI.
