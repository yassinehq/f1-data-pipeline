"""Transform : nettoie les données brutes FastF1 et construit 4 tables propres."""
from __future__ import annotations

import pandas as pd

# Codes TrackStatus FastF1 : 4 = Safety Car, 5 = drapeau rouge, 6/7 = VSC.
NEUTRALISED_CODES = ("4", "5", "6", "7")


class DataQualityError(Exception):
    """Levée quand les données ne passent pas les contrôles qualité."""


def build_race(event: pd.Series, season: int) -> pd.DataFrame:
    return pd.DataFrame([{
        "season": season,
        "round": int(event["RoundNumber"]),
        "event_name": event["EventName"],
        "country": event["Country"],
        "location": event["Location"],
        "race_date": pd.to_datetime(event["EventDate"]).date(),
    }])


def clean_results(results: pd.DataFrame, season: int, rnd: int) -> pd.DataFrame:
    df = pd.DataFrame({
        "season": season,
        "round": rnd,
        "driver": results["Abbreviation"],
        "driver_number": results["DriverNumber"].astype(str),
        "full_name": results["FullName"],
        "team": results["TeamName"],
        "team_color": "#" + results["TeamColor"].fillna("888888").astype(str),
        "grid_position": pd.to_numeric(results["GridPosition"], errors="coerce").astype("Int64"),
        "position": pd.to_numeric(results["Position"], errors="coerce").astype("Int64"),
        "status": results["Status"],
        "points": pd.to_numeric(results["Points"], errors="coerce").fillna(0.0),
    })
    return df.reset_index(drop=True)


def clean_laps(laps: pd.DataFrame, season: int, rnd: int) -> pd.DataFrame:
    track_status = laps["TrackStatus"].fillna("").astype(str)
    deleted = laps["Deleted"].fillna(False).astype(bool) if "Deleted" in laps else False

    df = pd.DataFrame({
        "season": season,
        "round": rnd,
        "driver": laps["Driver"],
        "lap_number": laps["LapNumber"].astype("Int64"),
        "lap_time_s": laps["LapTime"].dt.total_seconds(),
        "stint": laps["Stint"].astype("Int64"),
        "compound": laps["Compound"].fillna("UNKNOWN").str.upper(),
        "tyre_life": laps["TyreLife"].astype("Int64"),
        "position": pd.to_numeric(laps["Position"], errors="coerce").astype("Int64"),
        "is_pit_in": laps["PitInTime"].notna(),
        "is_pit_out": laps["PitOutTime"].notna(),
        "is_neutralised": track_status.apply(lambda s: any(c in s for c in NEUTRALISED_CODES)),
    })
    # Un tour « propre » reflète le vrai rythme : pas de stand, pas de SC/VSC,
    # pas de départ, pas de tour annulé.
    df["is_clean"] = (
        df["lap_time_s"].notna()
        & ~df["is_pit_in"] & ~df["is_pit_out"] & ~df["is_neutralised"]
        & (df["lap_number"] > 1)
        & ~pd.Series(deleted, index=df.index)
    )
    df = df.dropna(subset=["lap_number"]).drop_duplicates(["driver", "lap_number"])
    return df.reset_index(drop=True)


def build_stints(laps: pd.DataFrame) -> pd.DataFrame:
    """Un relais = une suite de tours sur le même train de pneus."""
    laps = laps.dropna(subset=["stint"])
    keys = ["season", "round", "driver", "stint"]
    stints = laps.groupby(keys, as_index=False).agg(
        compound=("compound", "first"),
        start_lap=("lap_number", "min"),
        end_lap=("lap_number", "max"),
        n_laps=("lap_number", "count"),
    )
    clean_pace = (
        laps[laps["is_clean"]].groupby(keys)["lap_time_s"].median()
        .rename("median_clean_lap_s").reset_index()
    )
    return stints.merge(clean_pace, on=keys, how="left")


def validate(results: pd.DataFrame, laps: pd.DataFrame) -> None:
    """Contrôles qualité : on refuse de charger des données incohérentes."""
    errors = []
    if (laps["lap_time_s"].dropna() <= 0).any():
        errors.append("temps au tour négatif ou nul")
    if laps.duplicated(["driver", "lap_number"]).any():
        errors.append("tours en double")
    if (results["position"] == 1).sum() > 1:
        errors.append("plusieurs vainqueurs")
    if results["driver"].duplicated().any():
        errors.append("pilote en double dans les résultats")
    unknown = set(laps["driver"]) - set(results["driver"])
    if unknown:
        errors.append(f"tours de pilotes absents des résultats : {sorted(unknown)}")
    if errors:
        raise DataQualityError(" ; ".join(errors))
