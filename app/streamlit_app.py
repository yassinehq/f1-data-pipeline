"""Dashboard F1 : streamlit run app/streamlit_app.py"""
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "f1.duckdb"
COMPOUND_COLORS = {
    "SOFT": "#DA291C", "MEDIUM": "#FFD12E", "HARD": "#F0F0EC",
    "INTERMEDIATE": "#43B02A", "WET": "#0067AD", "UNKNOWN": "#9AA0A6",
}

st.set_page_config(page_title="F1 Data Pipeline", page_icon="🏁", layout="wide")


@st.cache_data(ttl=3600)
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(sql, list(params)).df()


def driver_styles(results: pd.DataFrame) -> dict[str, dict]:
    """Couleur = écurie ; le 2e pilote de l'écurie est en pointillés."""
    latest = results.sort_values("round").groupby("driver").last().reset_index()
    styles, seen = {}, set()
    for _, row in latest.sort_values("driver").iterrows():
        styles[row["driver"]] = {"color": row["team_color"],
                                 "dash": "dash" if row["team"] in seen else "solid"}
        seen.add(row["team"])
    return styles


if not DB_PATH.exists():
    st.info("Base vide : lance d'abord `python -m src.pipeline`.")
    st.stop()

seasons = query("SELECT DISTINCT season FROM races ORDER BY season DESC")["season"].tolist()
if not seasons:
    st.info("Aucune course en base pour l'instant.")
    st.stop()

st.title("🏁 F1 Data Pipeline")
st.caption("Données collectées automatiquement après chaque Grand Prix (FastF1 → DuckDB).")

season = st.selectbox("Saison", seasons)
races = query("SELECT * FROM races WHERE season = ? ORDER BY round", (season,))
results = query("SELECT * FROM results WHERE season = ?", (season,))
styles = driver_styles(results)

kpis = query("""
    SELECT count(*) AS laps, sum(is_clean::INT) AS clean,
           (SELECT count(*) FROM stints WHERE season = ?) AS stints
    FROM laps WHERE season = ?""", (season, season)).iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Grands Prix analysés", len(races))
c2.metric("Tours en base", f"{int(kpis['laps']):,}".replace(",", " "),
          help=f"dont {int(kpis['clean']):,} tours « propres »".replace(",", " "))
c3.metric("Relais de pneus", int(kpis["stints"]))

tab_champ, tab_pace, tab_strat, tab_duel = st.tabs(
    ["Classement", "Rythme de course", "Stratégies pneus", "Duel"])

# --- 1. Classement cumulé -------------------------------------------------
with tab_champ:
    pts = results.merge(races[["round", "event_name"]], on="round")
    pts = pts.sort_values("round")
    pts["cumul"] = pts.groupby("driver")["points"].cumsum()
    top = pts.groupby("driver")["cumul"].max().nlargest(10).index
    fig = go.Figure()
    for drv in top:
        d = pts[pts["driver"] == drv]
        fig.add_trace(go.Scatter(
            x=d["event_name"], y=d["cumul"], name=drv, mode="lines+markers",
            line=dict(color=styles[drv]["color"], dash=styles[drv]["dash"], width=2),
            marker=dict(size=8),
            hovertemplate=f"<b>{drv}</b><br>%{{x}}<br>%{{y:.0f}} pts<extra></extra>"))
    fig.update_layout(title="Points cumulés – top 10", yaxis_title="Points",
                      hovermode="x unified", height=480)
    st.plotly_chart(fig, width="stretch")
    standings = (pts.groupby(["driver", "team"])["points"].sum()
                 .sort_values(ascending=False).reset_index())
    standings.index += 1
    st.dataframe(standings, width="stretch")

# Sélection d'un GP pour les onglets suivants
gp_labels = dict(zip(races["event_name"], races["round"]))

