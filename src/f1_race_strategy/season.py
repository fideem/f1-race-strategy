"""Build a season-wide lap table (input for the tyre degradation model).

Usage:   uv run python -m f1_race_strategy.season 2025
Output:  data/processed/laps_2025.parquet  (one row = one lap by one driver)
"""

import sys

import pandas as pd

from f1_race_strategy.openf1 import DATA_DIR, fetch

PROCESSED_DIR = DATA_DIR / "processed"

LAP_COLUMNS = [
    "session_key",
    "driver_number",
    "lap_number",
    "lap_duration",
    "compound",
    "stint_number",
    "tyre_age",
    "is_pit_in_lap",
    "is_pit_out_lap",
    "is_sc",
    "track_temperature",
    "rainfall",
]


def race_sessions(year: int) -> pd.DataFrame:
    """Return the season's Grand Prix races (sprints excluded), sorted by start date."""
    s = fetch("sessions", year=year, session_name="Race")
    cols = ["session_key", "meeting_key", "circuit_short_name", "country_name", "date_start"]
    return s.sort_values("date_start")[cols].reset_index(drop=True)


def build_lap_table(session_key: int) -> pd.DataFrame:
    """Build a per-lap table for one race with tyre and track-condition features.

    Combines the OpenF1 ``laps``, ``stints``, ``pit``, ``weather`` and
    ``race_control`` endpoints for the given session.

    Returns one row per driver lap with the columns in ``LAP_COLUMNS``:
    session_key, driver_number, lap_number, lap_duration, compound,
    stint_number, tyre_age (laps on the current set, including laps run
    before this stint), is_pit_in_lap, is_pit_out_lap, is_sc (Safety Car,
    VSC or red flag), track_temperature and rainfall.

    Simplifications:
    - A lap is flagged ``is_sc`` if any SC/VSC/red-flag message in race
      control has that lap_number; the exact start/end of the period is ignored.
    - Weather is a single value per race: mean track temperature and
      max rainfall (i.e. whether it rained at all).
    """
    laps = fetch("laps", session_key=session_key)
    stints = fetch("stints", session_key=session_key)
    pit = fetch("pit", session_key=session_key)
    weather = fetch("weather", session_key=session_key)
    race_control = fetch("race_control", session_key=session_key)

    # 1. Match each lap to the stint whose lap range contains it.
    df = laps.merge(stints, on=["session_key", "driver_number"])
    df = df.query("lap_start <= lap_number <= lap_end").copy()

    # 2. Tyre age on this lap.
    df["tyre_age"] = df["tyre_age_at_start"] + (df["lap_number"] - df["lap_start"])

    # 3a. Pit-in lap: the (driver, lap) pair appears in the pit table.
    pit_keys = pit[["driver_number", "lap_number"]].drop_duplicates()
    df = df.merge(pit_keys, on=["driver_number", "lap_number"], how="left", indicator=True)
    df["is_pit_in_lap"] = df["_merge"] == "both"
    df = df.drop(columns="_merge")

    # 3b. Laps under Safety Car, Virtual Safety Car or red flag.
    sc_mask = race_control["message"].str.contains("SAFETY CAR|VIRTUAL", na=False) | (
        race_control["flag"] == "RED"
    )
    df["is_sc"] = df["lap_number"].isin(race_control.loc[sc_mask, "lap_number"])

    # 4. Track conditions: one value per race.
    df["track_temperature"] = weather["track_temperature"].mean()
    df["rainfall"] = weather["rainfall"].max()

    return df[LAP_COLUMNS]


def build_season(year: int) -> pd.DataFrame:
    """Build the lap table for every race of the season and save it as parquet.

    The first run downloads data from OpenF1 (a few minutes); later runs
    read from the cache in data/raw.
    """
    sessions = race_sessions(year)
    frames = []
    for row in sessions.itertuples():
        print(f"{row.date_start[:10]} {row.circuit_short_name:<20}", end=" ", flush=True)
        df = build_lap_table(row.session_key)
        df["circuit"] = row.circuit_short_name
        frames.append(df)
        print(f"{len(df)} laps")
    season = pd.concat(frames, ignore_index=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"laps_{year}.parquet"
    season.to_parquet(out, index=False)
    print(f"Saved {len(season)} rows to {out}")
    return season


if __name__ == "__main__":
    build_season(int(sys.argv[1]) if len(sys.argv) > 1 else 2025)
