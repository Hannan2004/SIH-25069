"use client";
import { sankey, sankeyLinkHorizontal } from "d3-sankey";
import { useMemo, useEffect, useState } from "react";

export default function EmissionsSankeyChart({ 
  emissionsBreakdown,
  width = 380, 
  height = 200,
  animated = true 
}) {
  const [animationProgress, setAnimationProgress] = useState(0);

  // Create data structure from emissions breakdown
  const data = useMemo(() => {
    const production = emissionsBreakdown?.production_kg_co2e || 0;
    const transport = emissionsBreakdown?.transport_kg_co2e || 0;
    const energy = emissionsBreakdown?.energy_kg_co2e || 0;
    const endOfLife = emissionsBreakdown?.end_of_life_kg_co2e || 0;
    
    // If no real data, show placeholder
    if (production === 0 && transport === 0 && energy === 0 && endOfLife === 0) {
      return {
        nodes: [
          { name: "Sources" },
          { name: "Production" },
          { name: "Transport" },
          { name: "Energy" },
          { name: "End-of-Life" },
          { name: "Total Emissions" }
        ],
        links: [
          { source: 0, target: 1, value: 12.11 },
          { source: 0, target: 2, value: 31.00 },
          { source: 0, target: 3, value: 5.72 },
          { source: 0, target: 4, value: 0.00 },
          { source: 1, target: 5, value: 12.11 },
          { source: 2, target: 5, value: 31.00 },
          { source: 3, target: 5, value: 5.72 }
        ]
      };
    }

    return {
      nodes: [
        { name: "Sources" },
        { name: "Production" },
        { name: "Transport" },
        { name: "Energy" },
        { name: "End-of-Life" },
        { name: "Total Emissions" }
      ],
      links: [
        { source: 0, target: 1, value: production },
        { source: 0, target: 2, value: transport },
        { source: 0, target: 3, value: energy },
        { source: 0, target: 4, value: endOfLife },
        { source: 1, target: 5, value: production },
        { source: 2, target: 5, value: transport },
        { source: 3, target: 5, value: energy },
        { source: 4, target: 5, value: endOfLife }
      ].filter(link => link.value > 0) // Only show links with actual values
    };
  }, [emissionsBreakdown]);

  const { nodes, links } = useMemo(() => {
    const sankeyGen = sankey()
      .nodeWidth(12)
      .nodePadding(16)
      .extent([
        [10, 10],
        [width - 10, height - 20],
      ]);
    return sankeyGen({ ...data });
  }, [data, width, height]);

  // Animation effect
  useEffect(() => {
    if (!animated) {
      setAnimationProgress(1);
      return;
    }

    const duration = 2000; // 2 seconds
    const interval = 16; // ~60fps
    const steps = duration / interval;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const progress = Math.min(currentStep / steps, 1);
      
      // Ease-out animation curve
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setAnimationProgress(easeOut);

      if (progress >= 1) {
        clearInterval(timer);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [animated, data]);

  // Color mapping for different emission sources
  const nodeColors = {
    "Sources": "#374151",
    "Production": "#EF4444", 
    "Transport": "#F59E0B",
    "Energy": "#3B82F6",
    "End-of-Life": "#10B981",
    "Total Emissions": "#6B7280"
  };

  const linkColors = {
    "Production": "#EF4444",
    "Transport": "#F59E0B", 
    "Energy": "#3B82F6",
    "End-of-Life": "#10B981"
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
      <svg 
        width={width} 
        height={height} 
        className="block"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          {/* Gradient definitions for animated flow effect */}
          <linearGradient id="flowGradient" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="rgba(59, 130, 246, 0.8)" />
            <stop offset="50%" stopColor="rgba(59, 130, 246, 0.4)" />
            <stop offset="100%" stopColor="rgba(59, 130, 246, 0.1)" />
          </linearGradient>
        </defs>
        
        <g>
          {/* Links (flows) */}
          {links.map((link, i) => {
            const targetNodeName = nodes[link.target.index]?.name;
            const sourceNodeName = nodes[link.source.index]?.name;
            
            // Determine link color based on target
            let linkColor = "#94A3B8";
            if (sourceNodeName === "Sources") {
              linkColor = linkColors[targetNodeName] || "#94A3B8";
            } else {
              linkColor = linkColors[sourceNodeName] || "#94A3B8";
            }

            const animatedWidth = Math.max(1, link.width * animationProgress);
            
            return (
              <g key={i}>
                <path
                  d={sankeyLinkHorizontal()(link)}
                  stroke={linkColor}
                  fill="none"
                  strokeOpacity={0.6}
                  strokeWidth={animatedWidth}
                  style={{
                    transition: animated ? 'stroke-width 0.3s ease' : 'none'
                  }}
                />
                {/* Animated flow particles for visual effect */}
                {animated && animationProgress > 0.5 && (
                  <circle
                    r="2"
                    fill={linkColor}
                    opacity="0.8"
                  >
                    <animateMotion
                      dur="3s"
                      repeatCount="indefinite"
                      path={sankeyLinkHorizontal()(link)}
                    />
                  </circle>
                )}
              </g>
            );
          })}
          
          {/* Nodes */}
          {nodes.map((node, i) => {
            const nodeHeight = (node.y1 - node.y0) * animationProgress;
            const nodeY = node.y1 - nodeHeight;
            
            return (
              <g key={i}>
                <rect
                  x={node.x0}
                  y={nodeY}
                  width={node.x1 - node.x0}
                  height={nodeHeight}
                  fill={nodeColors[node.name] || "#6B7280"}
                  rx={2}
                  style={{
                    transition: animated ? 'height 0.5s ease, y 0.5s ease' : 'none'
                  }}
                />
                {/* Node labels */}
                <text
                  x={node.x0 < width / 2 ? node.x1 + 6 : node.x0 - 6}
                  y={(node.y0 + node.y1) / 2}
                  alignmentBaseline="middle"
                  textAnchor={node.x0 < width / 2 ? "start" : "end"}
                  fontSize={10}
                  className="fill-gray-700 font-medium"
                  style={{
                    opacity: animationProgress,
                    transition: animated ? 'opacity 0.5s ease' : 'none'
                  }}
                >
                  {node.name}
                </text>
                {/* Value labels for end nodes */}
                {(node.name === "Total Emissions" || 
                  (node.name !== "Sources" && node.name !== "Total Emissions")) && 
                 node.value && (
                  <text
                    x={node.x0 < width / 2 ? node.x1 + 6 : node.x0 - 6}
                    y={(node.y0 + node.y1) / 2 + 12}
                    alignmentBaseline="middle"
                    textAnchor={node.x0 < width / 2 ? "start" : "end"}
                    fontSize={8}
                    className="fill-gray-500"
                    style={{
                      opacity: animationProgress * 0.8,
                      transition: animated ? 'opacity 0.5s ease' : 'none'
                    }}
                  >
                    {node.value.toFixed(1)} kg
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
      
      {/* Loading indicator */}
      {animated && animationProgress < 1 && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded">
          <div className="text-xs text-gray-500">Loading flow...</div>
        </div>
      )}
    </div>
  );
}