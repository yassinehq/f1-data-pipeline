# 🏁 F1 Data Pipeline

Pipeline de données automatisé qui collecte, nettoie et stocke les données de chaque Grand Prix de Formule 1, puis les expose dans un dashboard en ligne.

**[▶ Démo live](https://LIEN-STREAMLIT.streamlit.app)** · Mise à jour automatique chaque lundi

![Aperçu du dashboard](docs/apercu.gif)

## Ce que fait le projet

1. **Collecte** : chaque lundi, GitHub Actions récupère les données des GP terminés via [FastF1](https://github.com/theOehrly/Fast-F1) (résultats, chaque tour de chaque pilote, pneus, arrêts).
2. **Nettoyage** : conversion des temps, détection des tours faussés (stands, Safety Car, VSC, 1er tour), reconstruction des relais de pneus, contrôles qualité.
3. **Stockage** : base DuckDB, chargement **incrémental et idempotent** (seuls les nouveaux GP sont chargés ; relancer le pipeline ne crée jamais de doublon).
4. **Visualisation** : dashboard Streamlit avec 4 vues — classement cumulé, rythme de course, stratégies pneus, duel entre deux pilotes.

## Architecture

```
FastF1 (API) ──► extract.py ──► transform.py ──► load.py ──► DuckDB ──► Streamlit
                                  │ contrôles qualité         ▲
                                  ▼                           │
                          rejet si incohérent     GitHub Actions (chaque lundi)
```

| Table | Contenu | Clé |
|---|---|---|
| `races` | un GP par ligne | saison, manche |
| `results` | résultat de chaque pilote | saison, manche, pilote |
| `laps` | chaque tour, avec indicateur « tour propre » | saison, manche, pilote, tour |
| `stints` | chaque relais : pneu, tours, rythme médian | saison, manche, pilote, relais |

## Choix techniques

- **DuckDB** plutôt que PostgreSQL : base analytique dans un seul fichier, aucun serveur, requêtes SQL rapides sur des millions de lignes.
- **Tour « propre »** : exclut tours d'entrée/sortie des stands, Safety Car / VSC / drapeau rouge, 1er tour et tours annulés. C'est la base de toute analyse de rythme.
- **Transaction par course** : une course est remplacée en entier ou pas du tout, jamais à moitié.
- **Tests** : pytest vérifie le nettoyage, les relais, les contrôles qualité et l'idempotence, sans connexion internet. Ils tournent avant chaque mise à jour.

## Lancer en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux : source .venv/bin/activate)
pip install -r requirements.txt

python -m src.pipeline                  # saison en cours
python -m src.pipeline --season 2025    # une autre saison
pytest                                   # tests
streamlit run app/streamlit_app.py       # dashboard
```

## Limites

- Les données dépendent de la disponibilité de l'API F1 Live Timing (via FastF1).
- Le rythme n'est pas corrigé de l'effet carburant ni du trafic : c'est la prochaine étape (modèle de dégradation des pneus).
- Courses uniquement (pas les qualifications ni les sprints).

## Stack

Python · pandas · FastF1 · DuckDB · SQL · Streamlit · Plotly · pytest · GitHub Actions
