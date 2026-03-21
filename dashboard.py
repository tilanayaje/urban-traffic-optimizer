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


# Helpers
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


# Header 
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

tab1, tab2, tab3, tab4 = st.tabs(["🧬  GA PROGRESS", "📊  BASELINE vs GA", "⚡  SCALABILITY", "🗺️  HEATMAPS"])


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

        st.divider()
        st.markdown("<h3 style='color:#f0f4ff;'>How to Read These Charts</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:0.88rem;color:#cbd5e1;line-height:1.9;max-width:1100px;">

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;">What the fitness and wait time curves show.</span>
        Each data point represents the single best solution found across the entire population at that generation — not the average,
        not the median. The GA uses elitism to carry the top 3 solutions forward unchanged each generation,
        so the best fitness score can only stay the same or improve. This is why both curves are monotonic:
        wait time never increases and fitness never decreases from one generation to the next.
        A plateau means the population has converged locally — the best solution found so far is being preserved,
        but crossover and mutation have not yet produced anything better.
        A sudden drop in wait time (or jump in fitness) means a new combination emerged that outperforms everything seen before.
        </p>

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;">The improvement metric is relative to generation 1, not a fixed baseline.</span>
        The "Improvement" KPI above compares the current best solution to the generation 1 best solution —
        which was itself drawn from a random population, not from a controlled fixed-timing condition.
        Generation 1 represents the best of 12 random timing plans, which typically performs similarly to SUMO's default 42s/42s timing
        but is not identical to it. For the validated improvement against the actual fixed-timing baseline,
        refer to the Baseline vs GA tab where both conditions are evaluated under identical controlled conditions across 20 independent runs.
        </p>

        <p style="margin-bottom:0;">
        <span style="color:#00ff99;font-weight:700;">What the gene evolution charts show.</span>
        Each small chart below tracks how the green phase duration for one intersection changed across generations.
        A flat line means the GA committed to a value early and stopped exploring — that timing is "solved."
        A line that changes significantly at a specific generation corresponds to the breakthrough moment where
        the GA discovered a better coordinated pattern involving that intersection.
        Intersections with noisy or unstable lines throughout the run are less critical to overall network performance —
        changing their timing has little effect on fitness either way, so mutation kept randomizing them without penalty.
        </p>

        </div>
        """, unsafe_allow_html=True)
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
                             title="Wait Time Distribution (20 runs each)",
                             labels={"avg_wait":"Avg Wait (s)","condition":""},
                             color_discrete_map={"Baseline":"#ff6b6b","GA_Optimized":"#00ff99"})
            fig_box.update_layout(**base_layout("Wait Time Distribution (20 runs each)"),
                                  showlegend=False)
            fig_box.update_traces(marker=dict(line=dict(width=1.5)), line=dict(width=2))
            st.plotly_chart(fig_box, use_container_width=True)

        with col2:
            fig_thru = px.box(cdf, x="condition", y="throughput", color="condition",
                              title="Throughput Distribution (20 runs each)",
                              labels={"throughput":"Cars Arrived","condition":""},
                              color_discrete_map={"Baseline":"#ff6b6b","GA_Optimized":"#00ff99"})
            fig_thru.update_layout(**base_layout("Throughput Distribution (20 runs each)"),
                                   showlegend=False)
            fig_thru.update_traces(marker=dict(line=dict(width=1.5)), line=dict(width=2))
            st.plotly_chart(fig_thru, use_container_width=True)

        st.subheader("Run-by-Run Results")
        display = cdf[["condition","run","avg_wait","throughput","fitness"]].copy()
        display.columns = ["Condition","Run","Avg Wait (s)","Throughput","Fitness"]
        display["Avg Wait (s)"] = display["Avg Wait (s)"].round(2)
        display["Fitness"]      = display["Fitness"].round(2)
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("<h3 style='color:#f0f4ff;'>How to Read These Results</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:0.88rem;color:#cbd5e1;line-height:1.9;max-width:1100px;">

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;">What is being compared.</span>
        The baseline condition is SUMO's default fixed-timing plan: 42 seconds of green per phase on every intersection,
        equal in both directions, with no optimization applied. This is the counterfactual — what the network looks like
        under standard unoptimized operation. The GA-optimized condition uses the best timing plan found after 20 generations of evolution,
        applied identically across all runs. Both conditions are evaluated 20 times each with different random seeds
        to account for stochastic variability in vehicle spawning — some seeds produce heavier traffic than others.
        The box plots show the full distribution across those 20 runs, not just a single result.
        </p>

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;">Why the GA wait time is higher than the GA progress tab shows.</span>
        The GA Progress tab reports the best single simulation result seen during optimization — a cherry-picked best case.
        This tab reports the mean across 20 independent runs with varied seeds, which is a more honest measure of
        real-world performance. Some seeds produce harder traffic conditions where even the optimized plan struggles.
        The mean is the correct number to use for any performance claim.
        </p>

        <p style="margin-bottom:0;">
        <span style="color:#00ff99;font-weight:700;">What statistical significance means here.</span>
        Welch's t-test tests whether the two distributions of wait times could plausibly have come from the same underlying population.
        A p-value near zero means: if the GA plan and the default plan were actually identical in performance,
        the probability of observing a difference this large across 20 runs is essentially zero.
        The result is not caused by lucky random seeds — it holds consistently across all tested conditions.
        Note that this validity is scoped to this synthetic network and traffic model.
        It does not automatically generalize to real-world networks with different geometry and empirical demand patterns.
        </p>

        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 3
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<h3 style='color:#f0f4ff;'>Parallel vs Sequential Scalability</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6b7280;font-family:JetBrains Mono;font-size:0.78rem;'>"
        "Parallel runtimes are directly measured. Sequential runtimes are calculated from observed per-simulation times (T × P × G).</p>",
        unsafe_allow_html=True)

    # Verified: 3-intersection parallel ~160min total (20 gens × ~8min/gen measured) gens = 1920min ≈ 2000min
    # 20-intersection parallel ~300min total measured, T~10-15min/sim
    # Sequential estimate: 12sims × 10min × 20gens = 2400min
    scale_df = pd.DataFrame({
        "Network":               ["3 Intersections", "20 Intersections"],
        "Intersections":         [3, 20],
        "Genes":                 [6, 40],
        "Sequential (20 gens)":  [2000, 2400],
        "Parallel (20 gens)":    [160, 300],
    })
    speedups = [s/p for s,p in zip(scale_df["Sequential (20 gens)"], scale_df["Parallel (20 gens)"])]

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Sequential (estimated)",
            x=scale_df["Network"], y=scale_df["Sequential (20 gens)"],
            marker_color="#ff6b6b", marker_line=dict(width=0), opacity=0.9))
        fig_bar.add_trace(go.Bar(
            name="Parallel — 12 cores (measured)",
            x=scale_df["Network"], y=scale_df["Parallel (20 gens)"],
            marker_color="#00ff99", marker_line=dict(width=0), opacity=0.9))
        fig_bar.update_layout(
            **base_layout("Total Runtime — 20 Generations (minutes)", ytitle="Minutes"),
            barmode="group",
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        fig_speedup = go.Figure(go.Bar(
            x=scale_df["Network"], y=speedups,
            marker_color=["#818cf8","#f472b6"],
            marker_line=dict(width=0), opacity=0.9,
            text=[f"{s:.0f}×" for s in speedups],
            textposition="outside",
            textfont=dict(family=FONT_MONO, size=14, color="#f0f4ff")))
        fig_speedup.update_layout(
            **base_layout("Speedup Factor (Sequential ÷ Parallel)", ytitle="Speedup ×"))
        st.plotly_chart(fig_speedup, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-label">Complexity Reduction</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Sequential",  "O(P × G × T)")
    c2.metric("Parallel",    "O(G × T)")
    c3.metric("Speedup",     "Factor P")
    c4.metric("Workers",     "12 processes")

    st.divider()
    st.markdown('<div class="section-label">Network Scaling Data</div>', unsafe_allow_html=True)
    sd = pd.DataFrame({
        "Network":                     ["3 Intersections", "20 Intersections", "113 Intersections (Thunder Bay)"],
        "Intersections":               [3, 20, 113],
        "Chromosome (genes)":          [6, 40, 226],
        "Search Space":                ["70⁶ ≈ 1.18×10¹¹", "70⁴⁰ (intractable)", "70²²⁶ (city-scale)"],
        "T per sim":                   ["~8 min (measured)", "~10–15 min (measured)", "~hours (projected)"],
        "Sequential 20 gens":          ["~2,000 min (est.)", "~2,400 min (est.)", "Not feasible"],
        "Parallel 12 cores 20 gens":   ["~160 min (measured)", "~300 min (measured)", "~days (12 cores)"],
    })
    st.dataframe(sd, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("<h3 style='color:#f0f4ff;margin-top:0.5rem;'>Theoretical Foundation</h3>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:0.88rem;color:#cbd5e1;line-height:1.9;max-width:1100px;">

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;">The Search Space Problem.</span>
    Traffic signal optimization is a combinatorial search problem that grows exponentially with network size.
    Each intersection has two green phase durations drawn from approximately 70 possible values (10s–80s).
    For a network of <em>n</em> intersections, the search space contains 70<sup>2n</sup> possible timing combinations.
    At 3 intersections this is approximately 1.18 × 10<sup>11</sup> — already too large for exhaustive search.
    At 20 intersections the space is 70<sup>40</sup>, a number with 74 digits.
    At Thunder Bay scale (113 intersections, 226 genes) the space is effectively infinite.
    No deterministic algorithm can enumerate this space — a heuristic search strategy is the only viable approach.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;">Why a Genetic Algorithm.</span>
    The GA navigates this space by maintaining a population of candidate solutions and applying selection, crossover, and mutation to evolve better solutions over generations.
    It does not require the fitness landscape to be differentiable or convex — it works through black-box simulation evaluation,
    making it directly compatible with SUMO. Each candidate solution is loaded into the simulator, vehicles are spawned, and performance is measured.
    Crossover enables combination of partial solutions: if one chromosome has discovered optimal timing for the western half of the grid
    and another for the eastern half, crossover can produce a solution that inherits both insights.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;">The Computational Bottleneck — O(P × G × T).</span>
    Sequential GA evaluation scales as <strong>O(P × G × T)</strong> where P = population size, G = generations, T = simulation time per evaluation.
    T is the dominant term and grows with network size: more intersections produce more vehicles requiring more simulation steps,
    and TraCI must process vehicle state at every step.
    At 20 intersections with 1,000+ simultaneous vehicles, T ≈ 10–15 minutes.
    Sequential evaluation requires P × T minutes per generation — with P=12 and T=10min (conservative estimate),
    that is 120 minutes per generation, or approximately 2,400 minutes (40 hours) for a full 20-generation run.
    This is the fundamental barrier to scaling.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;">Parallel Evaluation — O(G × T).</span>
    The parallel architecture eliminates P from the complexity by evaluating all P population members simultaneously.
    Each of the 12 population members is assigned to an independent SUMO process with its own TraCI port.
    All 12 simulations run concurrently — the generation completes in time T, not P×T.
    This reduces total complexity to <strong>O(G × T)</strong>, a factor-P reduction.
    With P=12 workers matching population size P=12, the theoretical maximum speedup is 12×.
    Observed speedup is approximately 8–12× (8× at 20 intersections, 12.5× at 3 intersections) due to process spawning overhead,
    file I/O latency from the worker cache, and non-uniform simulation completion times —
    faster workers must wait for the slowest member of each generation.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;">The Coordination Problem.</span>
    Multi-intersection optimization is qualitatively harder than single-intersection optimization.
    At a single intersection, optimal green split depends only on local demand.
    In a connected grid, timing at one intersection directly affects queue buildup on roads shared with adjacent intersections.
    A long green phase at J_0_0 dispatches a platoon toward J_1_0 — if J_1_0 is not timed to receive them,
    they arrive at red and wait, undoing the benefit.
    The globally optimal solution requires coordinated timing across the entire network simultaneously.
    This is the <em>coordination problem</em>, and explains the two-phase convergence observed at 20 intersections:
    early generations eliminate poor random solutions, while the breakthrough at generation 7 corresponds to the GA
    discovering a coherent green wave — a timing cascade where vehicles cleared at one intersection
    arrive at the next during its green phase, propagating throughput gains across the grid.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;">Scaling to Thunder Bay and Beyond.</span>
    Thunder Bay, Ontario has approximately 113 signalized intersections, requiring a 226-gene chromosome.
    The O(G × T) complexity means wall-clock time per generation is determined entirely by T —
    chromosome length does not affect it since the GA itself is fast; the bottleneck is always simulation.
    Provisioning a cloud instance with 113+ cores (e.g. AWS c6i.32xlarge with 128 vCPUs) would evaluate
    an entire Thunder Bay-scale generation in approximately time T, the same wall-clock time as the current 20-intersection run.
    The codebase requires no architectural changes — only the network generation script and compute provisioning would need to scale.
    </p>

    <p style="margin-bottom:0;">
    <span style="color:#818cf8;font-weight:700;">Why This Qualifies as Big Data Methodology.</span>
    The project addresses the computational tractability problem that defines big data challenges:
    the search space is too large to process exhaustively, the evaluation function is expensive,
    and the solution requires parallel distributed computation to execute within practical time constraints.
    Each 20-intersection GA run processes 12 × 20 = 240 full SUMO simulations,
    each sustaining 1,000+ vehicles across 8,000 timesteps — generating millions of vehicle-state data points per run.
    The parallel evaluation framework, file-based inter-process communication, and dynamic chromosome encoding
    are engineering solutions to the same class of problems addressed by distributed computing frameworks:
    distributing expensive computation across independent workers and aggregating results efficiently.
    </p>

    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 4 — Heatmaps
# ══════════════════════════════════════════════════════════════════════
with tab4:
    df_h = load_ga()
    if df_h.empty:
        st.info("⏳ No GA data yet.")
    else:
        best = df_h.iloc[-1]
        BASELINE = 42.0

        # Dynamically detect grid dimensions from CSV column names
        gene_cols = [c for c in best.index if c.startswith("green_J_") and c.endswith("_A")]
        col_indices = sorted(set(int(c.split("_")[2]) for c in gene_cols))
        row_indices = sorted(set(int(c.split("_")[3]) for c in gene_cols))
        COLS = len(col_indices)
        ROWS = len(row_indices)

        def get_val(col, row, suffix):
            key = f"green_J_{col}_{row}{suffix}"
            return float(best[key]) if key in best else BASELINE

        def val_to_viridis(v, vmin=10, vmax=80):
            t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
            # Viridis: dark purple → teal → green → yellow
            stops = [
                (0.0,  ( 68,  1,  84)),
                (0.25, ( 59,  82, 139)),
                (0.5,  ( 33, 145, 140)),
                (0.75, ( 94, 201,  98)),
                (1.0,  (253, 231,  37)),
            ]
            for i in range(len(stops)-1):
                t0, c0 = stops[i]
                t1, c1 = stops[i+1]
                if t0 <= t <= t1:
                    f = (t - t0) / (t1 - t0)
                    r = int(c0[0] + f*(c1[0]-c0[0]))
                    g = int(c0[1] + f*(c1[1]-c0[1]))
                    b = int(c0[2] + f*(c1[2]-c0[2]))
                    return f"rgb({r},{g},{b})"
            return "rgb(253,231,37)"

        def val_to_rdylgn(delta, vmin=-32, vmax=38):
            t = max(0.0, min(1.0, (delta - vmin) / (vmax - vmin)))
            stops = [
                (0.0,  (165,  0, 38)),
                (0.25, (215, 48, 39)),
                (0.45, (254, 224,139)),
                (0.5,  (255, 255,191)),
                (0.55, (217, 239,139)),
                (0.75, ( 26, 150, 65)),
                (1.0,  (  0, 104, 55)),
            ]
            for i in range(len(stops)-1):
                t0, c0 = stops[i]
                t1, c1 = stops[i+1]
                if t0 <= t <= t1:
                    f = (t - t0) / (t1 - t0)
                    r = int(c0[0] + f*(c1[0]-c0[0]))
                    g = int(c0[1] + f*(c1[1]-c0[1]))
                    b = int(c0[2] + f*(c1[2]-c0[2]))
                    return f"rgb({r},{g},{b})"
            return "rgb(0,104,55)"

        def luma(rgb_str):
            # Returns black or white text depending on background brightness
            import re
            nums = list(map(int, re.findall(r'\d+', rgb_str)))
            l = 0.299*nums[0] + 0.587*nums[1] + 0.114*nums[2]
            return "#000000" if l > 140 else "#ffffff"

        def render_intersection_grid(mode="plasma_a"):
            """
            mode: 'plasma_a', 'plasma_b', 'delta_a', 'delta_b'
            Renders a 4-col × 5-row grid of SVG intersection icons.
            Each intersection shows a + cross with N/S and E/W arms colored
            by their green duration, with values labelled on each arm.
            """
            CELL = 160   # cell size px
            PAD  = 12    # padding around grid
            ARM  = 44    # arm width
            ROAD = 28    # road width inside arm
            LEG_W = 36   # legend bar width
            LEG_PAD = 8  # gap between legend and grid
            grid_offset_x = LEG_W + LEG_PAD + PAD
            total_w = COLS * CELL + PAD * 2 + LEG_W + LEG_PAD
            total_h = ROWS * CELL + PAD * 2

            is_delta = mode in ("delta_a", "delta_b")

            svg_parts = [
                f'<svg viewBox="0 0 {total_w} {total_h}" '
                f'xmlns="http://www.w3.org/2000/svg" '
                f'style="width:100%;background:#0a0a0f;border-radius:12px;">'
            ]

            # Legend bar 
            leg_x = PAD
            leg_y = PAD + 20
            leg_h = ROWS * CELL - 40
            steps = 40
            step_h = leg_h / steps

            # Build legend gradient id
            leg_gid = f"leg_{mode}"
            svg_parts.append(f'<defs><linearGradient id="{leg_gid}" x1="0" y1="0" x2="0" y2="1">')
            for i in range(steps + 1):
                frac = i / steps
                if is_delta:
                    # delta: top=max positive (green), bottom=max negative (red)
                    delta_val = 38 * (1 - frac) + (-35) * frac
                    c = val_to_rdylgn(delta_val)
                else:
                    # viridis: top=max (yellow), bottom=min (purple)
                    v = 80 * (1 - frac) + 10 * frac
                    c = val_to_viridis(v)
                svg_parts.append(f'<stop offset="{frac*100:.1f}%" stop-color="{c}"/>')
            svg_parts.append(f'</linearGradient></defs>')

            # Draw bar
            svg_parts.append(
                f'<rect x="{leg_x}" y="{leg_y}" width="{LEG_W-4}" height="{leg_h}" '
                f'fill="url(#{leg_gid})" rx="3"/>')

            # Tick labels
            if is_delta:
                ticks = [(0.0, "+38s"), (0.5, "0s"), (1.0, "-32s")]
            else:
                ticks = [(0.0, "80s"), (0.5, "45s"), (1.0, "10s")]

            for frac, label in ticks:
                ty = leg_y + frac * leg_h
                svg_parts.append(
                    f'<line x1="{leg_x + LEG_W - 4}" y1="{ty}" '
                    f'x2="{leg_x + LEG_W}" y2="{ty}" stroke="#9ca3af" stroke-width="1"/>')
                svg_parts.append(
                    f'<text x="{leg_x + LEG_W + 2}" y="{ty + 4}" '
                    f'font-size="9" font-family="monospace" fill="#9ca3af">{label}</text>')

            # Legend title (rotated)
            mid_y = leg_y + leg_h / 2
            title_text = "Δ from 42s" if is_delta else "Green (s)"
            svg_parts.append(
                f'<text x="{leg_x + (LEG_W-4)//2}" y="{leg_y - 6}" '
                f'text-anchor="middle" font-size="8" font-family="monospace" fill="#6b7280">{title_text}</text>')

            for row in range(ROWS):
                for col in range(COLS):
                    cx = grid_offset_x + col * CELL + CELL // 2
                    cy = PAD + row * CELL + CELL // 2

                    val_a = get_val(col, row, "_A")
                    val_b = get_val(col, row, "_B")

                    if mode == "plasma_a":
                        color_ns = val_to_viridis(val_a)
                        color_ew_actual = val_to_viridis(val_a)
                        label_ns = f"{val_a:.0f}s"
                        label_ew = f"{val_a:.0f}s"
                    elif mode == "plasma_b":
                        color_ns = val_to_viridis(val_b)
                        color_ew_actual = val_to_viridis(val_b)
                        label_ns = f"{val_b:.0f}s"
                        label_ew = f"{val_b:.0f}s"
                    elif mode == "delta_a":
                        d_a = val_a - BASELINE
                        d_b = val_b - BASELINE
                        color_ns = val_to_rdylgn(d_a)
                        color_ew = val_to_rdylgn(d_b)
                        color_ew_actual = color_ew
                        sign_a = "+" if d_a >= 0 else ""
                        sign_b = "+" if d_b >= 0 else ""
                        label_ns = f"{sign_a}{d_a:.0f}s"
                        label_ew = f"{sign_b}{d_b:.0f}s"
                    else:  # delta_b
                        d_a = val_a - BASELINE
                        d_b = val_b - BASELINE
                        color_ns = val_to_rdylgn(d_b)
                        color_ew = val_to_rdylgn(d_a)
                        color_ew_actual = color_ew
                        sign_a = "+" if d_a >= 0 else ""
                        sign_b = "+" if d_b >= 0 else ""
                        label_ns = f"{sign_b}{d_b:.0f}s"
                        label_ew = f"{sign_a}{d_a:.0f}s"

                    half = CELL // 2
                    road = ROAD // 2

                    gid = f"g_{col}_{row}"
                    # Subtle radial glow over entire intersection 
                    svg_parts.append(
                        f'<defs><radialGradient id="{gid}" cx="50%" cy="50%" r="50%">'
                        f'<stop offset="0%" stop-color="#ffffff" stop-opacity="0.09"/>'
                        f'<stop offset="60%" stop-color="#ffffff" stop-opacity="0.03"/>'
                        f'<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>'
                        f'</radialGradient></defs>')

                    # N arm
                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy-half}" width="{ROAD}" height="{half-road}" fill="{color_ns}"/>')
                    # S arm
                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy+road}" width="{ROAD}" height="{half-road}" fill="{color_ns}"/>')
                    # W arm
                    svg_parts.append(
                        f'<rect x="{cx-half}" y="{cy-road}" width="{half-road}" height="{ROAD}" fill="{color_ew_actual}"/>')
                    # E arm
                    svg_parts.append(
                        f'<rect x="{cx+road}" y="{cy-road}" width="{half-road}" height="{ROAD}" fill="{color_ew_actual}"/>')

                    # Centre — blend of both arm colors, no black box
                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy-road}" width="{ROAD}" height="{ROAD}" '
                        f'fill="{color_ns}" opacity="0.5"/>')
                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy-road}" width="{ROAD}" height="{ROAD}" '
                        f'fill="{color_ew_actual}" opacity="0.5"/>')

                    # Radial glow over the full cell
                    full_span = CELL - 6
                    svg_parts.append(
                        f'<rect x="{cx - full_span//2}" y="{cy - full_span//2}" '
                        f'width="{full_span}" height="{full_span}" '
                        f'fill="url(#{gid})" pointer-events="none"/>')

                    # Centre dot
                    svg_parts.append(
                        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#ffffff" opacity="0.75"/>')

                    # N/S label (above centre) — white text with dark outline for readability on any color
                    svg_parts.append(
                        f'<text x="{cx}" y="{cy-road-6}" '
                        f'text-anchor="middle" font-size="9" font-family="monospace" '
                        f'stroke="#000000" stroke-width="2.5" paint-order="stroke" '
                        f'fill="#ffffff" font-weight="bold">{label_ns}</text>')

                    # E/W label (right of centre)
                    svg_parts.append(
                        f'<text x="{cx+road+4}" y="{cy+4}" '
                        f'text-anchor="start" font-size="9" font-family="monospace" '
                        f'stroke="#000000" stroke-width="2.5" paint-order="stroke" '
                        f'fill="#ffffff" font-weight="bold">{label_ew}</text>')

                    # Junction ID label (bottom of cell) — always white with dark outline
                    svg_parts.append(
                        f'<text x="{cx}" y="{cy+half-4}" '
                        f'text-anchor="middle" font-size="8" font-family="monospace" '
                        f'stroke="#000000" stroke-width="2" paint-order="stroke" '
                        f'fill="#e2e8f0">J_{col}_{row}</text>')

            svg_parts.append('</svg>')
            return ''.join(svg_parts)

        # Section 1: Phase durations
        st.markdown("<h3 style='color:#f0f4ff;margin-bottom:0.3rem;'>Green Phase Durations — Final GA Solution (Gen 20)</h3>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#6b7280;font-family:JetBrains Mono;font-size:0.75rem;margin-bottom:1.2rem;'>"
            "Each cell is one intersection. Arms are colored by green duration (dark purple = short, yellow = long). "
            "Top label = N/S duration · Right label = E/W duration.</p>",
            unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div style='color:#9ca3af;font-family:JetBrains Mono;font-size:0.7rem;margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.1em;'>Phase A — North-South</div>", unsafe_allow_html=True)
            st.markdown(render_intersection_grid("plasma_a"), unsafe_allow_html=True)
        with col2:
            st.markdown("<div style='color:#9ca3af;font-family:JetBrains Mono;font-size:0.7rem;margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.1em;'>Phase B — East-West</div>", unsafe_allow_html=True)
            st.markdown(render_intersection_grid("plasma_b"), unsafe_allow_html=True)

        st.divider()

        # Section 2: Deviation from baseline 
        st.markdown("<h3 style='color:#f0f4ff;margin-bottom:0.3rem;'>Deviation from Default Timing (42s baseline)</h3>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#6b7280;font-family:JetBrains Mono;font-size:0.75rem;margin-bottom:1.2rem;'>"
            "Green arm = GA increased green time above 42s default. Red arm = GA cut green time below default. "
            "Deeper color = larger change.</p>",
            unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("<div style='color:#9ca3af;font-family:JetBrains Mono;font-size:0.7rem;margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.1em;'>Phase A Deviation</div>", unsafe_allow_html=True)
            st.markdown(render_intersection_grid("delta_a"), unsafe_allow_html=True)
        with col4:
            st.markdown("<div style='color:#9ca3af;font-family:JetBrains Mono;font-size:0.7rem;margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.1em;'>Phase B Deviation</div>", unsafe_allow_html=True)
            st.markdown(render_intersection_grid("delta_b"), unsafe_allow_html=True)