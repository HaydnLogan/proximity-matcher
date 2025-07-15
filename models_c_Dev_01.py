# models/models_c.py
from .shared import (
    classify_time,
    polarity_shift_last,
    descending_abs_m,
    any_origin_anchor_or_epic,
    count_amigos,
    is_opposite_polarity,
    is_ascending_abs_m,
    polarity_alternates,
)

C_MODELS = {}

# C01a[L0] - Late Night Influence Shift * Origin today
def is_c01a_L0(sequence):
    if len(sequence) < 3:
        return False
    if classify_time(sequence[-1]["Arrival"]) != "Late":
        return False
    if sequence[-1]["Day"] != "0":
        return False
    if not polarity_shift_last(sequence):
        return False
    if not descending_abs_m(sequence[:-1]):
        return False
    if count_amigos(sequence) < 1:
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
C_MODELS["C01a[L0]"] = is_c01a_L0

# C01a[E0] - Early Night Influence Shift * Origin today
def is_c01a_E0(sequence):
    if len(sequence) < 3:
        return False
    if classify_time(sequence[-1]["Arrival"]) != "Early":
        return False
    if sequence[-1]["Day"] != "0":
        return False
    if not polarity_shift_last(sequence):
        return False
    if not descending_abs_m(sequence[:-1]):
        return False
    if count_amigos(sequence) < 1:
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
C_MODELS["C01a[E0]"] = is_c01a_E0

# C01b[L0] - Late Night Influence Shift NO* Origin today
def is_c01b_L0(sequence):
    if len(sequence) < 3:
        return False
    if classify_time(sequence[-1]["Arrival"]) != "Late":
        return False
    if sequence[-1]["Day"] != "0":
        return False
    if not polarity_shift_last(sequence):
        return False
    if not descending_abs_m(sequence[:-1]):
        return False
    if count_amigos(sequence) < 1:
        return False
    if any_origin_anchor_or_epic(sequence):
        return False
    return True
C_MODELS["C01b[L0]"] = is_c01b_L0

# C01b[E0] - Early Night Influence Shift NO* Origin today
def is_c01b_E0(sequence):
    if len(sequence) < 3:
        return False
    if classify_time(sequence[-1]["Arrival"]) != "Early":
        return False
    if sequence[-1]["Day"] != "0":
        return False
    if not polarity_shift_last(sequence):
        return False
    if not descending_abs_m(sequence[:-1]):
        return False
    if count_amigos(sequence) < 1:
        return False
    if any_origin_anchor_or_epic(sequence):
        return False
    return True
C_MODELS["C01b[E0]"] = is_c01b_E0

# C02aX - 0 in middle
def is_c02a(sequence, time_class):
    if len(sequence) != 3:
        return False
    if sequence[1]["M #"] != 0:
        return False
    if not is_opposite_polarity(sequence[0], sequence[2]):
        return False
    if classify_time(sequence[-1]["Arrival"]) != time_class:
        return False
    if sequence[-1]["Day"] != "0":
        return False
    return True
C_MODELS["C02a1.L"] = lambda seq: is_c02a(seq, "Late")
C_MODELS["C02a2.E"] = lambda seq: is_c02a(seq, "Early")
C_MODELS["C02a3.O"] = lambda seq: is_c02a(seq, "Open")

# C02bX - non-0 in middle
def is_c02b(sequence, time_class):
    if len(sequence) != 3:
        return False
    if sequence[1]["M #"] == 0:
        return False
    if not is_opposite_polarity(sequence[0], sequence[2]):
        return False
    if classify_time(sequence[-1]["Arrival"]) != time_class:
        return False
    if sequence[-1]["Day"] != "0":
        return False
    return True
C_MODELS["C02b1.L"] = lambda seq: is_c02b(seq, "Late")
C_MODELS["C02b2.E"] = lambda seq: is_c02b(seq, "Early")
C_MODELS["C02b3.O"] = lambda seq: is_c02b(seq, "Open")

# C03a - Quad descending to Origin Open today
def is_c03a(sequence):
    if len(sequence) < 4:
        return False
    if not polarity_alternates(sequence):
        return False
    if not descending_abs_m(sequence):
        return False
    last = sequence[-1]
    if last["M #"] != 0:
        return False
    if last["Day"] != "0":
        return False
    if classify_time(last["Arrival"]) != "Open":
        return False
    if not any_origin_anchor_or_epic([last]):
        return False
    return True
C_MODELS["C03a"] = is_c03a

# C03b - Quad descending to Origin Open previous day
def is_c03b(sequence):
    if len(sequence) < 4:
        return False
    if not polarity_alternates(sequence):
        return False
    if not descending_abs_m(sequence):
        return False
    last = sequence[-1]
    if last["M #"] != 0:
        return False
    if last["Day"] == "0":
        return False
    if classify_time(last["Arrival"]) != "Open":
        return False
    if not any_origin_anchor_or_epic([last]):
        return False
    return True
C_MODELS["C03b"] = is_c03b

# C04a - Trio up to |54| today
def is_c04a(sequence):
    if len(sequence) != 3:
        return False
    if [abs(t["M #"]) for t in sequence] != [0, 40, 54]:
        return False
    if sequence[-1]["Day"] != "0":
        return False
    return True
C_MODELS["C04a"] = is_c04a

# C04b - Trio up to |54| ≠[0]
def is_c04b(sequence):
    if len(sequence) != 3:
        return False
    if [abs(t["M #"]) for t in sequence] != [0, 40, 54]:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    return True
C_MODELS["C04b"] = is_c04b
