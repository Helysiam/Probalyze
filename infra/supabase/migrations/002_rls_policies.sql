-- Migration 002 — Row Level Security

-- Enable RLS on all tables
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE value_bets ENABLE ROW LEVEL SECURITY;

-- Public read-only access (anon + authenticated)
CREATE POLICY "Public read teams" ON teams FOR SELECT USING (true);
CREATE POLICY "Public read matches" ON matches FOR SELECT USING (true);
CREATE POLICY "Public read stats" ON stats FOR SELECT USING (true);
CREATE POLICY "Public read odds" ON odds FOR SELECT USING (true);
CREATE POLICY "Public read predictions" ON predictions FOR SELECT USING (true);
CREATE POLICY "Public read value_bets" ON value_bets FOR SELECT USING (true);

-- Service role has full access (backend writes via service key)
CREATE POLICY "Service insert teams" ON teams FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update teams" ON teams FOR UPDATE USING (true);

CREATE POLICY "Service insert matches" ON matches FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update matches" ON matches FOR UPDATE USING (true);

CREATE POLICY "Service insert stats" ON stats FOR INSERT WITH CHECK (true);
CREATE POLICY "Service insert odds" ON odds FOR INSERT WITH CHECK (true);
CREATE POLICY "Service insert predictions" ON predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "Service insert value_bets" ON value_bets FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update value_bets" ON value_bets FOR UPDATE USING (true);
