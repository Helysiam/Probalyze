import { api, ValueBet } from "@/lib/api";
import Link from "next/link";

export const revalidate = 60;

export default async function Home() {
  let summary = { total: 0, avg_value: 0, avg_odds: 0, by_market: {} as Record<string, { count: number; avg_value: number }> };
  let topBets: ValueBet[] = [];

  try {
    [{ data: topBets }, summary] = await Promise.all([
      api.valueBets({ page_size: 5, sort_by: "value" }),
      api.valueBetsSummary(),
    ]);
  } catch {}

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-6">
        <span className="text-xl font-bold text-green-400">⚽ Probalyze</span>
        <Link href="/matches" className="text-gray-400 hover:text-white text-sm">Matches</Link>
        <Link href="/valuebets" className="text-gray-400 hover:text-white text-sm">Value Bets</Link>
        <Link href="/predictions" className="text-gray-400 hover:text-white text-sm">Predictions</Link>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-400 mb-8">Détection de value bets football par modèle de Poisson</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <StatCard label="Value Bets actives" value={summary.total} color="green" />
          <StatCard label="Edge moyen" value={`+${(summary.avg_value * 100).toFixed(1)}%`} color="blue" />
          <StatCard label="Cote moyenne" value={summary.avg_odds?.toFixed(2) || "—"} color="purple" />
        </div>

        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Top Value Bets</h2>
            <Link href="/valuebets" className="text-green-400 text-sm hover:underline">Voir tout →</Link>
          </div>

          {topBets.length === 0 ? (
            <p className="text-gray-500 text-sm">Aucune value bet pour le moment.</p>
          ) : (
            <div className="space-y-3">
              {topBets.map((vb) => <ValueBetRow key={vb.id} vb={vb} />)}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  const colors: Record<string, string> = {
    green: "border-green-500 text-green-400",
    blue: "border-blue-500 text-blue-400",
    purple: "border-purple-500 text-purple-400",
  };
  return (
    <div className={`bg-gray-900 border-l-4 ${colors[color]} rounded-lg p-5`}>
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className={`text-3xl font-bold ${colors[color].split(" ")[1]}`}>{value}</p>
    </div>
  );
}

function ValueBetRow({ vb }: { vb: ValueBet }) {
  const edge = (vb.value * 100).toFixed(1);
  const matchName = vb.match
    ? `${vb.match.home_team?.name} vs ${vb.match.away_team?.name}`
    : "Match inconnu";
  return (
    <div className="bg-gray-900 rounded-lg p-4 flex items-center justify-between gap-4">
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{matchName}</p>
        <p className="text-sm text-gray-400">{vb.outcome} · {vb.bookmaker}</p>
      </div>
      <div className="text-right">
        <p className="text-lg font-bold text-yellow-400">@{vb.odds_value?.toFixed(2)}</p>
        <p className="text-xs text-gray-400">{(vb.probability * 100).toFixed(1)}% prob</p>
      </div>
      <div className="text-right min-w-[60px]">
        <span className="inline-block bg-green-900 text-green-300 text-sm font-bold px-3 py-1 rounded-full">
          +{edge}%
        </span>
      </div>
    </div>
  );
}
