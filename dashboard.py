import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import os
from datetime import datetime

st.set_page_config(
    page_title="Urban Traffic Optimizer",
    layout="wide",
    page_icon="🚦",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
        background-color: #0a0a0f;
        color: #e2e8f0;
    }
    .main { background-color: #0a0a0f; }
    .block-container { padding: 1.5rem 2rem; max-width: 1600px; }
    h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }

    .stMetric {
        background: linear-gradient(135deg, #0f0f1a 0%, #151528 100%);
        border: 1px solid #1e1e3f;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        transition: border-color 0.3s;
    }
    .stMetric:hover { border-color: #4f46e5; }
    .stMetric label {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.7rem !important;
        color: #6b7280 !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }
    .stMetric [data-testid="metric-container"] > div:nth-child(2) {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #f0f4ff !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #0f0f1a;
        border-bottom: 1px solid #1e1e3f;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
        padding: 0.75rem 1.5rem;
        border-bottom: 2px solid transparent;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .stTabs [aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom: 2px solid #818cf8 !important;
        background: transparent !important;
    }
    hr { border-color: #1e1e3f; }
    .network-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .badge-20 { background: #1e1b4b; color: #818cf8; border: 1px solid #3730a3; }
    .badge-3  { background: #052e16; color: #4ade80; border: 1px solid #166534; }
    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.5rem;
    }
    .timer-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        color: #818cf8;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────
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

def detect_network(df):
    if df.empty:
        return None, []
    gene_cols_a = [c for c in df.columns if c.endswith("_A")]
    return len(gene_cols_a), gene_cols_a

def get_tl_ids(gene_cols_a):
    return [c.replace("green_", "").replace("_A", "") for c in gene_cols_a]

DARK_BG   = "#0a0a0f"
GRID_COL  = "#111122"
FONT_MONO = "JetBrains Mono"
FONT_SANS = "Syne"

def base_layout(title_text, xtitle="", ytitle=""):
    return dict(
        plot_bgcolor=DARK_BG, paper_bgcolor=DARK_BG,
        font=dict(family=FONT_MONO, size=11, color="#9ca3af"),
        title=dict(text=title_text, font=dict(family=FONT_SANS, size=13, color="#e2e8f0")),
        xaxis=dict(gridcolor=GRID_COL, title=xtitle),
        yaxis=dict(gridcolor=GRID_COL, title=ytitle),
    )

def add_glow(fig, x, y, rgb, widths=((28,0.04),(18,0.08),(10,0.18),(5,0.4))):
    """Add neon glow layers then a white hot core."""
    for width, opacity in widths:
        fig.add_trace(go.Scatter(
            x=x, y=y,
            line=dict(color=f"rgba({rgb},{opacity})", width=width),
            mode="lines", showlegend=False, hoverinfo="skip"
        ))
    fig.add_trace(go.Scatter(
        x=x, y=y,
        line=dict(color="rgba(255,255,255,0.65)", width=1.2),
        mode="lines", showlegend=False, hoverinfo="skip"
    ))


# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:0.25rem;">
  <span style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
               color:#4b5563;text-transform:uppercase;letter-spacing:0.15em;">
    Urban Traffic Optimizer // PyGAD + SUMO
  </span>
</div>
""", unsafe_allow_html=True)
st.markdown("<h1 style='font-size:2rem;margin:0 0 0.1rem 0;color:#f0f4ff;'>Real-Time Traffic Flow Optimization</h1>",
            unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🧬  GA PROGRESS", "📊  BASELINE vs GA", "⚡  SCALABILITY"])


# ══════════════════════════════════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════════════════════════════════
with tab1:
    df = load_ga()
    n_intersections, gene_cols_a = detect_network(df)

    top_left, top_right = st.columns([3, 1])
    with top_left:
        if n_intersections:
            badge_class = "badge-20" if n_intersections == 20 else "badge-3"
            st.markdown(
                f'<span class="network-badge {badge_class}">'
                f'🔲 {n_intersections}-Intersection Network &nbsp;·&nbsp; {n_intersections*2} Genes'
                f'</span>', unsafe_allow_html=True)
    with top_right:
        if not df.empty:
            mtime = os.path.getmtime("ga_history.csv")
            elapsed = datetime.now() - datetime.fromtimestamp(mtime)
            mins, secs = int(elapsed.total_seconds()//60), int(elapsed.total_seconds()%60)
            st.markdown(
                f'<div class="section-label">Last generation logged</div>'
                f'<div class="timer-display">{mins:02d}:{secs:02d} ago</div>',
                unsafe_allow_html=True)

    st.divider()

    if not df.empty:
        latest, first = df.iloc[-1], df.iloc[0]

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("Generation", f"{int(latest['generation'])} / {len(df)}")
        k2.metric("Avg Wait Time", f"{latest['avg_waiting_time']:.1f}s",
                  delta=f"{latest['avg_waiting_time']-first['avg_waiting_time']:.1f}s",
                  delta_color="inverse")
        k3.metric("Throughput", f"{int(latest['throughput'])} cars",
                  delta=f"+{int(latest['throughput']-first['throughput'])}")
        k4.metric("Best Fitness", f"{latest['fitness']:.2f}")
        k5.metric("Improvement",
                  f"{abs((latest['avg_waiting_time']-first['avg_waiting_time'])/first['avg_waiting_time']*100):.1f}%",
                  delta="wait time reduction", delta_color="inverse")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            fig_wait = px.line(df, x="generation", y="avg_waiting_time",
                               title="Avg Wait Time per Generation", markers=True)
            fig_wait.update_traces(
                line_color="#ff6b6b", line_width=3,
                marker=dict(size=8, color="#ff6b6b", line=dict(width=2, color=DARK_BG)))
            fig_wait.update_layout(**base_layout("Avg Wait Time per Generation",
                                                  xtitle="Generation", ytitle="Seconds"))
            add_glow(fig_wait, df["generation"], df["avg_waiting_time"], "255,107,107")
            st.plotly_chart(fig_wait, use_container_width=True)

        with col2:
            fig_fit = px.line(df, x="generation", y="fitness",
                              title="Fitness Score per Generation", markers=True)
            fig_fit.update_traces(
                line_color="#00ff99", line_width=3,
                marker=dict(size=8, color="#00ff99", line=dict(width=2, color=DARK_BG)))
            fig_fit.update_layout(**base_layout("Fitness Score per Generation",
                                                 xtitle="Generation", ytitle="Fitness"))
            add_glow(fig_fit, df["generation"], df["fitness"], "0,255,153")
            st.plotly_chart(fig_fit, use_container_width=True)

        # Gene evolution grid
        if gene_cols_a:
            st.markdown('<div class="section-label">Traffic Light Phase Evolution — All Intersections</div>',
                        unsafe_allow_html=True)
            tl_ids = get_tl_ids(gene_cols_a)
            colors = ["#818cf8","#f472b6","#34d399","#fb923c",
                      "#60a5fa","#a78bfa","#4ade80","#fbbf24"]
            rows = [tl_ids[i:i+4] for i in range(0, len(tl_ids), 4)]

            for row_tls in rows:
                cols = st.columns(len(row_tls))
                for col, tl_id in zip(cols, row_tls):
                    ga_col = f"green_{tl_id}_A"
                    gb_col = f"green_{tl_id}_B"
                    if ga_col in df.columns:
                        idx   = tl_ids.index(tl_id)
                        ca    = colors[idx % len(colors)]
                        cb    = colors[(idx+3) % len(colors)]
                        fig   = go.Figure()
                        fig.add_trace(go.Scatter(x=df["generation"], y=df[ga_col],
                            name="A", line=dict(color=ca, width=2), marker=dict(size=4)))
                        fig.add_trace(go.Scatter(x=df["generation"], y=df[gb_col],
                            name="B", line=dict(color=cb, width=2, dash="dot"), marker=dict(size=4)))
                        fig.update_layout(
                            title=dict(text=tl_id.replace("_"," "),
                                       font=dict(family=FONT_MONO, size=10, color="#9ca3af")),
                            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                            font=dict(family=FONT_MONO, size=9, color="#6b7280"),
                            xaxis=dict(gridcolor=GRID_COL, showticklabels=False),
                            yaxis=dict(gridcolor=GRID_COL, range=[0,90]),
                            legend=dict(font=dict(size=8), bgcolor="rgba(0,0,0,0)"),
                            margin=dict(l=30,r=10,t=30,b=20), height=160)
                        col.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⏳ Waiting for GA data... Run pygad_optimizer.py to start.")


# ══════════════════════════════════════════════════════════════════════
# TAB 2
# ══════════════════════════════════════════════════════════════════════
with tab2:
    cdf = load_comparison()
    if cdf.empty:
        st.info("⏳ No comparison data yet. Run baseline.py after the GA completes.")
    else:
        baseline = cdf[cdf["condition"]=="Baseline"]
        ga_res   = cdf[cdf["condition"]=="GA_Optimized"]

        bmw  = baseline["avg_wait"].mean()
        gmw  = ga_res["avg_wait"].mean()
        pct  = (bmw - gmw) / bmw * 100
        tdel = ga_res["throughput"].mean() - baseline["throughput"].mean()
        t_stat, p_value = stats.ttest_ind(baseline["avg_wait"].values,
                                          ga_res["avg_wait"].values, equal_var=False)

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("Baseline Wait", f"{bmw:.1f}s")
        k2.metric("GA Wait",       f"{gmw:.1f}s")
        k3.metric("Wait Reduction", f"{pct:.1f}%")
        k4.metric("Throughput Gain", f"+{tdel:.0f} cars")
        k5.metric("p-value", f"{p_value:.6f}",
                  delta="✅ Significant" if p_value < 0.05 else "❌ Not significant")

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            fig_box = px.box(cdf, x="condition", y="avg_wait", color="condition",
                             title="Wait Time Distribution (10 runs each)",
                             labels={"avg_wait":"Avg Wait (s)","condition":""},
                             color_discrete_map={"Baseline":"#ff6b6b","GA_Optimized":"#00ff99"})
            fig_box.update_layout(**base_layout("Wait Time Distribution (10 runs each)"),
                                  showlegend=False)
            fig_box.update_traces(marker=dict(line=dict(width=1.5)), line=dict(width=2))
            st.plotly_chart(fig_box, use_container_width=True)

        with col2:
            fig_thru = px.box(cdf, x="condition", y="throughput", color="condition",
                              title="Throughput Distribution (10 runs each)",
                              labels={"throughput":"Cars Arrived","condition":""},
                              color_discrete_map={"Baseline":"#ff6b6b","GA_Optimized":"#00ff99"})
            fig_thru.update_layout(**base_layout("Throughput Distribution (10 runs each)"),
                                   showlegend=False)
            fig_thru.update_traces(marker=dict(line=dict(width=1.5)), line=dict(width=2))
            st.plotly_chart(fig_thru, use_container_width=True)

        st.subheader("Run-by-Run Results")
        display = cdf[["condition","run","avg_wait","throughput","fitness"]].copy()
        display.columns = ["Condition","Run","Avg Wait (s)","Throughput","Fitness"]
        display["Avg Wait (s)"] = display["Avg Wait (s)"].round(2)
        display["Fitness"]      = display["Fitness"].round(2)
        st.dataframe(display, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 3
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<h3 style='color:#f0f4ff;'>Parallel vs Sequential Speedup</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6b7280;font-family:JetBrains Mono;font-size:0.8rem;'>"
        "Theoretical speedup of parallel evaluation (12 workers) vs sequential evaluation across network sizes.</p>",
        unsafe_allow_html=True)

    scale_df = pd.DataFrame({
        "Network":           ["3 Intersections", "20 Intersections"],
        "Intersections":     [3, 20],
        "Genes":             [6, 40],
        "Sequential (min)":  [100, 2400],
        "Parallel (min)":    [20, 300],
    })
    speedups = [s/p for s,p in zip(scale_df["Sequential (min)"], scale_df["Parallel (min)"])]

    col1, col2 = st.columns(2)

    with col1:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Sequential",
            x=scale_df["Network"], y=scale_df["Sequential (min)"],
            marker_color="#ff6b6b", marker_line=dict(width=0), opacity=0.9))
        fig_bar.add_trace(go.Bar(
            name="Parallel (12 cores)",
            x=scale_df["Network"], y=scale_df["Parallel (min)"],
            marker_color="#00ff99", marker_line=dict(width=0), opacity=0.9))
        fig_bar.update_layout(
            **base_layout("Runtime Comparison (minutes, 20 generations)", ytitle="Minutes"),
            barmode="group",
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        fig_speedup = go.Figure(go.Bar(
            x=scale_df["Network"], y=speedups,
            marker_color=["#818cf8","#f472b6"],
            marker_line=dict(width=0), opacity=0.9,
            text=[f"{s:.1f}×" for s in speedups],
            textposition="outside",
            textfont=dict(family=FONT_MONO, size=14, color="#f0f4ff")))
        fig_speedup.update_layout(
            **base_layout("Speedup Factor (Sequential ÷ Parallel)", ytitle="Speedup ×"))
        st.plotly_chart(fig_speedup, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-label">Complexity Analysis</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric("Sequential Complexity", "O(P × G × T)")
    c2.metric("Parallel Complexity",   "O(G × T)")
    c3.metric("Workers",               "12 processes")

    st.markdown("""
    <div style="margin-top:1rem;padding:1rem;background:#0f0f1a;
                border:1px solid #1e1e3f;border-radius:8px;
                font-family:JetBrains Mono;font-size:0.78rem;color:#6b7280;line-height:1.8;">
        <span style="color:#818cf8;font-weight:600;">P</span> = population size &nbsp;·&nbsp;
        <span style="color:#818cf8;font-weight:600;">G</span> = generations &nbsp;·&nbsp;
        <span style="color:#818cf8;font-weight:600;">T</span> = simulation time per evaluation<br>
        Parallel evaluation eliminates P from the complexity by evaluating all P solutions simultaneously.<br>
        With 12 workers and P=12, each generation completes in the time of a single simulation.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Network Scaling</div>',
                unsafe_allow_html=True)
    sd = scale_df[["Network","Intersections","Genes","Sequential (min)","Parallel (min)"]].copy()
    sd.columns = ["Network","Intersections","Chromosome Size","Sequential (min)","Parallel (min)"]
    st.dataframe(sd, use_container_width=True, hide_index=True)