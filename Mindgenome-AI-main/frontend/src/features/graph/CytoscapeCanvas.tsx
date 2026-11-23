import { useEffect, useRef, useState } from "react";
import cytoscape, { type Core, type EventObject } from "cytoscape";
import fcose from "cytoscape-fcose";
import type { GraphEdgeData, GraphNodeData } from "./types";
import { Button } from "@/shared/ui/Button";
import { Maximize2, Minus, Plus, RefreshCw } from "lucide-react";

// Register fcose layout extension safely
if (typeof cytoscape === "function") {
  try {
    cytoscape.use(fcose);
  } catch {
    /* already registered or testing environment */
  }
}

export function CytoscapeCanvas({
  nodes,
  edges,
  selectedNodeId,
  highlightedLineageIds,
  onSelectNode,
}: {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
  selectedNodeId: string | null;
  highlightedLineageIds: string[];
  onSelectNode: (id: string | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  // Initialize and update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current) return;

    // Build Cytoscape element definitions
    const elements = [
      ...nodes.map((n) => ({
        data: {
          id: n.id,
          label: n.label,
          kind: n.kind,
          mastery: n.mastery ?? 0,
          band: n.band ?? "insufficient_evidence",
        },
      })),
      ...edges.map((e) => ({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          kind: e.kind,
        },
      })),
    ];

    try {
      const cy = cytoscape({
        container: containerRef.current,
        elements,
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "font-family": "Source Sans 3, sans-serif",
              "font-size": 10,
              "text-valign": "bottom",
              "text-margin-y": 5,
              color: "#1C2321",
              "background-color": "#94A3B8",
              width: 28,
              height: 28,
              "border-width": 2,
              "border-color": "#CBD5E1",
              "transition-property": "opacity, border-color, border-width, width, height",
              "transition-duration": 200,
            },
          },
          // Node styling by Mastery Band
          {
            selector: "node[band = 'mastered']",
            style: { "background-color": "#15803D", "border-color": "#4ADE80" },
          },
          {
            selector: "node[band = 'proficient']",
            style: { "background-color": "#0F766E", "border-color": "#2DD4BF" },
          },
          {
            selector: "node[band = 'developing']",
            style: { "background-color": "#2563EB", "border-color": "#60A5FA" },
          },
          {
            selector: "node[band = 'beginner']",
            style: { "background-color": "#B45309", "border-color": "#FBBF24" },
          },
          {
            selector: "node[kind = 'chapter']",
            style: {
              shape: "round-rectangle",
              width: 44,
              height: 32,
              "background-color": "#0F6E6B",
              "border-color": "#4ECDC4",
              "border-width": 3,
              "font-size": 11,
              "font-weight": "bold",
            },
          },
          {
            selector: "node[kind = 'document']",
            style: {
              shape: "barrel",
              width: 52,
              height: 40,
              "background-color": "#1C2321",
              "border-color": "#0F6E6B",
              "border-width": 3,
              color: "#0F6E6B",
              "font-weight": "bold",
            },
          },
          // Selected node spotlight
          {
            selector: "node:selected, .selected-node",
            style: {
              "border-width": 4,
              "border-color": "#B86B3D",
              width: 34,
              height: 34,
            },
          },
          // Level-of-Detail: Hide labels at low zoom level
          {
            selector: ".low-zoom",
            style: {
              label: "",
            },
          },
          // Edge base styling
          {
            selector: "edge",
            style: {
              width: 1.5,
              "line-color": "#CBD5E1",
              "curve-style": "bezier",
              "target-arrow-shape": "none",
              "transition-property": "opacity, line-color, width",
              "transition-duration": 200,
            },
          },
          // PREREQUISITE_OF edge: amber with directional arrow
          {
            selector: "edge[kind = 'PREREQUISITE_OF']",
            style: {
              width: 2.5,
              "line-color": "#B86B3D",
              "target-arrow-shape": "triangle",
              "target-arrow-color": "#B86B3D",
              "arrow-scale": 1.2,
            },
          },
          // USES edge: dotted teal
          {
            selector: "edge[kind = 'USES']",
            style: {
              width: 2,
              "line-color": "#0F766E",
              "line-style": "dotted",
              "target-arrow-shape": "vee",
              "target-arrow-color": "#0F766E",
            },
          },
          // PART_OF edge: muted solid
          {
            selector: "edge[kind = 'PART_OF']",
            style: {
              width: 1.5,
              "line-color": "#94A3B8",
              "line-style": "dashed",
            },
          },
          // Dimmed non-lineage items
          {
            selector: ".dimmed",
            style: {
              opacity: 0.15,
            },
          },
          // Lineage pulse highlight
          {
            selector: ".lineage-highlight",
            style: {
              "border-color": "#B86B3D",
              "border-width": 4,
              opacity: 1,
            },
          },
        ],
        layout: {
          name: "cose",
          idealEdgeLength: () => 90,
          nodeOverlap: 20,
          refresh: 20,
          fit: true,
          padding: 30,
          randomize: false,
          componentSpacing: 100,
          nodeRepulsion: () => 400000,
          edgeElasticity: () => 100,
        },
      });

      cyRef.current = cy;

      // Tap event listener
      cy.on("tap", "node", (evt: EventObject) => {
        const id = evt.target.id();
        onSelectNode(id);
      });

      cy.on("tap", (evt: EventObject) => {
        if (evt.target === cy) {
          onSelectNode(null);
        }
      });

      // Zoom listener for Level-of-Detail (LOD)
      cy.on("zoom", () => {
        const z = cy.zoom();
        setZoomLevel(z);
        if (z < 0.65) {
          cy.nodes().addClass("low-zoom");
        } else {
          cy.nodes().removeClass("low-zoom");
        }
      });

      return () => {
        cy.destroy();
      };
    } catch {
      // Fallback for jsdom / test environments
    }
  }, [nodes, edges, onSelectNode]);

  // Handle selected node and lineage highlights
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.elements().removeClass("selected-node dimmed lineage-highlight");

    if (selectedNodeId) {
      const selectedNode = cy.getElementById(selectedNodeId);
      if (selectedNode.length) {
        selectedNode.addClass("selected-node");
        cy.center(selectedNode);
      }
    }

    if (highlightedLineageIds.length > 0) {
      cy.elements().addClass("dimmed");
      highlightedLineageIds.forEach((id) => {
        const el = cy.getElementById(id);
        el.removeClass("dimmed").addClass("lineage-highlight");
      });
      // Also highlight connecting edges
      cy.edges().forEach((edge) => {
        if (
          highlightedLineageIds.includes(edge.source().id()) &&
          highlightedLineageIds.includes(edge.target().id())
        ) {
          edge.removeClass("dimmed").addClass("lineage-highlight");
        }
      });
    }
  }, [selectedNodeId, highlightedLineageIds]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 30);
  const handleReset = () => {
    cyRef.current?.layout({ name: "cose", animate: true, fit: true }).run();
  };

  return (
    <div className="relative h-full w-full overflow-hidden rounded-sheet border border-line bg-surface shadow-inner">
      {/* Cytoscape Canvas Container */}
      <div ref={containerRef} className="h-full w-full min-h-[500px]" data-testid="cytoscape-canvas" />

      {/* Floating Canvas Controls */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1.5 rounded-control border border-line bg-surface/90 p-1.5 shadow-md backdrop-blur-sm">
        <Button variant="ghost" className="h-7 w-7 p-0" onClick={handleZoomIn} aria-label="Zoom In">
          <Plus className="h-4 w-4" />
        </Button>
        <Button variant="ghost" className="h-7 w-7 p-0" onClick={handleZoomOut} aria-label="Zoom Out">
          <Minus className="h-4 w-4" />
        </Button>
        <div className="h-4 w-[1px] bg-line" />
        <Button variant="ghost" className="h-7 w-7 p-0" onClick={handleFit} aria-label="Fit to Viewport">
          <Maximize2 className="h-3.5 w-3.5" />
        </Button>
        <Button variant="ghost" className="h-7 w-7 p-0" onClick={handleReset} aria-label="Reset Layout">
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Canvas Status & Zoom Indicator */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 rounded-control border border-line bg-surface/90 px-2.5 py-1 text-[10px] font-mono text-muted backdrop-blur-sm">
        <span>LOD Zoom: {Math.round(zoomLevel * 100)}%</span>
        <span>•</span>
        <span>{nodes.length} Nodes</span>
        <span>•</span>
        <span>{edges.length} Edges</span>
      </div>

      {/* Visual Relationship Legend */}
      <div className="absolute bottom-4 right-4 z-10 hidden sm:flex items-center gap-3 rounded-control border border-line bg-surface/90 px-3 py-1.5 text-[10px] text-muted backdrop-blur-sm">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-copper" /> Prerequisite
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-proficient" /> Uses
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-line" /> Part Of
        </span>
      </div>
    </div>
  );
}
