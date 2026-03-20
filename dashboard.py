import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import time
import os

st.set_page_config(
    page_title="Urban Traffic Optimization Dashboard",
    layout="wide",
    page_icon="🚦"
)

st.title("Real-Time Traffic Flow Optimization")
st.markdown("Genetic Algorithm optimizing **3 coordinated intersections** — J1, J2, J3")


def load_ga():
    if os.path.exists("ga_history.csv"):
        try:
            return pd.read_csv("ga_history.csv")
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def load_comparison():
    if os.path.exists("comparison_results.csv"):
        try:
            return pd.read_csv("comparison_results.csv")
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


# ── Tabs ──────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🧬 GA Optimization Progress", "📊 Baseline vs GA Comparison"])


# ══════════════════════════════════════════════════════════════════════
# TAB 1 — GA live progress
# ══════════════════════════════════════════════════════════════════════
with tab1:
    df = load_ga()

    if not df.empty:
        latest = df.iloc[-1]
        first  = df.iloc[0]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Generation", int(latest["generation"]))
        k2.metric(
            "Avg Wait Time (s)",
            f"{latest['avg_waiting_time']:.1f}",
            delta=f"{latest['avg_waiting_time'] - first['avg_waiting_time']:.1f} s",
            delta_color="inverse",
        )
        k3.metric(
            "Throughput (cars)",
            int(latest["throughput"]),
            delta=int(latest["throughput"] - first["throughput"]),
        )
        k4.metric("Best Fitness", f"{latest['fitness']:.2f}")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            fig_wait = px.line(
                df, x="generation", y="avg_waiting_time",
                title="📉 Avg Wait Time per Generation (lower = better)",
                markers=True, template="plotly_dark",
            )
            fig_wait.update_traces(line_color="#FF4B4B")
            st.plotly_chart(fig_wait, use_container_width=True)

        with col2:
            fig_fit = px.line(
                df, x="generation", y="fitness",
                title="📈 Fitness Score per Generation (higher = better)",
                markers=True, template="plotly_dark",
            )
            fig_fit.update_traces(line_color="#00CC96")
            st.plotly_chart(fig_fit, use_container_width=True)

        st.subheader("⏱️ Traffic Light Phase Evolution (All 3 Intersections)")
        c1, c2, c3 = st.columns(3)
        for col, jid, ga_col, gb_col in [
            (c1, "J1", "green_J1_A", "green_J1_B"),
            (c2, "J2", "green_J2_A", "green_J2_B"),
            (c3, "J3", "green_J3_A", "green_J3_B"),
        ]:
            if ga_col in df.columns:
                fig = px.line(
                    df, x="generation", y=[ga_col, gb_col],
                    title=f"{jid} — Green Phase Durations",
                    markers=True, template="plotly_dark",
                    labels={"value": "Duration (s)", "variable": "Phase"},
                )
                col.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⏳ Waiting for GA data... Run pygad_optimizer.py to start.")


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — Baseline vs GA comparison
# ══════════════════════════════════════════════════════════════════════
with tab2:
    cdf = load_comparison()

    if cdf.empty:
        st.info("⏳ No comparison data yet. Run baseline.py to generate it.")
    else:
        baseline = cdf[cdf["condition"] == "Baseline"]
        ga       = cdf[cdf["condition"] == "GA_Optimized"]

        # ── KPIs ──────────────────────────────────────────────────────
        st.subheader("Summary")
        k1, k2, k3, k4 = st.columns(4)

        baseline_mean_wait = baseline["avg_wait"].mean()
        ga_mean_wait       = ga["avg_wait"].mean()
        pct_reduction      = (baseline_mean_wait - ga_mean_wait) / baseline_mean_wait * 100

        k1.metric("Baseline Avg Wait",   f"{baseline_mean_wait:.1f}s")
        k2.metric("GA Avg Wait",         f"{ga_mean_wait:.1f}s")
        k3.metric("Wait Time Reduction", f"{pct_reduction:.1f}%")
        k4.metric(
            "Throughput Increase",
            f"+{ga['throughput'].mean() - baseline['throughput'].mean():.0f} cars",
        )

        st.divider()

        # ── Statistical significance ───────────────────────────────────
        t_stat, p_value = stats.ttest_ind(
            baseline["avg_wait"].values,
            ga["avg_wait"].values,
            equal_var=False
        )

        st.subheader("Statistical Significance (Welch's t-test)")
        sig_col1, sig_col2, sig_col3 = st.columns(3)
        sig_col1.metric("t-statistic", f"{t_stat:.2f}")
        sig_col2.metric("p-value",     f"{p_value:.6f}")
        sig_col3.metric(
            "Result",
            "✅ Significant" if p_value < 0.05 else "❌ Not Significant",
        )

        st.divider()

        # ── Charts ────────────────────────────────────────────────────
        chart1, chart2 = st.columns(2)

        with chart1:
            fig_box = px.box(
                cdf, x="condition", y="avg_wait",
                color="condition",
                title="🕐 Wait Time Distribution: Baseline vs GA (10 runs each)",
                template="plotly_dark",
                labels={"avg_wait": "Avg Wait Time (s)", "condition": ""},
                color_discrete_map={
                    "Baseline":     "#FF4B4B",
                    "GA_Optimized": "#00CC96",
                },
            )
            st.plotly_chart(fig_box, use_container_width=True)

        with chart2:
            fig_thru = px.box(
                cdf, x="condition", y="throughput",
                color="condition",
                title="🚗 Throughput Distribution: Baseline vs GA (10 runs each)",
                template="plotly_dark",
                labels={"throughput": "Cars Arrived", "condition": ""},
                color_discrete_map={
                    "Baseline":     "#FF4B4B",
                    "GA_Optimized": "#00CC96",
                },
            )
            st.plotly_chart(fig_thru, use_container_width=True)

        # ── Run-by-run table ──────────────────────────────────────────
        st.subheader("Run-by-Run Results")
        display = cdf[["condition", "run", "avg_wait", "throughput", "fitness"]].copy()
        display.columns = ["Condition", "Run", "Avg Wait (s)", "Throughput", "Fitness"]
        display["Avg Wait (s)"] = display["Avg Wait (s)"].round(2)
        display["Fitness"]      = display["Fitness"].round(2)
        st.dataframe(display, use_container_width=True, hide_index=True)