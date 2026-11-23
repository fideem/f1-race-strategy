"""Test logiki build_lap_table na małych, ręcznie zrobionych danych (bez internetu).
Przejdzie, gdy zrobisz TODO 1-3 w season.py.  Uruchom: uv run pytest -v"""

import pandas as pd

from f1_race_strategy import season


def fake_fetch(endpoint, **params):
    data = {
        "laps": pd.DataFrame({
            "session_key": [1] * 6, "driver_number": [4] * 6, "lap_number": [1, 2, 3, 4, 5, 6],
            "lap_duration": [95.0, 90.0, 90.2, 110.0, 92.0, 89.5],
            "is_pit_out_lap": [False, False, False, False, True, False],
        }),
        "stints": pd.DataFrame({
            "session_key": [1, 1], "driver_number": [4, 4], "stint_number": [1, 2],
            "compound": ["MEDIUM", "HARD"], "lap_start": [1, 5], "lap_end": [4, 6],
            "tyre_age_at_start": [0, 2],
        }),
        "pit": pd.DataFrame({"session_key": [1], "driver_number": [4], "lap_number": [4],
                             "pit_duration": [22.0]}),
        "weather": pd.DataFrame({"session_key": [1, 1], "track_temperature": [30.0, 32.0],
                                 "rainfall": [0, 0]}),
        "race_control": pd.DataFrame({"session_key": [1], "lap_number": [1], "category": ["Flag"],
                                      "flag": ["GREEN"], "message": ["GREEN LIGHT - PIT EXIT OPEN"]}),
    }
    return data[endpoint]


def test_build_lap_table(monkeypatch):
    monkeypatch.setattr(season, "fetch", fake_fetch)
    df = season.build_lap_table(1).sort_values("lap_number").reset_index(drop=True)
    assert len(df) == 6  # każde okrążenie dokładnie raz
    assert df["compound"].tolist() == ["MEDIUM"] * 4 + ["HARD"] * 2
    assert df["tyre_age"].tolist() == [0, 1, 2, 3, 2, 3]
    assert df.loc[df["lap_number"] == 4, "is_pit_in_lap"].item()
    assert not df["is_sc"].any()
