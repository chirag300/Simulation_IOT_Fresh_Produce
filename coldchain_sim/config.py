from dataclasses import dataclass

@dataclass
class SKUParams:
    L_ref_hours: float
    T_ref: float = 4.0
    Q10: float = 2.0

@dataclass
class SimParams:
    service_minutes: int = 8
    setpoint_c: float = 4.0
    cool_rate_per_min: float = 0.15
    temp_spike_on_open: float = 1.8
    temp_drift_ambient: float = 0.02
    max_minutes: int = 8*60

# Update DEFAULT_SKUS to include four produce items. Each entry defines the
# nominal shelf life at the reference temperature and the Q10 factor.
DEFAULT_SKUS = {
    "strawberries": SKUParams(L_ref_hours=72, Q10=2.4),
    "romaine":      SKUParams(L_ref_hours=168, Q10=2.0),
    "blueberries":  SKUParams(L_ref_hours=120, Q10=2.2),
    "spinach":      SKUParams(L_ref_hours=96, Q10=2.3),
}

SIM = SimParams()
