# ⚽ Probalyze

> Plateforme de détection de **value bets** football par modèle de Poisson.

**URL de production :** https://probalyze.picsnature.fr

---

## Architecture

```
/apps
  /api        → FastAPI backend (Python)
  /worker     → Ingestion + calcul de prédictions
  /web        → Dashboard Next.js
/services
  /scrapers   → Understat, FBref
  /models     → Poisson, Value Bet Calculator
  /odds       → the-odds-api.com
/packages
  /db         → Client Supabase
  /utils      → Config, Logger, Cache
/infra
  /supabase
    /migrations → Schema SQL
docker-compose.yml
```

## Stack

| Composant | Tech |
|-----------|------|
| Backend   | Python 3.12, FastAPI |
| Frontend  | Next.js 15, Tailwind CSS |
| Database  | Supabase (PostgreSQL) |
| Queue     | Redis 7 |
| Scraping  | aiohttp, tenacity |
| Modèle    | Poisson (scipy) |
| DevOps    | Docker, Docker Compose |

---

## Démarrage rapide

### 1. Prérequis

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose

### 2. Variables d'environnement

```bash
cp .env.example .env
```

Renseigner dans `.env` :
- `SUPABASE_SERVICE_KEY` — clé service Supabase (Settings > API)
- `ODDS_API_KEY` — clé API [the-odds-api.com](https://the-odds-api.com) (gratuit : 500 req/mois)

### 3. Migrations Supabase

```bash
supabase login
supabase link --project-ref taefyqfdtulikkivkwnr
supabase db push
```

Ou directement via l'éditeur SQL Supabase :  
→ coller le contenu de `infra/supabase/migrations/001_initial_schema.sql`

### 4. Lancer avec Docker

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| API     | http://localhost:8000 |
| Docs    | http://localhost:8000/docs |
| Web     | http://localhost:3000 |

### 5. Lancer en local (dev)

**Backend :**
```bash
pip install -r apps/api/requirements.txt
uvicorn apps.api.main:app --reload --port 8000
```

**Worker :**
```bash
python -m apps.worker.main
```

**Frontend :**
```bash
cd apps/web
npm install
npm run dev
```

---

## API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Health check |
| GET | `/matches` | Liste des matchs |
| GET | `/matches/{id}` | Détail match |
| GET | `/teams` | Liste des équipes |
| GET | `/odds` | Cotes bookmakers |
| GET | `/predictions` | Prédictions Poisson |
| GET | `/valuebets` | Value bets actives |
| GET | `/valuebets/summary` | Résumé statistique |

**Filtres `GET /valuebets` :**
- `min_value` — edge minimum (ex: `0.05` = 5%)
- `market` — `home_win`, `draw`, `away_win`, `over_25`
- `sort_by` — `value`, `odds_value`, `probability`, `created_at`
- `page`, `page_size`

---

## Modèle de Poisson

```
λ_home = (xG_home / league_avg) × (xGA_away / league_avg) × league_avg × 1.08
λ_away = (xG_away / league_avg) × (xGA_home / league_avg) × league_avg

P(score h-a) = Poisson(h; λ_home) × Poisson(a; λ_away)

P(Home Win) = Σ P(h>a)
P(Draw)     = Σ P(h=a)
P(Away Win) = Σ P(h<a)

Value = (cote × probabilité) - 1   → value > 0 = value bet
Kelly = (b×p - q) / b               → taille de mise optimale
```

---

## Sources de données

| Source | Données | Gratuit |
|--------|---------|---------|
| [Understat](https://understat.com) | xG, xGA, scores | ✅ |
| [FBref](https://fbref.com) | Tirs, possession | ✅ |
| [the-odds-api.com](https://the-odds-api.com) | Cotes bookmakers | ✅ (500 req/mois) |

---

## Déploiement (picsnature.fr)

```nginx
# Nginx reverse proxy pour probalyze.picsnature.fr
server {
    server_name probalyze.picsnature.fr;

    location /api/ {
        proxy_pass http://localhost:8000/;
    }

    location / {
        proxy_pass http://localhost:3000/;
    }
}
```

---

## Roadmap

- [ ] Backtesting historique + calcul ROI
- [ ] Modèle Dixon-Coles (correction des scores faibles)
- [ ] Alertes Telegram/email sur nouvelles value bets
- [ ] Dashboard analytique ROI cumulé
