'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { RelatedPaperResult } from '@/types';
import {
  GRAPH_LAYOUT,
  GRAPH_NODE,
  GRAPH_COLORS,
  GRAPH_LINKS,
  GRAPH_SHADOW,
} from '@/lib/constants';

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
});

interface Node {
  id: string;
  name: string;
  year: number | null;
  citations: number;
  isCenter: boolean;
  url?: string;
  authors?: string[];
  index?: number; // Paper index number (for display)
  x?: number;
  y?: number;
  fx?: number; // Fixed x position
  fy?: number; // Fixed y position
}

interface Link {
  source: string;
  target: string;
  distance?: number;
  strength?: number; // 0-1, higher = stronger connection
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

interface ConnectedPapersGraphProps {
  sourceTitle: string;
  sourceYear?: number;
  sourceCitations?: number;
  connectedPapers: RelatedPaperResult[];
}

export default function ConnectedPapersGraph({
  sourceTitle,
  sourceYear,
  sourceCitations = 0,
  connectedPapers,
}: ConnectedPapersGraphProps) {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: GRAPH_LAYOUT.DEFAULT_WIDTH,
    height: GRAPH_LAYOUT.DEFAULT_HEIGHT,
  });

  // Update dimensions on mount and resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const width = rect.width || GRAPH_LAYOUT.DEFAULT_WIDTH;
        const height = GRAPH_LAYOUT.DEFAULT_HEIGHT;
        if (width > 0) {
          setDimensions({ width, height });
        }
      }
    };

    // Initial update
    updateDimensions();

    // Retry with delays
    const [delay1, delay2] = GRAPH_LAYOUT.DIMENSION_RETRY_DELAYS;
    const timer1 = setTimeout(updateDimensions, delay1);
    const timer2 = setTimeout(updateDimensions, delay2);

    window.addEventListener('resize', updateDimensions);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      window.removeEventListener('resize', updateDimensions);
    };
  }, [connectedPapers]);

  // Build graph data with circular layout - stable and reliable
  useEffect(() => {
    // react-force-graph-2d uses (0,0) as canvas center
    const baseRadius = Math.min(dimensions.width, dimensions.height) * GRAPH_LAYOUT.RADIUS_RATIO;

    const nodes: Node[] = [
      {
        id: 'center',
        name: sourceTitle,
        year: sourceYear || null,
        citations: sourceCitations,
        isCenter: true,
        x: 0,
        y: 0,
        fx: 0,
        fy: 0,
      },
    ];

    const links: Link[] = [];

    connectedPapers.forEach((paper, index) => {
      const nodeId = `paper-${index}`;

      // Perfect circular arrangement - all at same distance from center (0,0)
      const angle = (index / connectedPapers.length) * 2 * Math.PI - Math.PI / 2;
      const x = baseRadius * Math.cos(angle);
      const y = baseRadius * Math.sin(angle);

      nodes.push({
        id: nodeId,
        name: paper.title,
        year: paper.year || null,
        citations: paper.cited_by,
        isCenter: false,
        url: paper.url || undefined,
        authors: paper.authors,
        index: index + 1,
        x: x,
        y: y,
        fx: x,
        fy: y,
      });

      // Link strength based on recommendation rank (higher rank = stronger)
      const rankStrength = 1 - (index / connectedPapers.length); // 1.0 for #1, 0.1 for #10

      links.push({
        source: 'center',
        target: nodeId,
        strength: rankStrength,
      });
    });

    // Add cross-links between papers based on similarity
    const { MAX_CITATION_DIFF, MAX_YEAR_DIFF, CITATION_NORM_DIVISOR, YEAR_NORM_DIVISOR } =
      GRAPH_LINKS.SIMILARITY;

    for (let i = 0; i < connectedPapers.length; i++) {
      // Connect to next 2-3 papers for web-like structure
      for (let j = i + 1; j <= Math.min(i + 3, connectedPapers.length - 1); j++) {
        const citationDiff = Math.abs(connectedPapers[i].cited_by - connectedPapers[j].cited_by);
        const yearDiff = Math.abs((connectedPapers[i].year || 0) - (connectedPapers[j].year || 0));

        // Papers similar in citations and year are likely related
        if (citationDiff < MAX_CITATION_DIFF || yearDiff <= MAX_YEAR_DIFF) {
          // Calculate link strength: more similar = stronger
          const citationSimilarity = 1 - Math.min(citationDiff / CITATION_NORM_DIVISOR, 1);
          const yearSimilarity = 1 - Math.min(yearDiff / YEAR_NORM_DIVISOR, 1);
          const strength = (citationSimilarity + yearSimilarity) / 2;

          links.push({
            source: `paper-${i}`,
            target: `paper-${j}`,
            strength: strength,
          });
        }
      }
    }

    setGraphData({ nodes, links });
  }, [sourceTitle, sourceYear, sourceCitations, connectedPapers, dimensions]);

  // Color based on year with EXTREME contrast - Teal to Purple gradient
  const getNodeColor = (year: number | null, isCenter: boolean) => {
    if (isCenter) return GRAPH_COLORS.CENTER;
    if (!year) return GRAPH_COLORS.UNKNOWN_YEAR;

    const { MIN_YEAR, HUE_START, HUE_END, SATURATION_START, SATURATION_END, LIGHTNESS_START, LIGHTNESS_END } =
      GRAPH_COLORS.YEAR_GRADIENT;
    const currentYear = new Date().getFullYear();
    const maxYear = currentYear;

    // Normalize year to 0-1 range
    const normalized = Math.max(0, Math.min(1, (year - MIN_YEAR) / (maxYear - MIN_YEAR)));

    // EXTREME contrast: Light Cyan/Teal → Deep Purple/Violet
    const hue = HUE_START + (normalized * (HUE_END - HUE_START));
    const saturation = SATURATION_START + (normalized * (SATURATION_END - SATURATION_START));
    const lightness = LIGHTNESS_START - (normalized * (LIGHTNESS_START - LIGHTNESS_END));

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  };

  // Size based on citations - significant variation
  const getNodeSize = (citations: number, isCenter: boolean) => {
    if (isCenter) return GRAPH_NODE.CENTER_SIZE;

    // Clear variation based on citations
    const { MIN_SIZE, MAX_SIZE, MAX_CITATIONS_FOR_SCALE } = GRAPH_NODE;
    const logCitations = Math.log(citations + 1);
    const maxLogCitations = Math.log(MAX_CITATIONS_FOR_SCALE);

    return MIN_SIZE + (logCitations / maxLogCitations) * (MAX_SIZE - MIN_SIZE);
  };

  return (
    <div ref={containerRef} className="w-full h-full bg-white dark:bg-gray-900 overflow-hidden">
      {connectedPapers.length === 0 ? (
        <div className="flex items-center justify-center h-full p-8 text-gray-500">
          No graph data available
        </div>
      ) : graphData.nodes.length === 0 ? (
        <div className="flex items-center justify-center h-full p-8 text-gray-500">
          Loading graph...
        </div>
      ) : (
        <ForceGraph2D
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="rgba(255,255,255,0)"
          nodeColor={(node) => {
          const n = node as Node;
          return getNodeColor(n.year, n.isCenter);
        }}
        nodeVal={(node) => {
          const n = node as Node;
          return getNodeSize(n.citations, n.isCenter);
        }}
        linkColor={(link) => {
          const l = link as Link;
          const strength = l.strength || 0.5;
          const sourceId = typeof l.source === 'string' ? l.source : (l.source as Node).id;
          const targetId = typeof l.target === 'string' ? l.target : (l.target as Node).id;
          const isCrossLink = sourceId !== 'center' && targetId !== 'center';

          if (isCrossLink) {
            const { OPACITY_MIN, OPACITY_MAX, COLOR_BASE } = GRAPH_LINKS.CROSS;
            const opacity = OPACITY_MIN + (strength * (OPACITY_MAX - OPACITY_MIN));
            return COLOR_BASE.replace('rgb', 'rgba').replace(')', `, ${opacity})`);
          } else {
            const { OPACITY_MIN, OPACITY_MAX, COLOR_BASE } = GRAPH_LINKS.CENTER;
            const opacity = OPACITY_MIN + (strength * (OPACITY_MAX - OPACITY_MIN));
            return COLOR_BASE.replace('rgb', 'rgba').replace(')', `, ${opacity})`);
          }
        }}
        linkWidth={(link) => {
          const l = link as Link;
          const strength = l.strength || 0.5;
          const sourceId = typeof l.source === 'string' ? l.source : (l.source as Node).id;
          const targetId = typeof l.target === 'string' ? l.target : (l.target as Node).id;
          const isCrossLink = sourceId !== 'center' && targetId !== 'center';

          if (isCrossLink) {
            const { WIDTH_MIN, WIDTH_MAX } = GRAPH_LINKS.CROSS;
            return WIDTH_MIN + (strength * (WIDTH_MAX - WIDTH_MIN));
          } else {
            const { WIDTH_MIN, WIDTH_MAX } = GRAPH_LINKS.CENTER;
            return WIDTH_MIN + (strength * (WIDTH_MAX - WIDTH_MIN));
          }
        }}
        linkDirectionalParticles={0}
        d3AlphaDecay={1} // Stop simulation immediately for fixed positions
        d3VelocityDecay={1}
        cooldownTicks={0}
        nodeCanvasObject={(node, ctx: CanvasRenderingContext2D) => {
          const n = node as Node;
          const size = getNodeSize(n.citations, n.isCenter);
          const color = getNodeColor(n.year, n.isCenter);

          // Draw shadow
          ctx.shadowColor = GRAPH_SHADOW.COLOR;
          ctx.shadowBlur = GRAPH_SHADOW.BLUR;
          ctx.shadowOffsetX = GRAPH_SHADOW.OFFSET_X;
          ctx.shadowOffsetY = GRAPH_SHADOW.OFFSET_Y;

          // Draw outer glow for center node
          if (n.isCenter) {
            ctx.beginPath();
            ctx.arc(node.x!, node.y!, size + GRAPH_NODE.CENTER_GLOW_OFFSET, 0, 2 * Math.PI);
            ctx.fillStyle = GRAPH_COLORS.CENTER_GLOW;
            ctx.fill();
          }

          // Draw main circle
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, size, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();

          // Reset shadow for border
          ctx.shadowColor = 'transparent';
          ctx.shadowBlur = 0;
          ctx.shadowOffsetX = 0;
          ctx.shadowOffsetY = 0;

          // Add border
          if (n.isCenter) {
            ctx.strokeStyle = GRAPH_COLORS.CENTER_BORDER;
            ctx.lineWidth = 2.5;
            ctx.stroke();
          } else {
            ctx.strokeStyle = GRAPH_COLORS.NODE_BORDER;
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }

          // Draw index number outside node (for non-center nodes)
          if (!n.isCenter && n.index !== undefined) {
            const fontSize = 10;
            // Calculate angle from center (0,0) to position label radially
            const angle = Math.atan2(node.y!, node.x!);
            const labelDistance = size + 16;
            const labelX = node.x! + Math.cos(angle) * labelDistance;
            const labelY = node.y! + Math.sin(angle) * labelDistance;

            ctx.font = `600 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            // Draw text
            ctx.fillStyle = '#1f2937'; // Dark gray
            ctx.fillText(`#${n.index}`, labelX, labelY);
          }
        }}
        onNodeClick={(node) => {
          const n = node as Node;
          if (n.url && !n.isCenter) {
            window.open(n.url, '_blank');
          }
        }}
        nodeLabel={(node) => {
          const n = node as Node;
          return `${n.name}${n.year ? ` (${n.year})` : ''}${n.citations > 0 ? ` - ${n.citations.toLocaleString()} citations` : ''}`;
        }}
        enableNodeDrag={false}
        enableZoomInteraction={false}
        enablePanInteraction={false}
      />
      )}

      {/* Legend */}
      <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-700">
        <div className="flex flex-wrap gap-4 text-xs text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500 ring-2 ring-yellow-400"></div>
            <span className="font-medium">Origin Paper</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ background: 'hsl(270, 95%, 15%)' }}></div>
            <span>Newer</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ background: 'hsl(180, 45%, 85%)' }}></div>
            <span>Older</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-1 items-end">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-sm"></div>
              <div className="w-2 h-2 rounded-full bg-blue-500 shadow-sm"></div>
              <div className="w-3 h-3 rounded-full bg-blue-500 shadow-sm"></div>
            </div>
            <span>Size ∝ Citations</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5 items-center">
              <div className="w-4 h-px bg-gray-400" style={{ height: '1px' }}></div>
              <div className="w-4 h-0.5 bg-gray-500"></div>
              <div className="w-4 h-1 bg-gray-600"></div>
            </div>
            <span>굵을수록 연결 강함</span>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-gray-500 dark:text-gray-400">Click nodes to open paper</span>
          </div>
        </div>
      </div>
    </div>
  );
}
