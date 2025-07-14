import streamlit as st
import pandas as pd
import datetime as dt
from dateutil import parser
from collections import defaultdict

# 🌐 Config
st.set_page_config(layout="wide")
st.title("🔗 Pivot + A Model Processor – v07e")

# 📁 Uploads
small_feed_file = st.file_uploader("Upload small feed", type="csv")
big_feed_file = st.file_uploader("Upload big feed", type="csv")
measurement_file = st.file_uploader("Upload measurement file", type=["xlsx", "xls"])

# 🧠 Sidebar Controls
run_a_model = st.sidebar.checkbox("Run A Model Detection", value=True)

report_mode = st.radio("Select Report Time & Date", ["Most Current", "Choose a time"])
report_time = st.datetime_input("Choose Report Time", value=dt.datetime.now()) if report_mode == "Choose a time" else None
day_start_choice = st.radio("Select Day Start Time", ["17:00", "18:00"])
day_start_hour = int(day_start_choice.split(":")[0])
scope_type = st.radio("Scope by", ["Rows", "Days"])
scope_value = st.number_input(f"Enter number of {scope_type.lower()}", min_value=1, value=10)

# 🔧 Utilities
def clean_timestamp(ts):
    if isinstance(ts, str):
        dt_obj = parser.parse(ts)
        return dt_obj.replace(tzinfo=None)
    return pd.to_datetime(ts, errors="coerce")

def extract_origins(columns):
    origins = {}
    for col in columns:
        col = col.strip().lower()
        if col in ["time", "open"]: continue
        if any(suffix in col for suffix in [" h", " l", " c"]):
            bracket = ""
            if "[" in col and "]" in col:
                bracket = col[col.find("["):col.find("]")+1]
            core = col.replace(" h", "").replace(" l", "").replace(" c", "")
            if bracket and not core.endswith(bracket): core += bracket
            origins.setdefault(core, []).append(col)
    return {origin: cols for origin, cols in origins.items() if len(cols) == 3}

def get_weekly_anchor(report_time, weeks_back, start_hour):
    days_since_sunday = (report_time.weekday() + 1) % 7
    anchor = (report_time - dt.timedelta(days=days_since_sunday + 7 * (weeks_back - 1)))
    return anchor.replace(hour=start_hour, minute=0, second=0, microsecond=0)

def get_monthly_anchor(report_time, months_back, start_hour):
    year, month = report_time.year, report_time.month - (months_back - 1)
    while month <= 0:
        month += 12
        year -= 1
    return dt.datetime(year, month, 1, hour=start_hour)

def get_day_index(arrival, report, start_hour):
    if not report: return "[0] Today"
    start = report.replace(hour=start_hour, minute=0, second=0)
    if report.hour < start_hour: start -= dt.timedelta(days=1)
    return f"[{(arrival - start) // dt.timedelta(days=1)}]"

def calculate_pivot(H, L, C, M_value): return ((H + L + C) / 3) + M_value * (H - L)

def get_most_recent_time(df): return df["time"].max()

def get_input_value(df, report): match = df[df["time"] == report]; return match.iloc[-1]["open"] if not match.empty else None

def process_feed(df, feed_type, report_time, scope_type, scope_value, start_hour, measurements, input_value):
    df.columns = df.columns.str.strip().str.lower()
    df["time"] = df["time"].apply(clean_timestamp)
    df = df.iloc[::-1]
    origins = extract_origins(df.columns)
    rows = []

    if report_time:
        if scope_type == "Rows":
            try:
                start = df[df["time"] == report_time].index[0]
                df = df.iloc[start:start+scope_value]
            except: pass
        else:
            cutoff = report_time - pd.Timedelta(days=scope_value)
            df = df[df["time"] >= cutoff]

    for origin, cols in origins.items():
        relevant = df[["time", "open"] + cols].dropna()
        origin_name = origin.lower()
        is_special = any(tag in origin_name for tag in ["wasp", "macedonia"])

        if is_special:
            report_row = relevant[relevant["time"] == report_time]
            if report_row.empty: continue
            current = report_row.iloc[0]
            bracket = 0
            if "[" in origin_name and "]" in origin_name:
                try: bracket = int(origin_name.split("[")[-1].replace("]", ""))
                except: bracket = 0
            if "wasp" in origin_name:
                arrival = get_weekly_anchor(report_time, max(1, bracket), start_hour)
            elif "macedonia" in origin_name:
                arrival = get_monthly_anchor(report_time, max(1, bracket), start_hour)
            else:
                arrival = report_time

            H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
            for _, row in measurements.iterrows():
                output = calculate_pivot(H, L, C, row["m value"])
                day = get_day_index(arrival, report_time, start_hour)
                rows.append({
                    "Feed": feed_type, "Arrival": arrival, "Origin": origin,
                    "M Name": row["m name"], "M #": row["m #"], "R #": row["r #"],
                    "Tag": row["tag"], "Family": row["family"],
                    "Input": input_value, "Output": output,
                    "Diff": output - input_value, "Day": day
                })
            continue

        for i in range(len(relevant) - 1):
            current = relevant.iloc[i]
            above = relevant.iloc[i + 1]
            changed = any(current[col] != above[col] for col in cols)
            if changed:
                arrival = current["time"]
                if is_special:
                    bracket = 0
                    if "[" in origin_name and "]" in origin_name:
                        try: bracket = int(origin_name.split("[")[-1].replace("]", ""))
                        except: pass
                    if "wasp" in origin_name:
                        arrival = get_weekly_anchor(report_time, max(1, bracket), start_hour)
                    elif "macedonia" in origin_name:
                        arrival = get_monthly_anchor(report_time, max(1, bracket), start_hour)

                H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                for _, row in measurements.iterrows():
                    output = calculate_pivot(H, L, C, row["m value"])
                    day = get_day_index(arrival, report_time, start_hour)
                    rows.append({
                        "Feed": feed_type, "Arrival": arrival, "Origin": origin,
                        "M Name": row["m name"], "M #": row["m #"], "R #": row["r #"],
                        "Tag": row["tag"], "Family": row["family"],
                        "Input": input_value, "Output": output,
                        "Diff": output - input_value, "Day": day
                    })
    return rows

# 🧠 A Model Detection
def find_flexible_descents(df_subset):
    rows = df_subset[df_subset["Output"] > 0].sort_values("Arrival").reset_index(drop=True)
    raw_sequences = []
    for i in range(len(rows)):
        path, seen, last_abs = [], set(), float("inf")
        for j in range(i, len(rows)):
            m = rows.loc[j, "M #"]; abs_m = abs(m)
            if m == 0:
                if len(path) >= 2:
                    path.append(j)
                    raw_sequences.append(rows.loc[path])
                break
            if abs_m in seen or abs_m >= last_abs: continue
            path.append(j)
            seen.add(abs_m)
            last_abs = abs_m

    filtered = []
    all_signatures = [tuple(seq["M #"].tolist()) for seq in raw_sequences]
    for i, sig in enumerate(all_signatures):
        longer = any(set(sig).issubset(set(other)) and len(sig) < len(other) for j, other in enumerate(all_signatures) if i != j)
        if not longer: filtered.append(raw_sequences[i])
    return filtered

def classify_A_model(row_0, prior_rows):
    epic = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
    anchor = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
    t0, o0 = row_0["Arrival"], row_0["Origin"]
    time = "open" if t0.hour == 18 and t0.minute == 0 else "early" if t0.hour > 18 else "late"
