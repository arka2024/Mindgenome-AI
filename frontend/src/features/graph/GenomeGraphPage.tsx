import { useMemo, useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import { qk } from "@/shared/lib/queryKeys";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { CytoscapeCanvas } from "./CytoscapeCanvas";
import { NodeInspector } from "./NodeInspector";
import { GraphFilters } from "./GraphFilters";
import { AccessibleGraphTree } from "./AccessibleGraphTree";
import type { GraphFilterState, GraphPayload } from "./types";
import { List, Network } from "lucide-react";

export function GenomeGraphPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const focusParam = searchParams.get("focus");

  const [viewMode, setViewMode] = useState<"canvas" | "tree">("canvas");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(focusParam);
  const [highlightedLineageIds, setHighlightedLineageIds] = useState<string[]>([]);

  const [filters, setFilters] = useState<GraphFilterState>({
    search: "",
    band: "all",
    edgeKind: "all",
    highlightPrereqsOnly: false,
  });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.graph,
    queryFn: () => apiFetch<GraphPayload>("/graph"),
  });

  // Sync focus param to selected node
  useEffect(() => {
    if (focusParam) {
      setSelectedNodeId(focusParam);
    }
  }, [focusParam]);

  const allNodes = useMemo(() => data?.nodes.map((n) => n.data) ?? [], [data]);
  const allEdges = useMemo(() => data?.edges.map((e) => e.data) ?? [], [data]);

  // Filter nodes based on user search and filters
  const filteredNodes = useMemo(() => {
    return allNodes.filter((node) => {
      // Search filter
      if (filters.search) {
        const query = filters.search.toLowerCase();
        const matchesLabel = node.label.toLowerCase().includes(query);
        const matchesDef = node.definition?.toLowerCase().includes(query);
        if (!matchesLabel && !matchesDef) return false;
      }

      // Mastery band filter
      if (filters.band !== "all") {
        if (node.kind === "concept" && node.band !== filters.band) return false;
      }

      return true;
    });
  }, [allNodes, filters.search, filters.band]);

  // Filter edges based on visible nodes and edge relationship filter
  const filteredEdges = useMemo(() => {
    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));

    return allEdges.filter((edge) => {
      // Both source and target must be visible
      if (!visibleNodeIds.has(edge.source) || !visibleNodeIds.has(edge.target)) {
        return false;
      }

      // Edge relationship filter
      if (filters.edgeKind !== "all") {
        if (edge.kind !== filters.edgeKind) return false;
      }

      return true;
    });
  }, [allEdges, filteredNodes, filters.edgeKind]);

  // Prerequisite lineage traversal
  const handleHighlightLineage = (nodeId: string) => {
    if (highlightedLineageIds.includes(nodeId)) {
      setHighlightedLineageIds([]);
      return;
    }

    const lineage = new Set<string>([nodeId]);
    const queue = [nodeId];

    // Breadth-first search backward through prerequisite edges
    while (queue.length > 0) {
      const current = queue.shift()!;
      // Find edges where current node is target (meaning source is a prerequisite of current)
      const prereqEdges = allEdges.filter(
        (e) => e.target === current && (e.kind === "PREREQUISITE_OF" || e.kind === "USES"),
      );

      for (const edge of prereqEdges) {
        if (!lineage.has(edge.source)) {
          lineage.add(edge.source);
          queue.push(edge.source);
        }
      }
    }

    setHighlightedLineageIds(Array.from(lineage));
  };

  const handleSelectNode = (id: string | null) => {
    setSelectedNodeId(id);
    if (id) {
      setSearchParams({ focus: id });
    } else {
      searchParams.delete("focus");
      setSearchParams(searchParams);
      setHighlightedLineageIds([]);
    }
  };

  const selectedNode = allNodes.find((n) => n.id === selectedNodeId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-8 w-32" />
        </div>
        <Skeleton className="h-[600px] w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        title="Knowledge Graph Unavailable"
        body="Could not load the semantic knowledge graph telemetry."
        action="Retry"
        onAction={() => void refetch()}
      />
    );
  }

  return (
    <div className="flex flex-col space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-3xl font-bold sm:text-4xl">Knowledge Genome</h1>
            <span className="rounded-full bg-helix/10 px-2.5 py-0.5 text-xs font-semibold text-helix border border-helix/30">
              Interactive Canvas
            </span>
          </div>
          <p className="mt-1 text-sm text-muted">
            Explore your cognitive map. Colored by mastery, connected by prerequisite dependencies.
          </p>
        </div>

        {/* View Switcher (Canvas vs Accessible Tree) */}
        <div className="flex items-center gap-2 self-start sm:self-center">
          <div className="flex rounded-control border border-line bg-surface p-1 text-xs">
            <button
              onClick={() => setViewMode("canvas")}
              className={`flex items-center gap-1.5 rounded px-3 py-1.5 font-semibold transition ${
                viewMode === "canvas" ? "bg-helix text-white" : "text-muted hover:text-ink"
              }`}
            >
              <Network className="h-3.5 w-3.5" />
              <span>Canvas</span>
            </button>
            <button
              onClick={() => setViewMode("tree")}
              className={`flex items-center gap-1.5 rounded px-3 py-1.5 font-semibold transition ${
                viewMode === "tree" ? "bg-helix text-white" : "text-muted hover:text-ink"
              }`}
            >
              <List className="h-3.5 w-3.5" />
              <span>Accessible Tree</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter Rail */}
      <GraphFilters
        filters={filters}
        onChange={(next) => setFilters((prev) => ({ ...prev, ...next }))}
        onReset={() =>
          setFilters({ search: "", band: "all", edgeKind: "all", highlightPrereqsOnly: false })
        }
      />

      {/* Main Graph Content Area */}
      <div className="relative grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[600px] h-[calc(100vh-280px)]">
        {/* Graph Canvas or Tree Area */}
        <div
          className={`h-full transition-all duration-300 ${
            selectedNode ? "lg:col-span-8" : "lg:col-span-12"
          }`}
        >
          {viewMode === "canvas" ? (
            <CytoscapeCanvas
              nodes={filteredNodes}
              edges={filteredEdges}
              selectedNodeId={selectedNodeId}
              highlightedLineageIds={highlightedLineageIds}
              onSelectNode={handleSelectNode}
            />
          ) : (
            <div className="h-full overflow-y-auto rounded-sheet border border-line bg-canvas p-4">
              <AccessibleGraphTree
                nodes={filteredNodes}
                edges={filteredEdges}
                selectedNodeId={selectedNodeId}
                onSelectNode={handleSelectNode}
              />
            </div>
          )}
        </div>

        {/* Sliding Node Inspector Panel */}
        {selectedNode && (
          <div className="lg:col-span-4 h-full rounded-sheet overflow-hidden border border-line animate-in fade-in slide-in-from-right-4 duration-200">
            <NodeInspector
              node={selectedNode}
              allNodes={allNodes}
              edges={allEdges}
              onClose={() => handleSelectNode(null)}
              onSelectNode={handleSelectNode}
              onHighlightLineage={handleHighlightLineage}
              isLineageHighlighted={highlightedLineageIds.includes(selectedNode.id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
