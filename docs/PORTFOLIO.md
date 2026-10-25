# Intégrer le projet à ton portfolio (GitHub Pages)

## 1. Mettre le projet en ligne

1. Crée un repo public `f1-data-pipeline` sur GitHub et pousse ce dossier.
2. Lance une première fois en local `python -m src.pipeline`, puis commit `data/f1.duckdb`.
3. Onglet **Actions** du repo → « Pipeline F1 » → **Run workflow** pour vérifier que l'automatisation marche.
4. Sur [share.streamlit.io](https://share.streamlit.io) : connecte GitHub → New app → repo `f1-data-pipeline`, fichier `app/streamlit_app.py` → Deploy. Le dashboard se met à jour tout seul à chaque commit du lundi.
5. Remplace `LIEN-STREAMLIT` dans le README par ton vrai lien.
6. Enregistre un GIF de 10-15 s du dashboard (ScreenToGif sur Windows), mets-le dans `docs/apercu.gif`.

## 2. La carte projet pour ton site

Copie ce bloc à côté de tes autres projets et adapte les classes CSS à ton site :

```html
<article class="project-card">
  <img src="https://raw.githubusercontent.com/TON-PSEUDO/f1-data-pipeline/main/docs/apercu.gif"
       alt="Dashboard F1 : classement, rythme et stratégies pneus">
  <h3>🏁 F1 Data Pipeline</h3>
  <p>Pipeline automatisé qui collecte et structure les données de chaque Grand Prix de F1,
     puis les expose dans un dashboard en ligne.</p>
  <ul>
    <li>Chargement incrémental et idempotent dans DuckDB</li>
    <li>Mise à jour automatique chaque lundi (GitHub Actions)</li>
    <li>Contrôles qualité testés avec pytest</li>
  </ul>
  <p class="stack">Python · SQL · DuckDB · Streamlit · GitHub Actions</p>
  <a href="https://LIEN-STREAMLIT.streamlit.app">Démo live</a>
  <a href="https://github.com/TON-PSEUDO/f1-data-pipeline">Code</a>
</article>
```

Si ton portfolio est en Markdown (README / Jekyll) :

```markdown
### 🏁 F1 Data Pipeline
Pipeline automatisé qui collecte et structure les données de chaque Grand Prix de F1, puis les expose dans un dashboard en ligne.
- Chargement incrémental et idempotent dans DuckDB
- Mise à jour automatique chaque lundi (GitHub Actions)
- Contrôles qualité testés avec pytest

`Python` `SQL` `DuckDB` `Streamlit` `GitHub Actions` — [Démo live](https://LIEN-STREAMLIT.streamlit.app) · [Code](https://github.com/TON-PSEUDO/f1-data-pipeline)
```

Ajoute un chiffre concret une fois la saison chargée, par ex. « 24 GP · 25 000 tours analysés ».
