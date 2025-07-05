import streamlit as st
import pandas as pd
from datetime import datetime

# 📤 Upload CSV
st.title("🌀 Position Model Explorer")
uploaded_file = st.file_uploader("Upload your traveler CSV. cP v 06. placeholder for Pos B", type="csv")

# ✅ Shared Utilities
def feed_icon(feed): return "👶" if "sm" in feed else "🧔"

def label_polarity(seq):
    feeds = seq["Feed"].tolist()
    sm = any("sm" in f for f in feeds)
    bg = any("Bg" in f for f in feeds)
    if sm and bg: return "Mixed Feed"
    elif sm: return "sm-only"
    elif bg: return "Bg-only"
    return "Unknown"

def cluster_by_arrival_gap(df, max_hours=4):
    df = df.sort_values("Arrival").reset_index(drop=True)
    clusters = []
    group = [df.iloc[0]]
    for i in range(1, len(df)):
        gap = (df.iloc[i]["Arrival"] - df.iloc[i-1]["Arrival"]).total_seconds() / 3600
        if gap <= max_hours:
            group.append(df.iloc[i])
        else:
            clusters.append(pd.DataFrame(group))
            group = [df.iloc[i]]
    clusters.append(pd.DataFrame(group))
    return clusters

# 🧭 Output Quadrant Breakdown
def show_quadrants(df):
    st.markdown("### 📊 Output Quadrant Breakdown")
    quadrants = {
        "Q1 – High Positive": df[df["Output"] > 50000],
        "Q2 – Mid Positive": df[(df["Output"] > 0) & (df["Output"] <= 50000)],
        "Q3 – Mid Negative": df[(df["Output"] < 0) & (df["Output"] >= -50000)],
        "Q4 – High Negative": df[df["Output"] < -50000],
    }
    for q, subset in quadrants.items():
        st.write(f"{q}: {subset.shape[0]} travelers")

# 🧠 Flexible Descent to Zero
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

# 🔍 A Model Classification
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
    prior_has_strong = bool(prior & epic) or bool(prior & anchor)
    if is_epic and time == "open": return "A01", "Open Epic 0"
    if is_anchor and time == "open": return "A02", "Open Anchor 0"
    if not is_anchor and time == "open" and prior_has_strong: return "A03", "Open non-Anchor 0"
    if not is_anchor and time == "early" and prior_has_strong: return "A04", "Early non-Anchor 0"
    if is_anchor and time == "late": return "A05", "Late Anchor 0"
    if not is_anchor and time == "late" and prior_has_strong: return "A06", "Late non-Anchor 0"
    if not is_anchor and time == "open" and not prior_has_strong: return "A07", "Open general 0"
    if not is_anchor and time == "early" and not prior_has_strong: return "A08", "Early general 0"
    if not is_anchor and time == "late" and not prior_has_strong: return "A09", "Late general 0"
    return None, None

# 📍 A Model Detection & Display
def show_a_models(df):
    report_time = df["Arrival"].max()
    results = []
    for output in df["Output"].unique():
        subset = df[df["Output"] == output]
        sequences = find_flexible_descents(subset)
        for seq in sequences:
            if seq.shape[0] < 3 or seq.iloc[-1]["M #"] != 0:
                continue
            prior = seq.iloc[:-1]
            last = seq.iloc[-1]
            model, label = classify_A_model(last, prior)
            if model:
                results.append({
                    "model": model,
                    "label": label,
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })

    labels = {
        "A01": "Open Epic 0", "A02": "Open Anchor 0", "A03": "Open non-Anchor 0",
        "A04": "Early non-Anchor 0", "A05": "Late Anchor 0", "A06": "Late non-Anchor 0",
        "A07": "Open general 0", "A08": "Early general 0", "A09": "Late general 0"
    }

    st.subheader("🔍 A Model Results")
    for code, label in labels.items():
        matches = [r for r in results if r["model"] == code]
        header = f"{code}. 2+ to {label} – {len(matches)} result{'s' if len(matches) != 1 else ''}"
        with st.expander(header):
            if matches:
                for res in matches:
                    t = res["timestamp"]
                    hrs = "-" if pd.isnull(t) else int((report_time - t).total_seconds() / 3600)
                    time_str = "Unknown" if pd.isnull(t) else t.strftime('%Y-%m-%d %H:%M')
                    m_path = " → ".join([f"|{row['M #']}|" for _, row in res["sequence"].iterrows()])
                    icons = "".join([feed_icon(row["Feed"]) for _, row in res["sequence"].iterrows()])
                    polarity = label_polarity(res["sequence"])
                    summary = f"{hrs} hours ago, at {time_str}, at {res['output']}, {m_path} Cross [{icons}] – {polarity}"
                    st.markdown(summary)
                    st.table(res["sequence"])
            else:
                st.markdown("No matching sequences found.")

# 🧪 B Model Placeholder Logic
def show_b_models(df):
    st.subheader("🚧 B Models – Polarity-Based Detection (Coming Soon)")
    st.markdown("This section will detect traveler confluence based on polarity coherence, quadrant significance, and origin balancing.")
    show_quadrants(df)
    clustered = cluster_by_arrival_gap(df)
    st.markdown(f"{len(clustered)} clustered packs detected with ≤ 4 hour gaps between arrivals.")

# 🎬 Load CSV and Show Explorer
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")
    required = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
    if not required.issubset(df.columns):
        st.error("Missing columns: " + ", ".join(required - set(df.columns)))
        st.stop()
    df = df[df["Output"] > 0].copy()
    show_quadrants(df)

    model_choice = st.selectbox("📡 Choose Model Family", ["A Models", "B Models"])
    if model_choice == "A Models":
        show_a_models(df)
    elif model_choice == "B Models":
        show_b_models(df)
else:
    st.info("☝️ Upload a CSV file to begin model analysis.")
