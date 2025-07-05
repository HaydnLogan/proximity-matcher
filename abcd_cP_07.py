import streamlit as st
import pandas as pd
from datetime import datetime
from collections import defaultdict

st.set_page_config(layout="wide")


# 📤 Upload CSV
st.title("🅰️ Position A Models – Output-Centric Scanner")
uploaded_file = st.file_uploader("Upload your traveler report CSV. cP v07. Output focused", type="csv")

# ✅ Feed Icon
def feed_icon(feed): return "👶" if "sm" in feed else "🧔"

# 🔍 Flexible descent detection to M # 0
def find_flexible_descents(df_subset):
    rows = df_subset[df_subset["Output"] > 0].sort_values("Arrival").reset_index(drop=True)
    sequences = []
    total = len(rows)

    for i in range(total):
        path = []
        seen_abs = set()
        last_abs = float("inf")

        for j in range(i, total):
            m = rows.loc[j, "M #"]
            abs_m = abs(m)

            if m == 0:
                if len(path) >= 2:
                    path.append(j)
                    sequences.append(rows.loc[path])
                break

            if abs_m in seen_abs or abs_m >= last_abs:
                continue

            path.append(j)
            seen_abs.add(abs_m)
            last_abs = abs_m

    return sequences

# 🧠 Sequence signature for uniqueness
def sequence_signature(seq):
    return tuple(seq["M #"].tolist())

# 🧠 Classification logic for A Models
def classify_A_model(row_0, prior_rows):
    epic = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
    anchor = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
    t0 = row_0["Arrival"]
    o0 = row_0["Origin"]
    time = "open" if t0.hour == 18 and t0.minute == 0 else \
           "early" if (18 < t0.hour < 2 or (t0.hour == 1 and t0.minute < 59)) else "late"
    is_epic = o0 in epic
    is_anchor = o0 in anchor
    prior = set(prior_rows["Origin"])
    has_strong = bool(prior & epic) or bool(prior & anchor)

    if is_epic and time == "open": return "A01", "Open Epic 0"
    if is_anchor and time == "open": return "A02", "Open Anchor 0"
    if not is_anchor and time == "open" and has_strong: return "A03", "Open non-Anchor 0"
    if not is_anchor and time == "early" and has_strong: return "A04", "Early non-Anchor 0"
    if is_anchor and time == "late": return "A05", "Late Anchor 0"
    if not is_anchor and time == "late" and has_strong: return "A06", "Late non-Anchor 0"
    if not is_anchor and time == "open" and not has_strong: return "A07", "Open general 0"
    if not is_anchor and time == "early" and not has_strong: return "A08", "Early general 0"
    if not is_anchor and time == "late" and not has_strong: return "A09", "Late general 0"
    return None, None

# 🔍 A Model detection grouped by Output
def detect_A_models(df):
    report_time = df["Arrival"].max()
    model_outputs = defaultdict(list)

    for output in df["Output"].unique():
        subset = df[df["Output"] == output]
        sequences = find_flexible_descents(subset)

        seen_signatures = set()
        for seq in sequences:
            if seq.shape[0] < 3 or seq.iloc[-1]["M #"] != 0:
                continue

            sig = sequence_signature(seq)
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)

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

    return model_outputs, report_time

# 🧠 Display logic per A Model and per Output
def show_a_model_results(model_outputs, report_time):
    labels = {
        "A01": "Open Epic 0", "A02": "Open Anchor 0", "A03": "Open non-Anchor 0",
        "A04": "Early non-Anchor 0", "A05": "Late Anchor 0", "A06": "Late non-Anchor 0",
        "A07": "Open general 0", "A08": "Early general 0", "A09": "Late general 0"
    }

    st.subheader("🔍 A Model Results")
    for code, label in labels.items():
        results = model_outputs.get(code, [])
        unique_outputs = set(r["output"] for r in results)
        header = f"{code}. 2+ to {label} – {len(unique_outputs)} output{'s' if len(unique_outputs) != 1 else ''}"

        with st.expander(header):
            if results:
                # Group by output value
                outputs = defaultdict(list)
                for res in results:
                    outputs[res["output"]].append(res)

                for out_val, sequences in outputs.items():
                    with st.expander(f"🔸 Output {out_val} – {len(sequences)} descending"):
                        for res in sequences:
                            seq = res["sequence"]
                            m_path = " → ".join([f"|{row['M #']}|" for _, row in seq.iterrows()])
                            icons = "".join([feed_icon(row["Feed"]) for _, row in seq.iterrows()])
                            hrs = "-" if pd.isnull(res["timestamp"]) else int((report_time - res["timestamp"]).total_seconds() / 3600)
                            time_str = "Unknown" if pd.isnull(res["timestamp"]) else res["timestamp"].strftime('%Y-%m-%d %H:%M')
                            summary = f"{hrs} hours ago, at {time_str}, {m_path} Cross [{icons}]"
                            st.markdown(summary)
                            st.table(seq.reset_index(drop=True))
            else:
                st.markdown("No outputs matched this model.")

# 🚀 Main App Execution
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")
    required = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
    if not required.issubset(df.columns):
        st.error("Missing required columns: " + ", ".join(required - set(df.columns)))
        st.stop()

    df = df[df["Output"] > 0].copy()
    model_outputs, report_time = detect_A_models(df)
    show_a_model_results(model_outputs, report_time)
else:
    st.info("☝️ Upload a CSV file to begin detection.")
