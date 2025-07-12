import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import datetime as dt

# 📁 File Uploads
st.header("🧬 Data Feed Processor")
small_feed_file = st.file_uploader("Upload small feed", type="csv")
big_feed_file = st.file_uploader("Upload big feed", type="csv")
measurement_file = st.file_uploader("Upload measurement file", type=["xlsx", "xls"])

# 📅 Report & Day Settings
report_mode = st.radio("Select Report Time & Date", ["Most Current", "Choose a time"])
report_time = st.datetime_input("Choose Report Time", value=dt.datetime.now()) if report_mode == "Choose a time" else None
day_start_choice = st.radio("Select Day Start Time", ["17:00", "18:00"])
day_start_hour = int(day_start_choice.split(":")[0])
scope_type = st.radio("Scope by", ["Rows", "Days"])
scope_value = st.number_input(f"Enter number of {scope_type.lower()}", min_value=1, value=10)

# 🧮 Utility Functions
def clean_timestamp(ts):
    return pd.to_datetime(ts.split("-")[0])

def extract_origins(columns):
    origins = {}
    for col in columns:
        col = col.strip().lower()
        if col in ["time", "open"]:
            continue
        if any(suffix in col for suffix in [" h", " l", " c"]):
            # Normalize base name and brackets
            bracket = ""
            if "[" in col and "]" in col:
                bracket = col[col.find("["):col.find("]")+1]
            # Remove trailing H/L/C and assemble group ID
            origin_core = col.replace(" h", "").replace(" l", "").replace(" c", "")
            group_id = origin_core + bracket
            origins.setdefault(group_id, []).append(col)
    # Only keep origins that have exactly 3 columns (H, L, C)
    return {origin: cols for origin, cols in origins.items() if len(cols) == 3}


# def extract_origins(columns):
#     origins = {}
#     for col in columns:
#         col = col.strip().lower()
#         if col in ["time", "open"]:
#             continue
#         if any(suffix in col for suffix in [" h", " l", " c"]):
#             # Example: "wasp-12b h[1]" → origin_key = "wasp-12b[1]"
#             base, *rest = col.split()
#             bracket = ""
#             if "[" in col and "]" in col:
#                 bracket = col[col.find("["):col.find("]")+1]
#             base_origin = " ".join(base.split())  # Handles prefixes like "mercury", "wasp-12b"
#             group_id = base_origin.replace(" h", "").replace(" l", "").replace(" c", "") + bracket
#             origins.setdefault(group_id, []).append(col)
#     return origins

def get_day_index(arrival_time, report_time, start_hour):
    if not report_time: return "[0] Today"
    delta = arrival_time - report_time
    days_diff = (arrival_time - dt.datetime.combine(report_time.date(), dt.time(start_hour))) // dt.timedelta(days=1)
    return f"[{int(days_diff)}]"

# 📊 Pivot Formula
def calculate_pivot(H, L, C, M_value):
    return ((H + L + C) / 3) + M_value * (H - L)

def clean_timestamp(ts):
    return pd.to_datetime(ts.split("-")[0])

def get_most_recent_time(df):
    df["time"] = df["time"].apply(clean_timestamp)
    return df["time"].max()

def get_input_value(df, report_time):
    input_row = df[df["time"] == report_time]
    if not input_row.empty and "open" in input_row.columns:
        return input_row.iloc[0]["open"]
    return None

# 🔍 Establish Report Time if "Most Current" is selected
if report_mode == "Most Current":
    small_df["time"] = small_df["time"].apply(clean_timestamp)
    big_df["time"] = big_df["time"].apply(clean_timestamp)

    most_recent_small = get_most_recent_time(small_df)
    most_recent_big = get_most_recent_time(big_df)

    report_time = max(most_recent_small, most_recent_big)

# 🎯 Grab universal Input value from report row
input_value = get_input_value(small_df, report_time)
if input_value is None:
    input_value = get_input_value(big_df, report_time)


# 🔄 Feed Processor
def process_feed(df, feed_type, report_time, scope_type, scope_value, start_hour, measurements):
    df.columns = df.columns.str.strip().str.lower()
    df["time"] = df["time"].apply(clean_timestamp)
    df = df.iloc[::-1]  # bottom-up
    origins = extract_origins(df.columns)
    new_data_rows = []

    if report_time:
        if scope_type == "Rows":
            start_index = df[df["time"] == report_time].index[0]
            df = df.iloc[start_index:start_index+scope_value]
        else:
            cutoff = report_time - pd.Timedelta(days=scope_value)
            df = df[df["time"] >= cutoff]

    for origin, cols in origins.items():
        relevant_rows = df[["time", "open"] + cols].dropna()
        for i in range(len(relevant_rows)-1):
            current = relevant_rows.iloc[i]
            above = relevant_rows.iloc[i+1]
            changed = any(current[col] != above[col] for col in cols)
            is_special_origin = any(x in origin for x in ["WASP", "Macedonia"])
            if is_special_origin and report_time:
                if current["time"] == report_time:
                    H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                    # input_value = current["open"]
                    for _, row in measurements.iterrows():
                        output = calculate_pivot(H, L, C, row["M value"])
                        day_index = get_day_index(current["time"], report_time, start_hour)
                        new_data_rows.append({
                            "Feed": feed_type,
                            "Arrival": current["time"],
                            "Origin": origin,
                            "M Name": row["M Name"],
                            "M #": row["M #"],
                            "R #": row["R #"],
                            "Tag": row["Tag"],
                            "Family": row["Family"],
                            "Input": input_value,
                            "Output": output,
                            "Diff": output - input_value,
                            "Day": day_index
                        })
            elif not is_special_origin and changed:
                H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                input_value = current["open"]
                for _, row in measurements.iterrows():
                    output = calculate_pivot(H, L, C, row["M value"])
                    day_index = get_day_index(current["time"], report_time, start_hour)
                    new_data_rows.append({
                        "Feed": feed_type,
                        "Arrival": current["time"],
                        "Origin": origin,
                        "M Name": row["M Name"],
                        "M #": row["M #"],
                        "R #": row["R #"],
                        "Tag": row["Tag"],
                        "Family": row["Family"],
                        "Input": input_value,
                        "Output": output,
                        "Diff": output - input_value,
                        "Day": day_index
                    })
    return new_data_rows

# 🧬 Main Runner
if small_feed_file and big_feed_file and measurement_file:
    small_df = pd.read_csv(small_feed_file)
    big_df = pd.read_csv(big_feed_file)
    measure_df = pd.read_excel(measurement_file)
    # Read only the sheet named "2a"
    group_2a = pd.read_excel(measurement_file, sheet_name="2a")
    #group_2a = measure_df[measure_df["Group"] == "2a"]

    results = []
    results += process_feed(small_df, "Sm", report_time, scope_type, scope_value, day_start_hour, group_2a)
    results += process_feed(big_df, "Bg", report_time, scope_type, scope_value, day_start_hour, group_2a)

    final_df = pd.DataFrame(results)
    final_df.sort_values(by=["Output", "Arrival"], ascending=[False, True], inplace=True)

    st.dataframe(final_df)

    # 🎯 Download CSV
    csv_bytes = final_df.to_csv(index=False).encode()
    st.download_button("📥 Download Report CSV", data=csv_bytes, file_name="origin_report.csv", mime="text/csv")
