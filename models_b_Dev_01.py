# models/models_b.py
from .shared import (
    all_same_polarity,
    is_descending_abs_m,
    all_from_same_feed,
    count_day_entries,
    any_origin_anchor_or_epic,
)

B_MODELS = {}

# B01a[0]
def is_b01a_0(sequence):
    if len(sequence) < 3:
        return False
    if not all_same_polarity(sequence):
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if not all_from_same_feed(sequence):
        return False
    if count_day_entries(sequence, "0") < 2:
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B01a[0]"] = is_b01a_0

# B01a[≠0]
def is_b01a_not0(sequence):
    if len(sequence) < 3:
        return False
    if not all_same_polarity(sequence):
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    if not all_from_same_feed(sequence):
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B01a[≠0]"] = is_b01a_not0

# B01b[0]
def is_b01b_0(sequence):
    if len(sequence) < 3:
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if count_day_entries(sequence, "0") < 2:
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B01b[0]"] = is_b01b_0

# B01b[≠0]
def is_b01b_not0(sequence):
    if len(sequence) < 3:
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B01b[≠0]"] = is_b01b_not0

# B02a[0]
def is_b02a_0(sequence):
    if len(sequence) < 3:
        return False
    if not all_same_polarity(sequence):
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if not all_from_same_feed(sequence):
        return False
    if count_day_entries(sequence, "0") < 2:
        return False
    if any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B02a[0]"] = is_b02a_0

# B02a[≠0]
def is_b02a_not0(sequence):
    if len(sequence) < 3:
        return False
    if not all_same_polarity(sequence):
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    if not all_from_same_feed(sequence):
        return False
    if any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B02a[≠0]"] = is_b02a_not0

# B02b[0]
def is_b02b_0(sequence):
    if len(sequence) < 3:
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if count_day_entries(sequence, "0") < 2:
        return False
    if any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B02b[0]"] = is_b02b_0

# B02b[≠0]
def is_b02b_not0(sequence):
    if len(sequence) < 3:
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) != 40:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    if any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B02b[≠0]"] = is_b02b_not0

# B03a[0]
def is_b03a_0(sequence):
    if len(sequence) < 3:
        return False
    if not all_same_polarity(sequence):
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) == 40:
        return False
    if not all_from_same_feed(sequence):
        return False
    if count_day_entries(sequence, "0") < 2:
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B03a[0]"] = is_b03a_0

# B03a[≠0]
def is_b03a_not0(sequence):
    if len(sequence) < 3:
        return False
    if not all_same_polarity(sequence):
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) == 40:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    if not all_from_same_feed(sequence):
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B03a[≠0]"] = is_b03a_not0

# B03b[0]
def is_b03b_0(sequence):
    if len(sequence) < 3:
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) == 40:
        return False
    if count_day_entries(sequence, "0") < 2:
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B03b[0]"] = is_b03b_0

# B03b[≠0]
def is_b03b_not0(sequence):
    if len(sequence) < 3:
        return False
    if not is_descending_abs_m(sequence):
        return False
    if abs(sequence[-1]["M #"]) == 40:
        return False
    if sequence[-1]["Day"] == "0":
        return False
    if not any_origin_anchor_or_epic(sequence):
        return False
    return True
B_MODELS["B03b[≠0]"] = is_b03b_not0
