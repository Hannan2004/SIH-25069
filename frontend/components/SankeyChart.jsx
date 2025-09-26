"use client";
import { sankey, sankeyLinkHorizontal } from "d3-sankey";
import { useMemo } from "react";

export default function SankeyChart({ width = 420, height = 260 }) {
  const data = useMemo(
    () => ({
      nodes: [
        { name: "Mining" },
        { name: "Refining" },
        { name: "Smelting" },
        { name: "Casting" },
        { name: "Product" },
      ],
      links: [
        { source: 0, target: 1, value: 10 },
        { source: 1, target: 2, value: 8 },
        { source: 2, target: 3, value: 7 },
        { source: 3, target: 4, value: 7 },
      ],
    }),
    []
  );

  const { nodes, links } = useMemo(() => {
    const sankeyGen = sankey()
      .nodeWidth(18)
      .nodePadding(24)
      .extent([
        [0, 0],
        [width, height],
      ]);
    return sankeyGen({ ...data });
  }, [data, width, height]);

  const colorMap = ["#2E7D5B", "#6C7A89", "#B87333", "#C6CDD5", "#0F3D2E"];

  return (
    <svg width={width} height={height} className="mx-auto block">
      <g>
        {links.map((l, i) => (
          <path
            key={i}
            d={sankeyLinkHorizontal()(l)}
            stroke="#B87333"
            fill="none"
            strokeOpacity={0.35}
            strokeWidth={Math.max(1, l.width)}
          />
        ))}
        {nodes.map((n, i) => (
          <g key={i}>
            <rect
              x={n.x0}
              y={n.y0}
              width={n.x1 - n.x0}
              height={n.y1 - n.y0}
              fill={colorMap[i % colorMap.length]}
              rx={4}
            />
            <text
              x={n.x1 + 6}
              y={(n.y0 + n.y1) / 2}
              alignmentBaseline="middle"
              fontSize={12}
              className="fill-gray-700"
            >
              {n.name}
            </text>
          </g>
        ))}
      </g>
    </svg>
  );
}
