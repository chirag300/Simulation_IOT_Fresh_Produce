import math


def q10_degradation_per_min(L_ref_hours, T, T_ref=4.0, Q10=2.0):
    L_T = L_ref_hours / (Q10 ** ((T - T_ref) / 10.0))
    r_per_hour = 1.0 / max(L_T, 1e-6)
    return r_per_hour / 60.0


def arrhenius_deg_per_min(L_ref_hours, T, A, Ea, R=8.314, T_ref_c=4.0):
    # Optional: calibrate A,Ea to match L_ref at T_ref
    T_k = T + 273.15
    k = A * math.exp(-Ea / (R * T_k))
    return (k / 60.0)
