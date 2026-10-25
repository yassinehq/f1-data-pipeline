"""Point d'entrée : python -m src.pipeline [--season 2026]"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from src import extract, load, transform

log = logging.getLogger("pipeline")


def run(season: int, db_path: str, cache_dir: str, force: bool = False) -> int:
    extract.enable_cache(cache_dir)
    con = load.connect(db_path)

    races = extract.completed_races(season)
    already = set() if force else load.loaded_rounds(con, season)
    todo = races[~races["RoundNumber"].isin(already)]
    log.info("Saison %s : %d GP terminés, %d déjà en base, %d à charger",
             season, len(races), len(already), len(todo))

    loaded, failed = 0, 0
    for _, event in todo.iterrows():
        rnd = int(event["RoundNumber"])
        name = event["EventName"]
        try:
            raw_results, raw_laps = extract.fetch_race(season, rnd)
            results = transform.clean_results(raw_results, season, rnd)
            laps = transform.clean_laps(raw_laps, season, rnd)
            transform.validate(results, laps)
            load.load_race(con, {
                "races": transform.build_race(event, season),
                "results": results,
                "laps": laps,
                "stints": transform.build_stints(laps),
            })
            loaded += 1
            log.info("✔ %s : %d tours, %d pilotes", name, len(laps), len(results))
        except transform.DataQualityError as exc:
            failed += 1
            log.error("✘ %s rejeté (qualité) : %s", name, exc)
        except Exception as exc:  # données pas encore publiées, coupure réseau…
            failed += 1
            log.warning("… %s ignoré pour l'instant : %s", name, exc)

    total_laps = con.execute("SELECT count(*) FROM laps").fetchone()[0]
    log.info("Terminé : %d chargé(s), %d échec(s). %d tours en base.", loaded, failed, total_laps)
    con.close()
    return 1 if failed and not loaded and len(todo) else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de données F1")
    parser.add_argument("--season", type=int, default=date.today().year)
    parser.add_argument("--db", default="data/f1.duckdb")
    parser.add_argument("--cache", default="cache")
    parser.add_argument("--force", action="store_true", help="recharge toute la saison")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(run(args.season, args.db, args.cache, args.force))


if __name__ == "__main__":
    main()
