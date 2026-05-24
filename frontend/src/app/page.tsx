import { fetchAreas, Area } from "@/lib/api";
import { AreaSelector } from "@/components/AreaSelector";

export const revalidate = 60;

export default async function Home() {
  let areas: Area[] = [];
  try {
    areas = await fetchAreas();
  } catch {
    areas = [];
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold text-gray-900">CompStat Rio</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Plataforma de Inteligência Criminal — Força Municipal
          </p>
        </div>
      </header>
      <div className="max-w-4xl mx-auto px-6 py-10">
        <h2 className="text-lg font-semibold text-gray-700 mb-6">Selecione a Área FM</h2>
        {areas.length === 0 ? (
          <p className="text-gray-400 text-sm">
            Backend indisponível ou nenhuma área cadastrada.
          </p>
        ) : (
          <AreaSelector areas={areas} />
        )}
      </div>
    </main>
  );
}
