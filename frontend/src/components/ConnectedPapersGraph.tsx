'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { RelatedPaperResult } from '@/types';

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
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });

  // Update dimensions on mount and resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth;
        const height = Math.min(500, Math.max(400, width * 0.7));
        setDimensions({ width, height });
      }
    };

    // Initial update with a slight delay to allow layout to settle
    const timer = setTimeout(updateDimensions, 100);
    window.addEventListener('resize', updateDimensions);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updateDimensions);
    };
  }, [connectedPapers]);

  // Build graph data with circular layout - stable and reliable
  useEffect(() => {
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;
    const baseRadius = Math.min(dimensions.width, dimensions.height) * 0.32;

    const nodes: Node[] = [
      {
        id: 'center',
        name: sourceTitle,
        year: sourceYear || null,
        citations: sourceCitations,
        isCenter: true,
        x: centerX,
        y: centerY,
        fx: centerX,
        fy: centerY,
      },
    ];

    const links: Link[] = [];

    connectedPapers.forEach((paper, index) => {
      const nodeId = `paper-${index}`;

      // Perfect circular arrangement - all at same distance
      const angle = (index / connectedPapers.length) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + baseRadius * Math.cos(angle);
      const y = centerY + baseRadius * Math.sin(angle);

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
    for (let i = 0; i < connectedPapers.length; i++) {
      // Connect to next 2-3 papers for web-like structure
      for (let j = i + 1; j <= Math.min(i + 3, connectedPapers.length - 1); j++) {
        const citationDiff = Math.abs(connectedPapers[i].cited_by - connectedPapers[j].cited_by);
        const yearDiff = Math.abs((connectedPapers[i].year || 0) - (connectedPapers[j].year || 0));

        // Papers similar in citations and year are likely related
        if (citationDiff < 150 || yearDiff <= 2) {
          // Calculate link strength: more similar = stronger
          const citationSimilarity = 1 - Math.min(citationDiff / 150, 1);
          const yearSimilarity = 1 - Math.min(yearDiff / 5, 1);
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
    if (isCenter) return '#a855f7'; // Brighter purple for center node
    if (!year) return '#94a3b8'; // Gray for unknown year

    const currentYear = new Date().getFullYear();
    const minYear = 2019; // Tighter range for max contrast
    const maxYear = currentYear;

    // Normalize year to 0-1 range
    const normalized = Math.max(0, Math.min(1, (year - minYear) / (maxYear - minYear)));

    // EXTREME contrast: Light Cyan/Teal → Deep Purple/Violet
    // Old papers (2019-2020): Very light cyan (hue 180, light)
    // New papers (2025-2026): Deep purple/violet (hue 270, dark)
    const hue = 180 + (normalized * 90); // 180 (cyan) → 270 (purple)
    const saturation = 45 + (normalized * 50); // 45% → 95%
    const lightness = 85 - (normalized * 70); // 85% (very light) → 15% (very dark)

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  };

  // Size based on citations - significant variation
  const getNodeSize = (citations: number, isCenter: boolean) => {
    if (isCenter) return 14; // Larger center node

    // Clear variation based on citations
    const minSize = 6;
    const maxSize = 12;
    const logCitations = Math.log(citations + 1);
    const maxLogCitations = Math.log(5000); // Assume max ~5k citations

    return minSize + (logCitations / maxLogCitations) * (maxSize - minSize);
  };

  return (
    <div ref={containerRef} className="w-full bg-white dark:bg-gray-900 rounded-lg overflow-hidden relative">
      <ForceGraph2D
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        nodeColor={(node: any) => {
          const n = node as Node;
          return getNodeColor(n.year, n.isCenter);
        }}
        nodeVal={(node: any) => {
          const n = node as Node;
          return getNodeSize(n.citations, n.isCenter);
        }}
        linkColor={(link: any) => {
          const strength = link.strength || 0.5;
          const isCrossLink = link.source.id && link.target.id &&
                             link.source.id !== 'center' && link.target.id !== 'center';

          if (isCrossLink) {
            // Cross-links: opacity based on strength (0.2 to 0.7)
            const opacity = 0.2 + (strength * 0.5);
            return `rgba(120, 140, 170, ${opacity})`;
          } else {
            // Center links: opacity based on rank strength (0.3 to 0.8)
            const opacity = 0.3 + (strength * 0.5);
            return `rgba(160, 170, 190, ${opacity})`;
          }
        }}
        linkWidth={(link: any) => {
          const strength = link.strength || 0.5;
          const isCrossLink = link.source.id && link.target.id &&
                             link.source.id !== 'center' && link.target.id !== 'center';

          if (isCrossLink) {
            // Cross-links: width 0.8 to 2.0 based on strength
            return 0.8 + (strength * 1.2);
          } else {
            // Center links: width 1.0 to 2.5 based on rank
            return 1.0 + (strength * 1.5);
          }
        }}
        linkDirectionalParticles={0}
        d3AlphaDecay={1} // Stop simulation immediately for fixed positions
        d3VelocityDecay={1}
        cooldownTicks={0}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const n = node as Node;
          const size = getNodeSize(n.citations, n.isCenter);
          const color = getNodeColor(n.year, n.isCenter);

          // Draw shadow
          ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
          ctx.shadowBlur = 8;
          ctx.shadowOffsetX = 2;
          ctx.shadowOffsetY = 2;

          // Draw outer glow for center node
          if (n.isCenter) {
            ctx.beginPath();
            ctx.arc(node.x!, node.y!, size + 3, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(168, 85, 247, 0.3)';
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
            ctx.strokeStyle = '#fbbf24';
            ctx.lineWidth = 2.5;
            ctx.stroke();
          } else {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }

          // Draw index number outside node (for non-center nodes)
          if (!n.isCenter && n.index !== undefined) {
            const fontSize = 14;
            // Calculate angle from center to position label radially
            const centerX = dimensions.width / 2;
            const centerY = dimensions.height / 2;
            const angle = Math.atan2(node.y! - centerY, node.x! - centerX);
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
        onNodeClick={(node: any, event: MouseEvent) => {
          const n = node as Node;
          if (n.url && !n.isCenter) {
            window.open(n.url, '_blank');
          }
        }}
        nodeLabel={(node: any) => {
          const n = node as Node;
          return `${n.name}${n.year ? ` (${n.year})` : ''}${n.citations > 0 ? ` - ${n.citations.toLocaleString()} citations` : ''}`;
        }}
        enableNodeDrag={false}
        enableZoomInteraction={true}
        enablePanInteraction={true}
      />

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
