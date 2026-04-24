const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, params?: Record<string, string | number | boolean>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.toString(), { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export interface Match {
  id: string;
  match_date: string;
  league: string;
  status: string;
  home_team: { name: string; slug: string };
  away_team: { name: string; slug: string };
  home_score: number | null;
  away_score: number | null;
}

export interface ValueBet {
  id: string;
  market: string;
  outcome: string;
  odds_value: number;
  probability: number;
  value: number;
  kelly_fraction: number;
  bookmaker: string;
  created_at: string;
  match: Match;
}

export interface Prediction {
  id: string;
  match_id: string;
  prob_home_win: number;
  prob_draw: number;
  prob_away_win: number;
  prob_over_25: number;
  prob_btts: number;
  lambda_home: number;
  lambda_away: number;
  model_version: string;
  computed_at: string;
  match: Match;
}

export const api = {
  matches: (params?: Record<string, string | number | boolean>) =>
    apiFetch<{ data: Match[]; page: number; page_size: number }>("/matches", params),

  valueBets: (params?: Record<string, string | number | boolean>) =>
    apiFetch<{ data: ValueBet[] }>("/valuebets", params),

  valueBetsSummary: () =>
    apiFetch<{ total: number; avg_value: number; avg_odds: number; by_market: Record<string, { count: number; avg_value: number }> }>("/valuebets/summary"),

  predictions: (params?: Record<string, string | number | boolean>) =>
    apiFetch<{ data: Prediction[] }>("/predictions", params),
};
