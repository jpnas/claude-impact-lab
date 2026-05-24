"use client";

import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, GeoJSON, useMap, Tooltip } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import "leaflet/dist/leaflet.css";
import type { GeoJsonObject } from "geojson";

export type HeatPoint = [number, number, number];
export interface Camera {
  id: string;
  lat: number;
  lon: number;
}

interface Props {
  pontos: HeatPoint[];
  cameras: Camera[];
  poligono?: GeoJsonObject | null;
  totalOcorrencias?: number;
}

/* Heat overlay — leaflet.heat is imperative, so we bridge it via the map instance. */
function HeatLayer({ pontos, visivel }: { pontos: HeatPoint[]; visivel: boolean }) {
  const map = useMap();
  useEffect(() => {
    if (!visivel || pontos.length === 0) return;
    const layer = L.heatLayer(pontos as L.HeatLatLngTuple[], {
      radius: 24,
      blur: 20,
      maxZoom: 17,
      minOpacity: 0.32,
      max: Math.max(1, ...pontos.map((p) => p[2])),
      gradient: {
        0.0: "rgba(70,214,198,0)",
        0.25: "#2a9d8f",
        0.45: "#46d6c6",
        0.6: "#f5c542",
        0.78: "#ff8a3d",
        1.0: "#ff2d2d",
      },
    }).addTo(map);
    return () => {
      map.removeLayer(layer);
    };
  }, [map, pontos, visivel]);
  return null;
}

/* Fit the viewport to the data on first render. */
function FitToData({ pontos }: { pontos: HeatPoint[] }) {
  const map = useMap();
  useEffect(() => {
    if (pontos.length === 0) return;
    const bounds = L.latLngBounds(pontos.map((p) => [p[0], p[1]] as [number, number]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }, [map, pontos]);
  return null;
}

function LayerToggle({
  ativo,
  cor,
  onClick,
  children,
}: {
  ativo: boolean;
  cor: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-2.5 py-1.5 rounded-[3px] border transition-colors label"
      style={{
        background: ativo ? "rgba(20,27,39,0.92)" : "rgba(10,14,21,0.7)",
        borderColor: ativo ? cor : "var(--border)",
        color: ativo ? "var(--text)" : "var(--text-faint)",
        letterSpacing: "0.12em",
      }}
    >
      <span
        className="w-2 h-2 rounded-full"
        style={{ background: ativo ? cor : "transparent", border: `1px solid ${cor}` }}
      />
      {children}
    </button>
  );
}

export default function MapaCalor({ pontos, cameras, poligono, totalOcorrencias }: Props) {
  const [verCalor, setVerCalor] = useState(true);
  const [verCameras, setVerCameras] = useState(false);

  const center = useMemo<[number, number]>(() => {
    if (pontos.length === 0) return [-22.9, -43.2];
    const lat = pontos.reduce((s, p) => s + p[0], 0) / pontos.length;
    const lng = pontos.reduce((s, p) => s + p[1], 0) / pontos.length;
    return [lat, lng];
  }, [pontos]);

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={center}
        zoom={15}
        zoomControl
        scrollWheelZoom
        className="w-full h-full"
        style={{ background: "#0a0e15" }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
          maxZoom={19}
        />

        {poligono && (
          <GeoJSON
            data={poligono}
            style={{
              color: "#46d6c6",
              weight: 1.5,
              opacity: 0.7,
              fillColor: "#46d6c6",
              fillOpacity: 0.04,
              dashArray: "4 4",
            }}
          />
        )}

        <HeatLayer pontos={pontos} visivel={verCalor} />

        {verCameras &&
          cameras.map((c) => (
            <CircleMarker
              key={c.id}
              center={[c.lat, c.lon]}
              radius={2.6}
              pathOptions={{
                color: "#46d6c6",
                weight: 1,
                fillColor: "#46d6c6",
                fillOpacity: 0.55,
                opacity: 0.7,
              }}
            >
              <Tooltip>Câmera {c.id.slice(0, 8)}</Tooltip>
            </CircleMarker>
          ))}

        <FitToData pontos={pontos} />
      </MapContainer>

      {/* Layer controls */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1.5 items-end">
        <LayerToggle ativo={verCalor} cor="var(--accent)" onClick={() => setVerCalor((v) => !v)}>
          Mapa de calor
        </LayerToggle>
        <LayerToggle ativo={verCameras} cor="var(--data)" onClick={() => setVerCameras((v) => !v)}>
          Câmeras · {cameras.length}
        </LayerToggle>
      </div>

      {/* Intensity legend */}
      {verCalor && (
        <div
          className="absolute bottom-5 left-3 z-[1000] px-3 py-2.5 rounded-[3px] border"
          style={{ background: "rgba(8,11,16,0.82)", borderColor: "var(--border)", backdropFilter: "blur(6px)" }}
        >
          <p className="label mb-1.5" style={{ color: "var(--text-dim)" }}>
            Densidade de ocorrências
          </p>
          <div
            className="h-1.5 w-44 rounded-full"
            style={{
              background:
                "linear-gradient(90deg, #2a9d8f, #46d6c6, #f5c542, #ff8a3d, #ff2d2d)",
            }}
          />
          <div className="flex justify-between mt-1 label" style={{ letterSpacing: "0.1em" }}>
            <span>Baixa</span>
            <span>Crítica</span>
          </div>
          {typeof totalOcorrencias === "number" && (
            <p className="label mt-1.5" style={{ color: "var(--text-faint)" }}>
              {pontos.length} pontos · {totalOcorrencias} registros
            </p>
          )}
        </div>
      )}
    </div>
  );
}
