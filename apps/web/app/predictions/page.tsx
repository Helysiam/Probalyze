import { api, Prediction } from "@/lib/api";
import Link from "next/link";

export const revalidate = 60;

export default async function PredictionsPage() {
  let predictions: Prediction[] = [];
  try {
    const res = await api.predictions({ page_size: 30 });
    predictions = res.data;
  } catch {}

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-6">
        <Link href="/" className="text-xl font-bold text-green-400">⚽ Probalyze</Link>
        <Link href="/matches" className="text-gray-400 hover:text-white text-sm">Matches</Link>
        <Link href="/valuebets" className="text-gray-400 hover:text-white text-sm">Value Bets</Link>
        <span className="text-white text-sm">Predictions</span>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold mb-6">Prédictions</h1>

        {predictions.length === 0 ? (
          <p className="text-gray-500">Aucune prédiction disponible.</p>
        ) : (
          <div className="space-y-3">
            {predictions.map((p) => <PredictionCard key={p.id} pred={p} />)}
          </div>
        )}
      </div>
    </main>
  );
}

function PredictionCard({ pred }: { pred: Prediction }) {
  const matchName = pred.match
    ? `${pred.match.home_team?.name} vs ${pred.match.away_team?.name}`
    : "Match inconnu";

  const probs = [
    { label: pred.match?.home_team?.name || "Domicile", value: pred.prob_home_win, color: "blue" },
    { label: "Nul", value: pred.prob_draw, color: "gray" },
    { label: pred.match?.away_team?.name || "Extérieur", value: pred.prob_away_win, color: "red" },
  ];

  return (
    <div className="bg-gray-900 rounded-xl p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="font-semibold text-lg">{matchName}</p>
          <p className="text-sm text-gray-400">{pred.match?.league} · {pred.model_version}</p>
        </div>
        <div className="text-right text-sm text-gray-400">
          <p>λ⌂ {pred.lambda_home?.toFixed(2)}</p>
          <p>λ✈ {pred.lambda_away?.toFixed(2)}</p>
        </div>
      </div>

      {/* Probability bars */}
      <div className="space-y-2">
        {probs.map((p) => (
          <div key={p.label} className="flex items-center gap-3">
            <span className="w-28 text-sm text-gray-400 truncate">{p.label}</span>
            <div className="flex-1 bg-gray-800 rounded-full h-3">
              <div
                className={`h-3 rounded-full ${p.color === "blue" ? "bg-blue-500" : p.color === "red" ? "bg-red-500" : "bg-gray-500"}`}
                style={{ width: `${(p.value || 0) * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium w-12 text-right">
              {((p.value || 0) * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      <div className="mt-3 flex gap-4 text-xs text-gray-500">
        <span>Over 2.5: {((pred.prob_over_25 || 0) * 100).toFixed(1)}%</span>
        <span>BTTS: {((pred.prob_btts || 0) * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
