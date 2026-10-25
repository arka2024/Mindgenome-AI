# ADR-013: Cytoscape Knowledge Graph Performance & Mobile Virtualization

Status: accepted

## Context
MindGenome AI centers on an interactive semantic knowledge graph that can scale from dozens of concepts to 1,000+ nodes and edges (concepts, chapters, documents, prerequisites). On mobile or low-power devices, rendering heavy force-directed physics or thousands of canvas labels causes dropped frames and poor touch ergonomics.

## Decision
1. **Desktop Engine**: Cytoscape.js with `fcose` (fast compound spring embedder) or `cose-bilkent` for layout calculation. Layout positions are computed once, cached in memory per document context, and reused across filter interactions.
2. **Level-of-Detail (LOD)**:
   - Zoom < 0.6: Hide node text labels, show only color-coded mastery rings and cluster centroids.
   - Zoom 0.6–1.2: Render primary concept labels with ellipsis.
   - Zoom > 1.2: Render full labels, badge chips, and relationship labels.
3. **Responsive Mobile Fallback**:
   - On screens < 768px, render a dual-mode toggle: `Interactive Tree/List` (primary default) and `Minimap Canvas`. The tree view presents the exact same semantic data grouped by chapters with prerequisite chips, full keyboard accessibility, and search.
4. **Prerequisite Highlight Path**:
   - Selecting a node executes an immediate directed breadth-first traversal up the `PREREQUISITE_OF` and `USES` edge tree, dimming non-relevant nodes (opacity 0.15) and pulsing the prerequisite lineage with amber/teal strokes.

## Consequences
- Guarantees 60fps canvas interaction even on larger documents.
- Satisfies WCAG 2.1 AA keyboard accessibility requirements via the accessible tree alternative.
