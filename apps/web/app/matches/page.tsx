import { api, Match } from "@/lib/api";
import Link from "next/link";

export const revalidate = 60;

const LEAGUES = ["", "EPL", "La_liga", "Bundesliga", "Serie_A", "Ligue_1"];

interface SearchParams { league?: string; status?: string; page?: string }

export default async function MatchesPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const sp = await searchParams;
  const league = sp.league || "";
  const status = sp.status || "";
  const page = Number(sp.page || 1);

  let matches: Match[] = [];
  try {
    const params: Record<string, string | number | boolean> = { page, page_size: 30 };
    if (league) params.league = league;
    if (status) params.status = status;
    const res = await api.matches(params);
    matches = res.data;
  } catch {}

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-6">
        <Link href="/" className="text-xl font-bold text-green-400">⚽ Probalyze</Link>
        <span className="text-white text-sm">Matches</span>
        <Link href="/valuebets" className="text-gray-400 hover:text-white text-sm">Value Bets</Link>
        <Link href="/predictions" className="text-gray-400 hover:text-white text-sm">Predictions</Link>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold mb-6">Matches</h1>

        {/* Filters (server-side via URL params) */}
        <form method="GET" className="bg-gray-900 rounded-xl p-4 flex flex-wrap gap-4 mb-6">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Ligue</label>
            <select name="league" defaultValue={league}
              className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700">
              {LEAGUES.map((l) => <option key={l} value={l}>{l || "Toutes"}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Statut</label>
            <select name="status" defaultValue={status}
              className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700">
              <option value="">Tous</option>
              <option value="scheduled">À venir</option>
              <option value="finished">Terminés</option>
            </select>
          </div>
          <div className="flex items-end">
            <button type="submit" className="bg-green-600 hover:bg-green-500 text-white text-sm px-4 py-2 rounded">
              Filtrer
            </button>
          </div>
        </form>

        {matches.length === 0 ? (
          <p className="text-gray-500">Aucun match trouvé.</p>
        ) : (
          <div className="space-y-2">
            {matches.map((m) => <MatchRow key={m.id} match={m} />)}
          </div>
        )}

        <div className="flex gap-3 mt-6">
          {page > 1 && (
            <Link href={`/matches?league=${league}&status=${status}&page=${page - 1}`}
              className="px-4 py-2 bg-gray-800 rounded text-sm hover:bg-gray-700">
              ← Précédent
            </Link>
          )}
          <span className="px-4 py-2 text-sm text-gray-400">Page {page}</span>
          {matches.length >= 30 && (
            <Link href={`/matches?league=${league}&status=${status}&page=${page + 1}`}
              className="px-4 py-2 bg-gray-800 rounded text-sm hover:bg-gray-700">
              Suivant →
            </Link>
          )}
        </div>
      </div>
    </main>
  );
}

function MatchRow({ match }: { match: Match }) {
  const date = match.match_date ? new Date(match.match_date).toLocaleDateString("fr-FR", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  }) : "—";

  const statusColor = match.status === "finished"
    ? "bg-gray-700 text-gray-400"
    : "bg-green-900 text-green-400";

  return (
    <div className="bg-gray-900 rounded-lg px-5 py-4 flex items-center justify-between gap-4">
      <div className="flex-1">
        <div className="flex items-center gap-3 font-medium">
          <span>{match.home_team?.name}</span>
          {match.home_score !== null ? (
            <span className="text-yellow-400 font-bold">{match.home_score} — {match.away_score}</span>
          ) : (
            <span className="text-gray-500">vs</span>
          )}
          <span>{match.away_team?.name}</span>
        </div>
        <p className="text-sm text-gray-400 mt-1">{match.league} · {date}</p>
      </div>
      <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor}`}>
        {match.status}
      </span>
    </div>
  );
}
