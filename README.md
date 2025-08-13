````markdown
# ColdChain IoT Fresh Produce Simulation

A lightweight simulation of a temperature-controlled delivery route for perishable goods. It models a single refrigerated vehicle serving multiple stores while tracking trailer temperature dynamics and the **remaining shelf-life** of each SKU delivered.

## ✨ Features
- Synthetic road network with depot + 10 customers (`coldchain_sim.graph`).
- Multiple routing policies: Nearest Neighbor, 2-Opt local search, and Google OR-Tools TSP.
- Temperature model with door-open spikes, passive drift, and active cooling.
- Shelf-life decay using Q10 model per SKU.
- KPIs recorded each minute and at each delivery.
- Batch experiments (grid + Monte Carlo) and a **live Matplotlib** visualization.

## 📁 Project Structure
```
Simulation_IOT_Fresh_Produce-main/
- run_once.py
- coldchain_sim/
  - __init__.py
  - agents.py
  - config.py
  - graph.py
  - model.py
  - objectives.py
  - run_once.py
  - shelf_life.py
  - temps.py
  - experiments/
    - grid.py
    - mc.py
  - policies/
    - __init__.py
    - base.py
    - heuristics.py
    - heuristics_fixed.py
    - ortools_tsp.py
  - viz/
    - live_mpl.py
```

### Key Modules
- `coldchain_sim/model.py` — Core Mesa model orchestrating time steps, deliveries, temperature, and shelf-life logging.
- `coldchain_sim/config.py` — Simulation knobs (service time, setpoint, heat dynamics) and default SKUs with Q10.
- `coldchain_sim/graph.py` — Synthetic depot+customers graph; symmetric or asymmetric travel times.
- `coldchain_sim/policies/` — Route builders:
  - `heuristics.py`: `NearestNeighborPolicy`, `TwoOptPolicy`, helper `path_time`.
  - `ortools_tsp.py`: `ORToolsTSPPolicy` using Google OR-Tools Routing.
- `coldchain_sim/objectives.py` — KPIs such as total minutes and remaining life.
- `coldchain_sim/experiments/grid.py` — Compare policies once, write `results.csv`.
- `coldchain_sim/experiments/mc.py` — Monte-Carlo across many seeds; writes `mc_results.csv`.
- `coldchain_sim/viz/live_mpl.py` — Live animation of a single run (network, temp trace, KPI).

## 🧰 Requirements

Python ≥ 3.9. Install dependencies (no GPU needed):

```
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install mesa networkx matplotlib pandas ortools
```

> If `ortools` fails to build on your platform, try a prebuilt wheel:
> `pip install --only-binary=:all: ortools`

## 🚀 Quick Start

From the project root (`Simulation_IOT_Fresh_Produce-main`):

### 1) Single run (script)
Runs a 10-stop instance with OR-Tools TSP and prints the tail of the minute-level dataframe plus summary KPIs.

```
python run_once.py
# or equivalently
python -m coldchain_sim.run_once
```

### 2) Policy comparison grid
Runs **Nearest Neighbor**, **Two-Opt**, and **OR-Tools** once each and saves a table to `results.csv`.

```
python -m coldchain_sim.experiments.grid
```

### 3) Monte-Carlo (repeatable multi-seed study)
Evaluate multiple random seeds and write `mc_results.csv`.

```
python -m coldchain_sim.experiments.mc --seeds 20 --start-seed 1 --asymmetric --outfile mc_results.csv
```

Arguments:
- `--seeds` (int, default 20): number of seeds to run.
- `--start-seed` (int, default 1): first seed.
- `--asymmetric` (flag): use asymmetric travel times.
- `--outfile` (str, default `mc_results.csv`).

### 4) Live visualization
Animate one run with a moving vehicle, temperature trace, and KPI panel.

```
python -m coldchain_sim.viz.live_mpl
```

Use **Ctrl+C** to stop. The script draws a synthetic graph (`seed=7`) and uses the default four SKUs.

## 🔧 Customizing the Simulation

- **SKUs & Q10**: edit `coldchain_sim/config.py` → `DEFAULT_SKUS`  
  (`L_ref_hours`, `T_ref`, `Q10`).
- **Trailer dynamics**: tweak `SimParams` in `config.py`  
  (`service_minutes`, `setpoint_c`, `cool_rate_per_min`, `temp_spike_on_open`, `temp_drift_ambient`, `max_minutes`).
- **Demands & capacity**: see patterns in `run_once.py`, `experiments/grid.py`, `experiments/mc.py`.
- **Graph**: use symmetric/asymmetric or rescale in `coldchain_sim/graph.py` or the experiment helpers.

## 📊 Outputs

- **Minute-level DataFrame** (`model.datacollector`): time series of temperature and KPIs (printed in `run_once.py` via `df.tail()`).
- **Per-delivery logs**: `model.rem_life_log_per_stop` — snapshot of quantity-weighted remaining minutes by SKU for each completed stop.
- **CSV summaries**:
  - `results.csv` (grid): policy-level KPIs (route preview minutes, total time, total remaining life, units, and averages).
  - `mc_results.csv` (MC): per-seed results and aggregate stats.

## 🧪 Reproducibility

- Scripts accept or set **random seeds** to make runs repeatable (`--start-seed`, `--seeds` in MC).
- OR-Tools search is deterministic for fixed seed and model.

## 🐞 Troubleshooting

- **`ImportError: ortools`** → reinstall with a wheel: `pip install --only-binary=:all: ortools`  
- **Matplotlib backend errors** on headless servers → set `MPLBACKEND=Agg` or run non-GUI experiments (`grid.py`, `mc.py`).  
- **Animation window blank** → ensure you run `python -m coldchain_sim.viz.live_mpl` from the project root so relative imports resolve.

---
````
