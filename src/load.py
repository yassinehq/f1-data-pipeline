"""Load : stockage dans DuckDB, chargement incrémental et idempotent."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS races (
    season INTEGER, round INTEGER, event_name VARCHAR, country VARCHAR,
    location VARCHAR, race_date DATE,
    PRIMARY KEY (season, round)
);
CREATE TABLE IF NOT EXISTS results (
    season INTEGER, round INTEGER, driver VARCHAR, driver_number VARCHAR,
    full_name VARCHAR, team VARCHAR, team_color VARCHAR,
    grid_position INTEGER, position INTEGER, status VARCHAR, points DOUBLE,
    PRIMARY KEY (season, round, driver)
);
CREATE TABLE IF NOT EXISTS laps (
    season INTEGER, round INTEGER, driver VARCHAR, lap_number INTEGER,
    lap_time_s DOUBLE, stint INTEGER, compound VARCHAR, tyre_life INTEGER,
    position INTEGER, is_pit_in BOOLEAN, is_pit_out BOOLEAN,
    is_neutralised BOOLEAN, is_clean BOOLEAN,
    PRIMARY KEY (season, round, driver, lap_number)
);
CREATE TABLE IF NOT EXISTS stints (
    season INTEGER, round INTEGER, driver VARCHAR, stint INTEGER,
    compound VARCHAR, start_lap INTEGER, end_lap INTEGER, n_laps INTEGER,
    median_clean_lap_s DOUBLE,
    PRIMARY KEY (season, round, driver, stint)
);
"""

TABLES = ("races", "results", "laps", "stints")


def connect(path: str | Path = "data/f1.duckdb") -> duckdb.DuckDBPyConnection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    return con


def loaded_rounds(con: duckdb.DuckDBPyConnection, season: int) -> set[int]:
    rows = con.execute("SELECT round FROM races WHERE season = ?", [season]).fetchall()
    return {r[0] for r in rows}


def load_race(con: duckdb.DuckDBPyConnection, frames: dict[str, pd.DataFrame]) -> None:
    """Remplace une course dans une seule transaction : relancer = même résultat."""
    season = int(frames["races"]["season"].iloc[0])
    rnd = int(frames["races"]["round"].iloc[0])
    con.begin()
    try:
        for table in TABLES:
            con.execute(f"DELETE FROM {table} WHERE season = ? AND round = ?", [season, rnd])
            con.register("incoming", frames[table])
            con.execute(f"INSERT INTO {table} BY NAME SELECT * FROM incoming")
            con.unregister("incoming")
        con.commit()
    except Exception:
        con.rollback()
        raise
