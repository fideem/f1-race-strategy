# F1 Race Strategy – tyre degradation in the 2025 season

> 🚧 Work in progress

**Question:** how much lap time does a Formula 1 car lose with every lap on the same set of tyres,
and how does it differ between SOFT, MEDIUM and HARD compounds?

## Data

[OpenF1 API](https://openf1.org) – every race of the 2025 season: `laps`, `stints`, `pit`, `weather`, `race_control`.
One row = one lap of one driver (`data/processed/laps_2025.parquet`, built by `src/f1_race_strategy/season.py`).

Cleaning: dry compounds only; lap 1, pit-in / pit-out laps and Safety Car laps removed.
<!-- TODO: ile okrążeń zostało (liczba i %), jakie uproszczenia (np. SC po lap_number) -->

## Method

1. Target: lap time relative to the driver's median lap in that race (removes car/driver/track pace).
2. Features: tyre age, lap number (fuel burn proxy), compound.
3. Train/test split **by race** (last N races as test) to avoid leakage between laps of the same race.
4. Baseline (mean) → linear regression → (optional) gradient boosting. Metric: MAE in seconds.

## Results

<!-- TODO: wykres degradacji per mieszanka + tabela MAE -->

| Model | MAE test (s) |
|---|---|
| Baseline (mean) | TODO |
| Linear regression | TODO |

Key finding: <!-- TODO: np. "SOFT loses ~0.0X s per lap vs HARD ~0.0Y s" -->

## Run it

```bash
uv sync
uv run python -m f1_race_strategy.season 2025   # downloads & caches data (first run takes a few minutes)
uv run pytest
```
Then open `notebooks/02_tyre_degradation.ipynb`.

## Notebooks

- `01_first_look.ipynb` – first look at one race (2025 Australian GP), Norris vs Verstappen
- `02_tyre_degradation.ipynb` – season data, cleaning, model

## Limitations & next steps

<!-- TODO: np. klasyfikator "czy zjedzie w ciągu N okrążeń", symulator 1 vs 2 postoje -->

## Related

[F1 Data Agent](https://github.com/fideem/f1-data-agent) – an LLM agent that answers questions about the same data with SQL.
