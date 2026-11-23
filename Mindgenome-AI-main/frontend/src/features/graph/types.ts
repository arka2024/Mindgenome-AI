import type { MasteryBand } from "@/shared/lib/mastery";

export type GraphNodeData = {
  id: string;
  label: string;
  kind: "concept" | "chapter" | "document";
  mastery?: number | null;
  band?: MasteryBand | null;
  definition?: string;
  parent?: string;
  document_id?: string;
};

export type GraphEdgeData = {
  id: string;
  source: string;
  target: string;
  kind: "RELATED_TO" | "USES" | "PART_OF" | "PREREQUISITE_OF";
};

export type GraphPayload = {
  nodes: Array<{ data: GraphNodeData }>;
  edges: Array<{ data: GraphEdgeData }>;
};

export type GraphFilterState = {
  search: string;
  band: MasteryBand | "all";
  edgeKind: GraphEdgeData["kind"] | "all";
  highlightPrereqsOnly: boolean;
};
