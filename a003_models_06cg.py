import streamlit as st
import pandas as pd
from collections import defaultdict

# Project file 3; Models, v6, A, B & C models ***
# -----------------------
# Helper functions
# -----------------------
def feed_icon(feed):
    return "👶" if "sm" in feed.lower() else "🤔"

def sequence_signature(seq):
    return tuple(seq["M #"].tolist())

def classify_A_model(row_0, prior_rows):
    epic = {"trinidad", "tobago", "wasp-12b", "macedonia"}
    anchor = {"spain", "saturn", "jupiter", "kepler-62", "kepler-44"}
    t0 = row_0["Arrival"]
    o0 = row_0["Origin"].lower()
    time = "open" if t0.hour == 18 and t0.minute == 0 else \
           "early" if (18 < t0.hour < 2 or (t0.hour == 1 and t0.minute < 59)) else "late"
    is_epic = o0 in epic
    is_anchor = o0 in anchor
    prior = set(prior_rows["Origin"].str.lower())
    strong = bool(prior & epic) or bool(prior & anchor)

    if is_epic and time == "open": return "A01", "Open Epic 0"
    if is_anchor and time == "open": return "A02", "Open Anchor 0"
    if not is_anchor and time == "open" and strong: return "A03", "Open non-Anchor 0"
    if not is_anchor and time == "early" and strong: return "A04", "Early non-Anchor 0"
    if is_anchor and time == "late": return "A05", "Late Anchor 0"
    if not is_anchor and time == "late" and strong: return "A06", "Late non-Anchor 0"
    if not is_anchor and time == "open" and not strong: return "A07", "Open general 0"
    if not is_anchor and time == "early" and not strong: return "A08", "Early general 0"
    if not is_anchor and time == "late" and not strong: return "A09", "Late general 0"
    return None, None

def classify_B_model(seq):
    if len(seq) < 2: return None, None
    m_vals = seq["M #"].tolist()
    abs_sorted = sorted(m_vals[:-1], key=lambda x: abs(x), reverse=True)
    descending = all(abs(m_vals[i]) > abs(m_vals[i+1]) for i in range(len(m_vals)-1))
    same_polarity = all((m > 0) == (m_vals[0] > 0) for m in m_vals[:-1])
    mixed = not same_polarity
    if descending:
        if same_polarity: return "B01", "Same Polarity Descent"
        if mixed: return "B02", "Mixed Polarity Descent"
    return None, None

def classify_C_model(seq):
    if len(seq) != 3:
        return None, None
    m1, m2, m3 = seq["M #"].tolist()
    if m1 == -m3:
        if m2 == 0:
            tcat = classify_time(seq.iloc[-1]["Arrival"])
            return f"C02a{tcat}", f"Opposites, 0 in middle ({tcat})"
        else:
            tcat = classify_time(seq.iloc[-1]["Arrival"])
            return f"C02b{tcat}", f"Opposites, mid ≠ 0 ({tcat})"
    return None, None

def classify_time(t):
    if t.hour == 18:
        return "Open"
    elif 18 < t.hour < 2 or (t.hour == 1 and t.minute < 59):
        return "Early"
    else:
        return "Late"

