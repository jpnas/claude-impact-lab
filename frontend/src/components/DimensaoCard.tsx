interface Props {
  titulo: string;
  children: React.ReactNode;
}

export function DimensaoCard({ titulo, children }: Props) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
        {titulo}
      </h3>
      {children}
    </div>
  );
}
