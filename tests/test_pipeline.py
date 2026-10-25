import pandas as pd
import pytest

from src import load, transform


def build_frames(raw_results, raw_laps, event):
    results = transform.clean_results(raw_results, 2026, 1)
    laps = transform.clean_laps(raw_laps, 2026, 1)
    return {
        "races": transform.build_race(event, 2026),
        "results": results,
        "laps": laps,
        "stints": transform.build_stints(laps),
    }


def test_tours_propres(raw_laps):
    laps = transform.clean_laps(raw_laps, 2026, 1).set_index(["driver", "lap_number"])
    assert not laps.loc[("VER", 1), "is_clean"]   # départ
    assert not laps.loc[("VER", 3), "is_clean"]   # entrée aux stands
    assert not laps.loc[("VER", 4), "is_clean"]   # sortie des stands
    assert not laps.loc[("VER", 5), "is_clean"]   # Safety Car
    assert laps.loc[("VER", 2), "is_clean"]
    assert laps.loc[("VER", 6), "is_clean"]


def test_relais(raw_laps):
    stints = transform.build_stints(transform.clean_laps(raw_laps, 2026, 1))
    ver = stints[stints["driver"] == "VER"].set_index("stint")
    assert list(ver["compound"]) == ["MEDIUM", "HARD"]
    assert ver.loc[1, "n_laps"] == 3 and ver.loc[2, "start_lap"] == 4


def test_controle_qualite_detecte_deux_vainqueurs(raw_results, raw_laps):
    raw_results.loc[1, "Position"] = 1.0
    results = transform.clean_results(raw_results, 2026, 1)
    laps = transform.clean_laps(raw_laps, 2026, 1)
    with pytest.raises(transform.DataQualityError, match="vainqueurs"):
        transform.validate(results, laps)


def test_controle_qualite_temps_negatif(raw_results, raw_laps):
    raw_laps.loc[0, "LapTime"] = pd.Timedelta(seconds=-1)
    with pytest.raises(transform.DataQualityError, match="négatif"):
        transform.validate(transform.clean_results(raw_results, 2026, 1),
                           transform.clean_laps(raw_laps, 2026, 1))


def test_chargement_idempotent(tmp_path, raw_results, raw_laps, event):
    con = load.connect(tmp_path / "test.duckdb")
    frames = build_frames(raw_results, raw_laps, event)
    load.load_race(con, frames)
    load.load_race(con, frames)  # deuxième passage : aucun doublon
    assert con.execute("SELECT count(*) FROM laps").fetchone()[0] == 12
    assert con.execute("SELECT count(*) FROM races").fetchone()[0] == 1
    assert load.loaded_rounds(con, 2026) == {1}
