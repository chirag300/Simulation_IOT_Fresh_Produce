def total_time_minutes(model):
    v = model.vehicle
    return v.drive_min + v.service_min


def total_remaining_life_at_deliveries(model):
    return sum(model.rem_life_log)


def weighted_score(model, alpha=1.0, beta=1e-3):
    return total_time_minutes(model) - beta * total_remaining_life_at_deliveries(model)
