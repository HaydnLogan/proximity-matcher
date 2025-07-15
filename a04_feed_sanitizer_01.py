import pandas as pd

# 🧼 feed_sanitizer.py – Core Module (Version 1)

def sanitize_feed(df):
    # 🧹 Normalize column headers
    df.columns = df.columns.str.strip().str.lower()

    # ⏱️ Parse datetime if present
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    # 🔢 Force numeric fields
    numeric_fields = ["open", "output", "m #", "input"]
    for col in numeric_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def validate_feed(df):
    issues = []

    # Check key columns
    for col in ["m #", "output", "arrival"]:
        if col not in df.columns:
            issues.append(f"❌ Missing column: {col}")
        elif df[col].isnull().any():
            issues.append(f"⚠️ Nulls found in column '{col}'")

    # Check for string-looking numerics
    sample = df.select_dtypes(include="object").head()
    for col in sample.columns:
        if sample[col].apply(lambda x: isinstance(x, str) and x.replace(".", "").isdigit()).any():
            issues.append(f"🧪 Column '{col}' may store numbers as strings")

    return issues
