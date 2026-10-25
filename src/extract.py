"""Extract : récupère le calendrier et les données de course via FastF1."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import fastf1
import pandas as pd

log = logging.getLogger(__name__)

# Les données officielles sont publiées quelques heures après l'arrivée.
PUBLICATION_DELAY = pd.Timedelta(hours=4)


def enable_cache(path: str | Path = "cache") -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(path))
    # FastF1 est très bavard : on garde seulement ses avertissements.
    logging.getLogger("fastf1").setLevel(logging.WARNING)


def completed_races(season: int, now: datetime | None = None) -> pd.DataFrame:
    """Liste des GP de la saison dont la course est terminée."""
    now = now or datetime.now(timezone.utc)
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    race_start = pd.to_datetime(schedule["Session5DateUtc"], utc=True)
    done = schedule[race_start + PUBLICATION_DELAY < now]
    races = done[["RoundNumber", "EventName", "Country", "Location", "EventDate"]].copy()
    races["season"] = season
    return races.reset_index(drop=True)


def fetch_race(season: int, round_number: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge résultats + tours d'une course (sans la télémétrie, trop lourde)."""
    session = fastf1.get_session(season, round_number, "R")
    session.load(laps=True, telemetry=False, weather=False, messages=False)
    if session.results is None or session.results.empty or session.laps.empty:
        raise ValueError(f"Données indisponibles pour {season} manche {round_number}")
    return session.results.copy(), session.laps.copy()
