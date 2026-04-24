"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ValueBet } from "@/lib/api";

const MARKETS = ["", "home_win", "draw", "away_win", "over_25"];
const SORT_OPTIONS = [
  { value: "value", label: "Edge ↓" },
  { value: "odds_value", label: "Cote ↓" },
  { value: "probability", label: "Probabilité ↓" },
  { value: "created_at", label: "Récent ↓" },
];

export default function ValueBetsPage() {
  const [bets, setBets] = useState<ValueBet[]>([]);
  const [loading, setLoading] = useState(true);
  const [market, setMarket] = useState("");
  const [sortBy, setSortBy] = useState("value");
  const [minValue, setMinValue] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setLoading(true);
    api
      .valueBets({ market: market || undefined, sort_by: sortBy, min_value: minValue, page, page_size: 25 })
      .then((r) => setBets(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [market, sortBy, minValue, page]);

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-6">
        <Link href="/" className="text-xl font-bold text-green-400">⚽ Probalyze</Link>
        <Link href="/matches" className="text-gray-400 hover:text-white text-sm">Matches</Link>
        <span className="text-white text-sm">Value Bets</span>
        <Link href="/predictions" className="text-gray-400 hover:text-white text-sm">Predictions</Link>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold mb-6">Value Bets</h1>

        {/* Filters */}
        <div className="bg-gray-900 rounded-xl p-4 flex flex-wrap gap-4 mb-6">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Marché</label>
            <select
              value={market}
              onChange={(e) => { setMarket(e.target.value); setPage(1); }}
              className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700"
            >
              {MARKETS.map((m) => (
                <option key={m} value={m}>{m || "Tous"}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Trier par</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Edge min (%)</label>
            <input
              type="number"
              value={minValue * 100}
              onChange={(e) => { setMinValue(Number(e.target.value) / 100); setPage(1); }}
              className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700 w-24"
              step="1"
              min="0"
            />
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <p className="text-gray-500 animate-pulse">Chargement...</p>
        ) : bets.length === 0 ? (
          <p className="text-gray-500">Aucune value bet trouvée.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-800">
                  <th className="pb-3 pr-4">Match</th>
                  <th className="pb-3 pr-4">Ligue</th>
                  <th className="pb-3 pr-4">Marché</th>
                  <th className="pb-3 pr-4">Bookmaker</th>
                  <th className="pb-3 pr-4 text-right">Cote</th>
                  <th className="pb-3 pr-4 text-right">Prob</th>
                  <th className="pb-3 text-right">Edge</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {bets.map((vb) => (
                  <tr key={vb.id} className="hover:bg-gray-900/50 transition-colors">
                    <td className="py-3 pr-4 font-medium">
                      {vb.match ? `${vb.match.home_team?.name} — ${vb.match.away_team?.name}` : "—"}
                    </td>
                    <td className="py-3 pr-4 text-gray-400">{vb.match?.league || "—"}</td>
                    <td className="py-3 pr-4">
                      <span className="bg-gray-800 text-gray-300 text-xs px-2 py-1 rounded">{vb.outcome}</span>
                    </td>
                    <td className="py-3 pr-4 text-gray-400">{vb.bookmaker}</td>
                    <td className="py-3 pr-4 text-right font-bold text-yellow-400">
                      @{vb.odds_value?.toFixed(2)}
                    </td>
                    <td className="py-3 pr-4 text-right text-gray-300">
                      {(vb.probability * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 text-right">
                      <span className={`font-bold ${vb.value > 0.1 ? "text-green-400" : "text-green-600"}`}>
                        +{(vb.value * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 bg-gray-800 rounded text-sm disabled:opacity-40 hover:bg-gray-700"
          >
            ← Précédent
          </button>
          <span className="px-4 py-2 text-sm text-gray-400">Page {page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={bets.length < 25}
            className="px-4 py-2 bg-gray-800 rounded text-sm disabled:opacity-40 hover:bg-gray-700"
          >
            Suivant →
          </button>
        </div>
      </div>
    </main>
  );
}
