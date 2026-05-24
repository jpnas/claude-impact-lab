/* Horizontal labelled bars for distributions (por_tipo, ORCRIM, etc.). */
export function BarList({
  data,
  cor = "var(--accent)",
  format = (v) => String(v),
  max,
}: {
  data: [string, number][];
  cor?: string;
  format?: (v: number) => string;
  max?: number;
}) {
  const top = max ?? Math.max(1, ...data.map(([, v]) => v));
  return (
    <div className="space-y-2">
      {data.map(([label, v]) => (
        <div key={label}>
          <div className="flex justify-between items-baseline gap-2 mb-1">
            <span className="text-[11px] truncate" style={{ color: "var(--text-dim)" }}>
              {label}
            </span>
            <span className="tnum text-[11px] flex-shrink-0" style={{ color: "var(--text)" }}>
              {format(v)}
            </span>
          </div>
          <div className="bar-track h-1">
            <div
              className="h-full rounded-[1px]"
              style={{ width: `${(v / top) * 100}%`, background: cor, transition: "width .6s ease" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/* Vertical column sparkline — for hourly distribution (24h or partial). */
export function ColumnChart({
  data,
  cor = "var(--accent)",
  destaque,
}: {
  data: [string, number][];
  cor?: string;
  destaque?: string;
}) {
  const max = Math.max(1, ...data.map(([, v]) => v));
  return (
    <div className="flex items-end gap-[3px] h-16">
      {data.map(([label, v]) => {
        const ativo = label === destaque;
        return (
          <div key={label} className="flex-1 flex flex-col items-center gap-1 group" title={`${label}h · ${v}`}>
            <div className="w-full flex items-end h-12">
              <div
                className="w-full rounded-[1px]"
                style={{
                  height: `${Math.max(6, (v / max) * 100)}%`,
                  background: ativo ? cor : "rgba(150,170,200,0.18)",
                  boxShadow: ativo ? `0 0 8px ${cor}` : "none",
                  transition: "height .6s ease",
                }}
              />
            </div>
            <span
              className="tnum text-[8px]"
              style={{ color: ativo ? cor : "var(--text-faint)" }}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