def detect_C_models(df, model_outputs, all_signatures):
    for output in df["Output"].unique():
        subset = df[df["Output"] == output].sort_values("Arrival").reset_index(drop=True)
        for i in range(len(subset) - 2):
            seq = subset.iloc[i:i+3]
            sig = sequence_signature(seq)
            if sig in all_signatures:
                continue
            model, label = classify_C_model(seq)
            if model:
                all_signatures.add(sig)
                model_outputs[model].append({
                    "label": label,
                    "output": output,
                    "timestamp": seq.iloc[-1]["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })


def find_flexible_descents(rows):
    raw_sequences = []
    for i in range(len(rows)):
        path = []
        seen = set()
        last_abs = float("inf")
        for j in range(i, len(rows)):
            m = rows.loc[j, "M #"]
            abs_m = abs(m)
            if m == 0:
                if len(path) >= 2:
                    path.append(j)
                    raw_sequences.append(rows.loc[path])
                break
            if abs_m in seen or abs_m >= last_abs:
                continue
            path.append(j)
            seen.add(abs_m)
            last_abs = abs_m
    filtered = []
    all_signatures = [tuple(seq["M #"].tolist()) for seq in raw_sequences]
    for i, sig in enumerate(all_signatures):
        longer = any(set(sig).issubset(set(other)) and len(sig) < len(other) 
                     for j, other in enumerate(all_signatures) if i != j)
        if not longer:
            filtered.append(raw_sequences[i])
    return filtered

def find_pairs(rows, seen_signatures):
    pairs = []
    for i in range(len(rows) - 1):
        m1 = rows.iloc[i]["M #"]
        m2 = rows.iloc[i + 1]["M #"]
        if abs(m2) >= abs(m1):
            continue
        if m2 != 0:
            continue
        pair = rows.iloc[[i, i + 1]]
        sig = tuple(pair["M #"].tolist())
        if sig not in seen_signatures:
            pairs.append(pair)
    return pairs

def detect_A_models(df):
    report_time = df["Arrival"].max()
    model_outputs = defaultdict(list)
    all_signatures = set()

    for output in df["Output"].unique():
        subset = df[df["Output"] == output].sort_values("Arrival").reset_index(drop=True)
        full_matches = find_flexible_descents(subset)

        for seq in full_matches:
            if seq.shape[0] < 3 or seq.iloc[-1]["M #"] != 0:
                continue
            sig = sequence_signature(seq)
            if sig in all_signatures:
                continue
            all_signatures.add(sig)
            prior = seq.iloc[:-1]
            last = seq.iloc[-1]
            model, label = classify_A_model(last, prior)
            if model:
                model_outputs[model].append({
                    "label": label,
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })

        pairs = find_pairs(subset, all_signatures)
        for seq in pairs:
            sig = sequence_signature(seq)
            if sig in all_signatures:
                continue
            all_signatures.add(sig)
            prior = seq.iloc[:-1]
            last = seq.iloc[-1]
            model, label = classify_A_model(last, prior)
            if model:
                pr_model = model + "pr"
                model_outputs[pr_model].append({
                    "label": f"Pair to {label}",
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })
            b_model, b_label = classify_B_model(seq)
            if b_model:
                pr_model = b_model + "pr"
                model_outputs[pr_model].append({
                    "label": f"Pair to {b_label}",
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })

    detect_C_models(df, model_outputs, all_signatures)
    return model_outputs, report_time

def show_a_model_results(model_outputs, report_time):
    base_labels = {
        "A01": "Open Epic 0", "A02": "Open Anchor 0", "A03": "Open non-Anchor 0",
        "A04": "Early non-Anchor 0", "A05": "Late Anchor 0", "A06": "Late non-Anchor 0",
        "A07": "Open general 0", "A08": "Early general 0", "A09": "Late general 0",
        "B01": "Same Polarity Descent", "B02": "Mixed Polarity Descent",
        "C01": "Polarity Shift After Midnight", "C01s": "Polarity Shift Before Midnight",
        "C02aOpen": "Opposites, 0 in middle (Open)", "C02aEarly": "Opposites, 0 in middle (Early)", "C02aLate": "Opposites, 0 in middle (Late)",
        "C02bOpen": "Opposites, mid ≠ 0 (Open)", "C02bEarly": "Opposites, mid ≠ 0 (Early)", "C02bLate": "Opposites, mid ≠ 0 (Late)"
    }

    st.subheader("🔍 A + B + C Model Results")
    for code, label in base_labels.items():
        for suffix, title in [("", f"2+ to {label}"), ("pr", f"Pair to {label}")]:
            key = code + suffix
            results = model_outputs.get(key, [])
            if not results:
                continue
            output_count = len(set(r["output"] for r in results))
            header = f"{key}. {title} – {output_count} output{'s' if output_count != 1 else ''}"

            with st.expander(header):
                today_results = [r for r in results if "[0]" in r["sequence"].iloc[-1]["Day"]]
                other_results = [r for r in results if "[0]" not in r["sequence"].iloc[-1]["Day"]]

                def render_group(name, group):
                    st.markdown(f"#### {name}")
                    output_groups = defaultdict(list)
                    for r in group:
                        output_groups[r["output"]].append(r)

                    for out_val, items in output_groups.items():
                        latest = max(items, key=lambda r: r["timestamp"])
                        hrs = int((report_time - latest["timestamp"]).total_seconds() / 3600)
                        ts = latest["timestamp"].strftime('%-m/%-d/%y %H:%M')
                        subhead = f"🔹 Output {out_val:,.3f} – {len(items)} descending {hrs} hours ago at {ts}"

                        with st.expander(subhead):
                            for res in items:
                                seq = res["sequence"]
                                m_path = " → ".join([f"|{row['M #']}|" for _, row in seq.iterrows()])
                                icons = "".join([feed_icon(row["Feed"]) for _, row in seq.iterrows()])
                                st.markdown(f"{m_path} Cross [{icons}]")
                                st.table(seq.reset_index(drop=True))

                if today_results:
                    render_group("📅 Today", today_results)
                if other_results:
                    render_group("📦 Other Days", other_results)
                if not today_results and not other_results:
                    st.markdown("No matching outputs.")

def run_a_model_detection(df):
    model_outputs, report_time = detect_A_models(df)
    show_a_model_results(model_outputs, report_time)
    return model_outputs
