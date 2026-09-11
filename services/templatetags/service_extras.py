from django import template

register = template.Library()

CATEGORY_ICONS = {
    "electrician": "bi-lightning-charge",
    "plumber": "bi-droplet",
    "carpenter": "bi-hammer",
    "painter": "bi-brush",
    "cleaner": "bi-stars",
    "caregiver": "bi-heart-pulse",
    "driver": "bi-car-front",
    "gardener": "bi-flower1",
    "technician": "bi-wrench-adjustable-circle",
    "domestic_helper": "bi-house-heart",
    "other": "bi-tools",
}


@register.filter
def category_icon(category):
    return CATEGORY_ICONS.get(category, "bi-tools")


@register.filter
def format_distance(distance_km):
    if distance_km is None:
        return "Location unavailable"
    try:
        distance_km = float(distance_km)
    except (TypeError, ValueError):
        return "Location unavailable"
    if distance_km < 0:
        return "Location unavailable"
    if distance_km < 1:
        return f"{round(distance_km * 1000)} m away"
    return f"{round(distance_km, 1)} km away"


@register.filter
def format_eta(minutes):
    if minutes is None:
        return ""
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return ""
    if minutes <= 0:
        return ""
    return f"Approx. {minutes} min away"
