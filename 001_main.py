import streamlit as st
import pandas as pd
import datetime as dt
from dateutil import parser
from a002_processor import run_feed_processor, clean_timestamp, get_most_recent_time
from a003_models import run_a_model_detection


# 🔌 Streamlit interface (UI + orchestration)

st.set_page_config(layout="wide")
st.title("🧬 Data Feed Processor + A Model Scanner")

# --- File Uploads ---
small_feed_file = st.file_uploader("Upload small feed", type="csv")
big_feed_file = st.file_uploader("Upload big feed", type="csv")
measurement_file = st.file_uploader("Upload measurement file", type=["xlsx", "xls"])

# --- Report Time Selection ---
report_mode = st.radio("Select Report Time & Date", ["Most Current", "Choose a time"], key="report_mode_radio")
if report_mode == "Choose a time":
    selected_date = st.date_input("Select Report Date", value=dt.date.today(), key="report_date_picker")
    selected_time = st.time_input("Select Report Time", value=dt.time(18, 0), key="report_time_picker")
    report_time = dt.datetime.combine(selected_date, selected_time)
else:
    report_time = None  # to be determined after loading feeds

# --- Day Start and Scope ---
day_start_choice = st.radio("Select Day Start Time", ["17:00", "18:00"])
day_start_hour = int(day_start_choice.split(":" )[0])
scope_type = st.radio("Scope by", ["Rows", "Days"])
scope_value = st.number_input(f"Enter number of {scope_type.lower()}", min_value=1, value=10)

# --- File Check ---
if small_feed_file and big_feed_file and measurement_file:
    small_df = pd.read_csv(small_feed_file)
    big_df = pd.read_csv(big_feed_file)

    small_df.columns = small_df.columns.str.strip().str.lower()
    big_df.columns = big_df.columns.str.strip().str.lower()
    small_df["time"] = small_df["time"].apply(clean_timestamp)
    big_df["time"] = big_df["time"].apply(clean_timestamp)

    xls = pd.ExcelFile(measurement_file)
    available_sheets = xls.sheet_names
    default_sheet = "2a" if "2a" in available_sheets else available_sheets[0]
    sheet_choice = st.selectbox("Select measurement tab", available_sheets, index=available_sheets.index(default_sheet))
    measurements = pd.read_excel(measurement_file, sheet_name=sheet_choice)
    measurements.columns = measurements.columns.str.strip().str.lower()

    # Determine report time if not chosen manually
    if report_mode == "Most Current":
        report_time = max(get_most_recent_time(small_df), get_most_recent_time(big_df))

    st.success(f"✅ Using report time: {report_time.strftime('%d-%b-%y %H:%M')}")

    try:
        final_df = run_feed_processor(
            small_df=small_df,
            big_df=big_df,
            measurements=measurements,
            report_time=report_time,
            scope_type=scope_type,
            scope_value=scope_value,
            start_hour=day_start_hour
        )

        if final_df.empty:
            st.warning("⚠️ No output rows found.")
        else:
            st.success(f"✅ {len(final_df)} results calculated.")
            final_df["Arrival"] = pd.to_datetime(final_df["Arrival"]).dt.strftime("%#d-%b-%y %H:%M")
            st.dataframe(final_df)

            timestamp_str = report_time.strftime("%y-%m-%d_%H-%M")
            filename = f"origin_report_{timestamp_str}.csv"
            csv_bytes = final_df.to_csv(index=False).encode()
            st.download_button("📥 Download Report CSV", data=csv_bytes, file_name=filename, mime="text/csv")

            # ✅ Optional: A Model Detection
            run_a_model = st.checkbox("🔎 Run A Model Detection")
            if run_a_model:
                from a003_models import detect_A_models, show_a_model_results
                final_df["Arrival"] = pd.to_datetime(final_df["Arrival"], errors="coerce")
                model_outputs, rep_time = detect_A_models(final_df)
                show_a_model_results(model_outputs, rep_time)

    except Exception as e:
        st.error(f"❌ Processing error: {e}")