# --- 2. Rythme de course --------------------------------------------------
with tab_pace:
    gp = st.selectbox("Grand Prix", list(gp_labels)[::-1], key="pace_gp")
    rnd = gp_labels[gp]
    laps = query("""SELECT l.driver, l.lap_time_s, r.position FROM laps l
                    JOIN results r USING (season, round, driver)
                    WHERE l.season = ? AND l.round = ? AND l.is_clean""", (season, rnd))
    if laps.empty:
        st.info("Pas de tours propres pour ce GP.")
    else:
        order = laps.groupby("driver")["lap_time_s"].median().sort_values().index.tolist()
        fig = px.box(laps, x="driver", y="lap_time_s", color="driver",
                     category_orders={"driver": order},
                     color_discrete_map={d: s["color"] for d, s in styles.items()},
                     labels={"driver": "", "lap_time_s": "Temps au tour (s)"})
        fig.update_layout(title=f"{gp} – distribution des tours propres "
                                "(hors stands, SC/VSC et 1er tour)",
                          showlegend=False, height=480)
        st.plotly_chart(fig, width="stretch")
        st.caption("Plus la boîte est basse et serrée, plus le pilote était rapide et régulier.")

# --- 3. Stratégies pneus --------------------------------------------------
with tab_strat:
    gp = st.selectbox("Grand Prix", list(gp_labels)[::-1], key="strat_gp")
    rnd = gp_labels[gp]
    stints = query("""SELECT s.*, r.position FROM stints s
                      JOIN results r USING (season, round, driver)
                      WHERE s.season = ? AND s.round = ?""", (season, rnd))
    order = (stints.drop_duplicates("driver")
             .sort_values("position", na_position="last")["driver"].tolist())
    fig = go.Figure()
    for compound, color in COMPOUND_COLORS.items():
        d = stints[stints["compound"] == compound]
        if d.empty:
            continue
        fig.add_trace(go.Bar(
            y=d["driver"], x=d["n_laps"], base=d["start_lap"] - 1, orientation="h",
            name=compound.capitalize(), marker=dict(color=color, line=dict(color="#555", width=1)),
            customdata=d[["stint", "start_lap", "end_lap"]],
            hovertemplate="<b>%{y}</b> – relais %{customdata[0]}<br>"
                          "Tours %{customdata[1]}→%{customdata[2]}<extra>" + compound + "</extra>"))
    fig.update_layout(title=f"{gp} – stratégies (ordre d'arrivée)", barmode="overlay",
                      xaxis_title="Tour", height=max(420, 26 * len(order)),
                      yaxis=dict(categoryorder="array", categoryarray=order[::-1]),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                      margin=dict(t=90))
    st.plotly_chart(fig, width="stretch")

# --- 4. Duel --------------------------------------------------------------
with tab_duel:
    gp = st.selectbox("Grand Prix", list(gp_labels)[::-1], key="duel_gp")
    rnd = gp_labels[gp]
    drivers = (results[results["round"] == rnd].sort_values("position")["driver"].tolist())
    col_a, col_b = st.columns(2)
    a = col_a.selectbox("Pilote A", drivers, index=0)
    b = col_b.selectbox("Pilote B", drivers, index=min(1, len(drivers) - 1))
    duel = query("""SELECT driver, lap_number, lap_time_s FROM laps
                    WHERE season = ? AND round = ? AND is_clean AND driver IN (?, ?)""",
                 (season, rnd, a, b))
    if a == b or duel.empty:
        st.info("Choisis deux pilotes différents.")
    else:
        fig = go.Figure()
        for drv, dash in ((a, "solid"), (b, "dash")):
            d = duel[duel["driver"] == drv]
            color = styles[drv]["color"]
            fig.add_trace(go.Scatter(x=d["lap_number"], y=d["lap_time_s"], name=drv,
                                     mode="lines+markers", marker=dict(size=8),
                                     line=dict(color=color, dash=dash, width=2)))
        fig.update_layout(title=f"{gp} – {a} vs {b}, tours propres",
                          xaxis_title="Tour", yaxis_title="Temps (s)",
                          hovermode="x unified", height=440)
        st.plotly_chart(fig, width="stretch")
        med = duel.groupby("driver")["lap_time_s"].median()
        gap = med[b] - med[a]
        faster = a if gap > 0 else b
        st.metric("Écart médian sur tour propre", f"{abs(gap):.3f} s",
                  help=f"{faster} était plus rapide en rythme de course")
        st.caption(f"➜ **{faster}** plus rapide de {abs(gap):.3f} s au tour en médiane.")
