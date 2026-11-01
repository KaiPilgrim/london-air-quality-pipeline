
import csv
from pathlib import Path
from datetime import datetime
import streamlit as st

DATA = Path(__file__).parent / "data" / "processed"

def load_csv(filename):
    with open(DATA / filename, newline="") as f:
        return list(csv.DictReader(f))

annual = load_csv("annual_no2.csv")
monthly = load_csv("monthly_no2.csv")
comparison = load_csv("ulez_comparison.csv")

for row in annual:
    row["year"] = datetime(int(row["year"]), 1, 1)
    row["average_no2"] = (
        float(row["average_no2"]) if row["average_no2"] else None
    )
    row["completeness_pct"] = float(row["completeness_pct"])

for row in monthly:
    row["month"] = datetime.fromisoformat(row["month"])
    row["average_no2"] = (
        float(row["average_no2"]) if row["average_no2"] else None
    )
    row["completeness_pct"] = float(row["completeness_pct"])

for row in comparison:
    row["percentage_change"] = float(row["percentage_change"])
    row["before_no2"] = float(row["before_no2"])
    row["after_no2"] = float(row["after_no2"])
    row["paired_months"] = int(row["paired_months"])

# Page
st.set_page_config(page_title="London Air Quality Explorer", layout="wide")

st.title("London Air Quality Explorer")
st.write(
    "Explore nitrogen dioxide (NO₂) measurements across "
    "11 London monitoring stations from 2016 to 2025."
    ""
    "Only years with at least 75% recording coverage are "
    "displayed. Some stations have fewer years of available data."
)

st.caption("Concentrations in µg/m³ | Source: London Air Quality Network")

# Station selector
stations = sorted({row["site_code"] for row in annual})
station = st.selectbox("Choose a monitoring station", stations)

st.subheader("Historical NO₂ trend")

annual_station = [
    row for row in annual
    if row["site_code"] == station
    and row["completeness_pct"] >= 75
    and row["average_no2"] is not None
]

st.line_chart(
    annual_station,
    x="year",
    y="average_no2",
    x_label="Year",
    y_label="Average NO₂ (µg/m³)"
)

st.caption("Only years with at least 75% recording coverage are shown.")

st.subheader("Monthly NO₂ trend")

monthly_station = [
    {
        "month": row["month"],
        "average_no2": (
            row["average_no2"]
            if row["completeness_pct"] >= 75
            else None
        )
    }
    for row in monthly
    if row["site_code"] == station
]

st.line_chart(
    monthly_station,
    x="month",
    y="average_no2",
    x_label="Month",
    y_label="Average NO₂ (µg/m³)"
)

# ULEZ comparison
st.divider()
st.subheader("Before and after the 2023 ULEZ expansion")

st.write(
    "Comparing September 2022 - August 2023 with "
    "September 2023 - August 2024."
)

st.bar_chart(
    comparison,
    x="site_code",
    y="percentage_change",
    horizontal=True,
    sort=False,
    x_label="Monitoring station",
    y_label="Change in NO₂ (%)"
)

st.dataframe(comparison, hide_index=True)

st.info(
    "These are observed changes, not estimates of the "
    "causal impact of ULEZ. The analysis requires at least "
    "75% hourly coverage per month and 9 matching calendar "
    "months in each period. Weather, traffic changes and "
    "long term pollution trends may also affect the results."
)
