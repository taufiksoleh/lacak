import cytoscape from "cytoscape";
import { useEffect, useRef } from "react";
import { PLATFORM_COLOR } from "../format";
import type { GraphData } from "../types";

const COMMUNITY = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6"];

export default function AffiliationGraph({ data, height = 520 }: { data: GraphData; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const maxW = Math.max(1, ...data.nodes.map((n) => n.weight));
    const cy = cytoscape({
      container: ref.current,
      elements: [
        ...data.nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.entity ? `${n.label}\n(${n.entity})` : n.label,
            color: n.is_subject ? PLATFORM_COLOR[n.platform] ?? "#334155" : n.entity ? "#dc2626" : COMMUNITY[n.community % COMMUNITY.length],
            size: n.is_subject ? 46 : 18 + (30 * n.weight) / maxW,
            shape: n.is_subject ? "star" : n.entity ? "diamond" : "ellipse",
          },
        })),
        ...data.edges.map((e, i) => ({
          data: {
            id: `e${i}`,
            source: e.source,
            target: e.target,
            width: 1 + Math.min(8, e.weight),
            dashed: e.kinds.same_person ? "dashed" : "solid",
            title: Object.entries(e.kinds).map(([k, v]) => `${k}: ${v}`).join(", "),
          },
        })),
      ],
      style: [
        {
          selector: "node",
          style: {
            "background-color": "data(color)",
            width: "data(size)",
            height: "data(size)",
            shape: "data(shape)" as never,
            label: "data(label)",
            "font-size": 10,
            "text-wrap": "wrap",
            "text-valign": "bottom",
            "text-margin-y": 4,
            color: "#334155",
          },
        },
        {
          selector: "edge",
          style: {
            width: "data(width)",
            "line-color": "#cbd5e1",
            "line-style": "data(dashed)" as never,
            "curve-style": "bezier",
            opacity: 0.8,
          },
        },
      ],
      layout: { name: "cose", animate: false, nodeRepulsion: () => 9000, idealEdgeLength: () => 90 },
      wheelSensitivity: 0.3,
    });
    return () => cy.destroy();
  }, [data]);

  return (
    <div>
      <div ref={ref} style={{ height }} className="w-full rounded-lg border border-slate-200 bg-white" />
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-600">
        <span>★ akun target</span>
        <span className="text-red-600">◆ entitas terdaftar (organisasi/pemerintah/perusahaan)</span>
        <span>● akun lain (warna = komunitas)</span>
        <span>ukuran = frekuensi interaksi · garis putus = akun target yang sama</span>
      </div>
    </div>
  );
}
