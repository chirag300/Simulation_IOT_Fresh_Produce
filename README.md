# Project: Simulation of IoT-Enabled Cold Chain for Fresh Produce

**Status:** Core simulation complete with multiple routing policies, Monte Carlo experiments, and live visualization.

## 1. Project Objective

This project simulates the delivery of temperature-sensitive fresh produce using a refrigerated vehicle across multiple stops.  
It models **temperature dynamics**, **door-opening events**, **passive heat drift**, and **cooling rates**,  
while tracking **shelf-life decay** using the Q10 model for each SKU.

The system compares multiple routing strategies (Nearest Neighbor, Two-Opt, OR-Tools TSP)  
and records KPIs like **total time**, **remaining freshness**, and **average shelf-life per unit delivered**.

## 2. Project File Structure

```
Simulation_IOT_Fresh_Produce-main/
│
├── run_once.py                  # Top-level script for single-run simulation
│
├── coldchain_sim/
│   ├── __init__.py
│   ├── agents.py                 # Mesa agents for vehicle and stops
│   ├── config.py                 # Simulation parameters and SKU definitions
│   ├── graph.py                  # Graph generators for symmetric/asymmetric routes
│   ├── model.py                  # Core Mesa model logic
│   ├── objectives.py             # KPI calculation functions
│   ├── run_once.py                # Single-run simulation module
│   ├── shelf_life.py             # Shelf-life decay calculations (Q10 model)
│   ├── temps.py                   # Temperature dynamics modeling
│   │
│   ├── experiments/
│   │   ├── grid.py               # Compare policies once and save CSV results
│   │   └── mc.py                 # Monte Carlo multi-seed experiments
│   │
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── base.py               # Base class for route policies
│   │   ├── heuristics.py         # Nearest Neighbor, Two-Opt heuristics
│   │   ├── heuristics_fixed.py   # Fixed variants of heuristics
│   │   └── ortools_tsp.py        # OR-Tools TSP policy
│   │
│   └── viz/
│       └── live_mpl.py           # Live matplotlib visualization
```

## 3. Setup and Usage Instructions

### 3.1. Environment Setup

```bash
git clone https://github.com/your-org/Simulation_IOT_Fresh_Produce-main.git
cd Simulation_IOT_Fresh_Produce-main

python -m venv .venv
source .venv/bin/activate         # On Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install mesa networkx matplotlib pandas ortools
```

> If `ortools` fails to build, use:
> ```bash
> pip install --only-binary=:all: ortools
> ```

### 3.2. Running a Single Simulation

```bash
python run_once.py
# or equivalently
python -m coldchain_sim.run_once
```

### 3.3. Comparing Policies Once (Grid Run)

```bash
python -m coldchain_sim.experiments.grid
```

This will save `results.csv` with KPIs for Nearest Neighbor, Two-Opt, and OR-Tools.

### 3.4. Monte Carlo Experiments

```bash
python -m coldchain_sim.experiments.mc --seeds 20 --start-seed 1 --asymmetric --outfile mc_results.csv
```

**Arguments**:
- `--seeds` (default: 20) — number of random seeds to run.
- `--start-seed` (default: 1) — first seed value.
- `--asymmetric` — use asymmetric travel times.
- `--outfile` — output CSV file path.

### 3.5. Live Visualization

```bash
python -m coldchain_sim.viz.live_mpl
```

Shows:
- Left: network with depot (blue), stores (gray→green when served), vehicle (red dot)
- Top-right: trailer temperature over time
- Bottom-right: average remaining minutes per unit delivered so far

## 4. Routing Policies

| Policy             | Description                                       | Module                                   |
|--------------------|---------------------------------------------------|------------------------------------------|
| `NearestNeighbor`  | Greedy nearest-stop selection                     | `coldchain_sim/policies/heuristics.py`   |
| `TwoOpt`           | Nearest Neighbor seed + 2-opt improvement         | `coldchain_sim/policies/heuristics.py`   |
| `ORToolsTSP`       | Optimal route with OR-Tools constraint solver     | `coldchain_sim/policies/ortools_tsp.py`  |

## 5. Simulation Parameters

Defined in `coldchain_sim/config.py`:

- **Service time**: `service_minutes` per stop  
- **Trailer setpoint**: `setpoint_c`  
- **Cooling rate**: `cool_rate_per_min`  
- **Door-open spike**: `temp_spike_on_open`  
- **Ambient drift**: `temp_drift_ambient`  
- **Max simulation time**: `max_minutes`  

**SKUs**: `DEFAULT_SKUS` contains each item's reference shelf life (`L_ref_hours`), reference temperature (`T_ref`), and Q10 factor.

## 6. Output & KPIs

- **Minute-level DataFrame** — collected via Mesa's `DataCollector`
- **Per-delivery log** — remaining life per SKU at each stop
- **CSV summaries**:
  - `results.csv` — single-run policy comparison
  - `mc_results.csv` — Monte Carlo statistics

## 7. Next Steps

- 📈 Add support for real-world graph data from OpenStreetMap.
- 🧪 Test sensitivity to parameter variations.
- ⚡ Parallelize Monte Carlo runs for speed.
- 📊 Integrate Plotly/Dash dashboards for post-simulation analysis.

## 8. License & Contact

This is a research-focused simulation framework.  
Please cite appropriately when using in academic or production settings.

**Maintained by:** Your Name / Team  
For questions, open an issue or contact via email.
