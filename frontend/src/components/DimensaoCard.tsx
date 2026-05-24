interface Props {
  titulo: string;
  indice?: string;
  acento?: "accent" | "data";
  className?: string;
  children: React.ReactNode;
}

export function DimensaoCard({ titulo, indice, acento = "accent", className = "", children }: Props) {
  const cor = acento === "data" ? "var(--data)" : "var(--accent)";
  return (
    <section className={`panel p-4 rise ${className}`}>
      <header className="flex items-center justify-between mb-3 pb-2.5 border-b" style={{ borderColor: "var(--border)" }}>
        <h3 className="label" style={{ color: "var(--text-dim)" }}>
          {titulo}
        </h3>
        {indice && (
          <span className="tnum text-[10px]" style={{ color: cor }}>
            {indice}
          </span>
        )}
      </header>
      {children}
    </section>
  );
}
