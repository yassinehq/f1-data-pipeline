"""Fausses données au format FastF1 : les tests tournent sans internet."""
import pandas as pd
import pytest


@pytest.fixture
def raw_results():
    return pd.DataFrame({
        "DriverNumber": ["1", "16"],
        "Abbreviation": ["VER", "LEC"],
        "FullName": ["Max Verstappen", "Charles Leclerc"],
        "TeamName": ["Red Bull Racing", "Ferrari"],
        "TeamColor": ["3671C6", "E8002D"],
        "GridPosition": [1.0, 2.0],
        "Position": [1.0, 2.0],
        "Status": ["Finished", "Finished"],
        "Points": [25.0, 18.0],
    })


@pytest.fixture
def raw_laps():
    rows = []
    for drv in ("VER", "LEC"):
        for lap in range(1, 7):
            rows.append({
                "Driver": drv,
                "LapNumber": float(lap),
                "LapTime": pd.Timedelta(seconds=90 + lap * 0.1),
                "Stint": 1.0 if lap <= 3 else 2.0,
                "Compound": "MEDIUM" if lap <= 3 else "HARD",
                "TyreLife": float(lap if lap <= 3 else lap - 3),
                "Position": 1.0 if drv == "VER" else 2.0,
                "PitInTime": pd.Timedelta(minutes=5) if lap == 3 else pd.NaT,
                "PitOutTime": pd.Timedelta(minutes=5) if lap == 4 else pd.NaT,
                "TrackStatus": "14" if lap == 5 else "1",   # Safety Car au tour 5
                "Deleted": False,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def event():
    return pd.Series({
        "RoundNumber": 1, "EventName": "Test Grand Prix", "Country": "France",
        "Location": "Dijon-Prenois", "EventDate": pd.Timestamp("2026-03-08"),
    })
