# models/shared.py
import re
from datetime import datetime

ANCHOR_ORIGINS = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
EPIC_ORIGINS_TODAY = {"Trinidad", "Tobago"}
EPIC_ORIGINS_WEEK = {"WASP-12b"}
EPIC_ORIGINS_MONTH = {"Macedonia"}
THREE_AMIGOS = {0, 40, -40, 54, -54}

# ---- Time Classification ----
def classify_time(timestr):
    """Classify time as Open, Early, or Late."""
    try:
        t = datetime.strptime(timestr, "%H:%M").time()
    except Exception:
        return "Unknown"
    if t.hour == 17 and t.minute == 0:
        return "Open"
    if t.hour == 18 and t.minute == 0:
        return "Open"
    if t < datetime.strptime("02:00", "%H:%M").time():
        return "Early"
    if t >= datetime.strptime("02:00", "%H:%M").time():
        return "Late"
    return "Unknown"

# ---- Origin Checks ----
def any_origin_anchor_or_epic(sequence):
    for row in sequence:
        origin = row.get("Origin", "")
        if origin in ANCHOR_ORIGINS:
            return True
        if origin in EPIC_ORIGINS_TODAY:
            return True
        if origin in EPIC_ORIGINS_WEEK:
            return True
        if origin in EPIC_ORIGINS_MONTH:
            return True
    return False

# ---- Three Amigos Count ----
def count_amigos(sequence):
    return sum(1 for row in sequence if row.get("M #") in THREE_AMIGOS)

# ---- Polarity Utilities ----
def get_polarity(m):
    return "+" if m > 0 else "-" if m < 0 else "0"

def all_same_polarity(sequence):
    polarities = {get_polarity(row["M #"]) for row in sequence}
    return len(polarities) == 1

def polarity_shift_last(sequence):
    if len(sequence) < 2:
        return False
    prev = get_polarity(sequence[-2]["M #"])
    last = get_polarity(sequence[-1]["M #"])
    return prev != last

def is_opposite_polarity(a, b):
    return get_polarity(a["M #"]) != get_polarity(b["M #"])

def polarity_alternates(sequence):
    if len(sequence) < 2:
        return False
    polarities = [get_polarity(row["M #"]) for row in sequence]
    return all(p1 != p2 for p1, p2 in zip(polarities, polarities[1:]))

# ---- M # Order Checks ----
def descending_abs_m(sequence):
    abs_vals = [abs(row["M #"]) for row in sequence]
    return abs_vals == sorted(abs_vals, reverse=True)

def is_ascending_abs_m(sequence):
    abs_vals = [abs(row["M #"]) for row in sequence]
    return abs_vals == sorted(abs_vals)
