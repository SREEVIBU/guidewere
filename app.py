import streamlit as st
import pandas as pd
import numpy as np


# --- 1. GENERATE MOCK DATA ---
@st.cache_data
def generate_data():
    np.random.seed(42)
    data = {
        "Worker_ID": np.random.randint(100, 110, 500),
        "Historical_Login_Prob": np.random.uniform(0.2, 0.9, 500),
        "Temp_C": np.random.randint(30, 48, 500),
        "Rain_mm": np.random.randint(0, 60, 500),
        "AQI": np.random.randint(100, 500, 500),
    }
    df = pd.DataFrame(data)

    # Workers are less likely to login if weather is bad or their historical probability is low.
    df["Did_Login"] = np.where(
        (df["Historical_Login_Prob"] > 0.5)
        & (df["Temp_C"] < 43)
        & (df["Rain_mm"] < 40),
        1,
        0,
    )

    # Add randomness to mimic real behavior.
    df["Did_Login"] = np.where(np.random.rand(500) > 0.8, 1 - df["Did_Login"], df["Did_Login"])
    return df


# --- 2. LIGHTWEIGHT AI SCORE (FRAUD / INTENT FILTER) ---
def score_intent_probability(hist_prob, temp, rain, aqi):
    # Weighted heuristic that approximates likelihood of genuine work intent.
    score = (
        0.60 * hist_prob
        + 0.20 * max(0, (45 - temp) / 15)
        + 0.12 * max(0, (60 - rain) / 60)
        + 0.08 * max(0, (500 - aqi) / 500)
    )
    return float(np.clip(score, 0.0, 1.0))


# --- 3. PARAMETRIC ENGINE (RULES) ---
def check_parametric_triggers(temp, rain, aqi):
    payout = 0
    reasons = []

    if temp >= 44:
        payout += 300
        reasons.append("Extreme Heat (>44 C)")
    if rain >= 40:
        payout += 200
        reasons.append("Heavy Rainfall (>40 mm)")
    if aqi >= 400:
        payout += 250
        reasons.append("Severe Air Pollution (>400 AQI)")

    return payout, reasons


# --- 4. WEEKLY PRICING ENGINE ---
def build_weekly_plan(weekly_income):
    # Weekly premium is kept simple and tied to earnings cycle.
    weekly_premium = max(49, int(round(weekly_income * 0.02)))
    max_weekly_cover = int(round(weekly_income * 0.30))
    return weekly_premium, max_weekly_cover


# --- 5. STREAMLIT WEB APP UI ---
st.set_page_config(page_title="GigGuard: Parametric Insurance", layout="wide")
st.title("GigGuard: AI-Enabled Income Protection")
st.write(
    "This dashboard simulates a parametric income-protection platform for delivery partners "
    "on Zomato, Swiggy, Zepto, Amazon, Dunzo, and similar networks."
)

st.subheader("The Problem We Are Solving")
st.markdown(
    """
India's platform-based delivery partners are the backbone of the digital economy.
External disruptions such as extreme weather, pollution, and natural disasters can reduce
their working hours and cut 20-30% of monthly earnings. Today, most gig workers have no
income protection against these uncontrollable events and bear the full financial loss.
"""
)

# Load data.
df = generate_data()

# Sidebar inputs.
st.sidebar.header("Weekly Plan and Event Simulation")
selected_worker = st.sidebar.selectbox("Select Worker ID", sorted(df["Worker_ID"].unique()))
weekly_income = st.sidebar.slider("Typical Weekly Earnings (INR)", 3000, 12000, 6000, step=500)
weekly_premium, weekly_cover_limit = build_weekly_plan(weekly_income)
coverage_active = st.sidebar.checkbox("Weekly Premium Paid (Coverage Active)", value=True)
st.sidebar.info(
    f"Weekly premium: INR {weekly_premium} | Max weekly protection: INR {weekly_cover_limit}"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Today's External Conditions")
today_temp = st.sidebar.slider("Temperature (C)", 30, 50, 35)
today_rain = st.sidebar.slider("Rainfall (mm)", 0, 100, 0)
today_aqi = st.sidebar.slider("AQI Level", 50, 500, 150)

worker_hist_prob = df[df["Worker_ID"] == selected_worker]["Historical_Login_Prob"].mean()
st.sidebar.info(f"Worker {selected_worker} historical attendance rate: {worker_hist_prob * 100:.1f}%")

st.divider()
col0, col1, col2 = st.columns(3)

with col0:
    st.subheader("1. Weekly Micro-Cover")
    if coverage_active:
        st.success("Policy is active for this week.")
        st.metric("Weekly Premium", f"INR {weekly_premium}")
        st.metric("Max Weekly Cover", f"INR {weekly_cover_limit}")
    else:
        st.warning("Coverage inactive. No payout can be released this week.")

with col1:
    st.subheader("2. Parametric Trigger Engine")
    raw_payout_amount, triggers = check_parametric_triggers(today_temp, today_rain, today_aqi)
    payout_amount = min(raw_payout_amount, weekly_cover_limit)

    if raw_payout_amount > 0:
        st.error(f"Extreme Weather Detected: {', '.join(triggers)}")
        st.write(f"**Triggered Payout (Before Cover Limit):** INR {raw_payout_amount}")
        st.write(f"**Eligible Payout (After Weekly Limit):** INR {payout_amount}")
    else:
        st.success("Weather is normal. No parametric triggers activated.")

with col2:
    st.subheader("3. AI Fraud and Auto Settlement")

    if not coverage_active:
        st.info("Coverage is inactive. Claims are skipped until weekly premium is paid.")
    elif payout_amount > 0:
        intent_prob = score_intent_probability(worker_hist_prob, today_temp, today_rain, today_aqi)
        fraud_risk = 1 - intent_prob
        st.metric("AI Intent Probability", f"{intent_prob * 100:.1f}%")
        st.metric("Fraud Risk Score", f"{fraud_risk * 100:.1f}%")

        if intent_prob >= 0.60:
            st.success(
                "**Claim Approved:** AI verifies this worker has a genuine history of working similar shifts. "
                "Payout processed automatically via UPI."
            )
            st.metric(label="Funds Transferred", value=f"INR {payout_amount}")
        elif intent_prob >= 0.45:
            st.warning(
                "**Claim Under Review:** Medium confidence intent. A lightweight manual verification is required."
            )
        else:
            st.warning(
                "**Claim Flagged:** AI detects low probability of intent to work based on historical login "
                "patterns. Payout placed on manual hold."
            )
    else:
        st.write("Waiting for a weather trigger to evaluate claims...")

st.divider()
st.subheader("How to Pitch This")
st.markdown(
    """
- **Who this is for:** Platform delivery partners (Zomato, Swiggy, Zepto, Amazon, Dunzo, etc.).
- **Core pain:** Uncontrollable disruptions can erase 20-30% of monthly income with no safety net.
- **Weekly model:** Worker pays a simple weekly premium aligned with gig earning cycles.
- **Parametric protection:** Objective disruption thresholds auto-trigger payout eligibility.
- **Trust and speed:** AI intent scoring enables instant payouts for low-risk claims and review for risky ones.
"""
)
