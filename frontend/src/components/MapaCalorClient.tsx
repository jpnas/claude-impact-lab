"use client";

import dynamic from "next/dynamic";
import type { ComponentProps } from "react";
import type MapaCalor from "./MapaCalor";

const MapaCalorInner = dynamic(() => import("./MapaCalor"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex flex-col items-center justify-center gap-3" style={{ background: "#0a0e15" }}>
      <div
        className="w-6 h-6 rounded-full border-2 animate-spin"
        style={{ borderColor: "var(--border-strong)", borderTopColor: "var(--accent)" }}
      />
      <span className="label">Carregando malha geoespacial…</span>
    </div>
  ),
});

export default function MapaCalorClient(props: ComponentProps<typeof MapaCalor>) {
  return <MapaCalorInner {...props} />;
}
