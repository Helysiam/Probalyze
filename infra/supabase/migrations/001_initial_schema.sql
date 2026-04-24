-- Probalyze — Initial Schema
-- Migration 001

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────
-- TEAMS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    league      TEXT,
    country     TEXT,
    understat_id TEXT,
    fbref_id    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_teams_slug ON teams(slug);
CREATE INDEX idx_teams_league ON teams(league);

-- ─────────────────────────────────────────
-- MATCHES
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS matches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_team_id    UUID REFERENCES teams(id),
    away_team_id    UUID REFERENCES teams(id),
    league          TEXT NOT NULL,
    season          TEXT,
    match_date      TIMESTAMPTZ,
    status          TEXT DEFAULT 'scheduled', -- scheduled | live | finished
    home_score      INT,
    away_score      INT,
    understat_id    TEXT UNIQUE,
    fbref_id        TEXT,
    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_league ON matches(league);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);

-- ─────────────────────────────────────────
-- STATS (xG, tirs, possession, forme)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stats (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id        UUID REFERENCES matches(id) ON DELETE CASCADE,
    team_id         UUID REFERENCES teams(id),
    is_home         BOOLEAN,
    xg              DECIMAL(6,3),
    xga             DECIMAL(6,3),
    shots           INT,
    shots_on_target INT,
    possession      DECIMAL(5,2),
    deep_completions INT,
    ppda            DECIMAL(8,4),
    source          TEXT, -- understat | fbref
    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stats_match ON stats(match_id);
CREATE INDEX idx_stats_team ON stats(team_id);

-- ─────────────────────────────────────────
-- ODDS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS odds (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id        UUID REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker       TEXT NOT NULL,
    market          TEXT NOT NULL, -- 1X2 | btts | over_under
    home_win        DECIMAL(8,3),
    draw            DECIMAL(8,3),
    away_win        DECIMAL(8,3),
    over_25         DECIMAL(8,3),
    under_25        DECIMAL(8,3),
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),
    raw_data        JSONB
);

CREATE INDEX idx_odds_match ON odds(match_id);
CREATE INDEX idx_odds_bookmaker ON odds(bookmaker);

-- ─────────────────────────────────────────
-- PREDICTIONS (Poisson model output)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id        UUID REFERENCES matches(id) ON DELETE CASCADE,
    model_version   TEXT NOT NULL,
    lambda_home     DECIMAL(6,3),   -- expected goals home
    lambda_away     DECIMAL(6,3),   -- expected goals away
    prob_home_win   DECIMAL(6,4),
    prob_draw       DECIMAL(6,4),
    prob_away_win   DECIMAL(6,4),
    prob_over_25    DECIMAL(6,4),
    prob_btts       DECIMAL(6,4),
    score_matrix    JSONB,          -- matrix of score probabilities
    computed_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_match ON predictions(match_id);

-- ─────────────────────────────────────────
-- VALUE BETS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS value_bets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id        UUID REFERENCES matches(id) ON DELETE CASCADE,
    prediction_id   UUID REFERENCES predictions(id),
    odds_id         UUID REFERENCES odds(id),
    bookmaker       TEXT,
    market          TEXT,       -- home_win | draw | away_win | over_25 | btts
    outcome         TEXT,
    odds_value      DECIMAL(8,3),
    probability     DECIMAL(6,4),
    value           DECIMAL(8,4),   -- (odds * prob) - 1
    kelly_fraction  DECIMAL(6,4),   -- Kelly criterion
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_valuebets_value ON value_bets(value DESC);
CREATE INDEX idx_valuebets_match ON value_bets(match_id);
CREATE INDEX idx_valuebets_active ON value_bets(is_active);

-- ─────────────────────────────────────────
-- INGESTION LOG (audit trail)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source      TEXT NOT NULL,
    status      TEXT NOT NULL, -- success | error | partial
    records_in  INT DEFAULT 0,
    records_out INT DEFAULT 0,
    error_msg   TEXT,
    metadata    JSONB,
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

-- ─────────────────────────────────────────
-- Updated_at trigger
-- ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
