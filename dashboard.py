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

    /* Glassmorphism */
    .stMetric {
        background: rgba(15, 15, 30, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(129, 140, 248, 0.15);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        transition: border-color 0.4s, box-shadow 0.4s, transform 0.2s;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
        animation: cardEntrance 0.5s ease both;
    }
    .stMetric:hover {
        border-color: rgba(129, 140, 248, 0.5);
        box-shadow: 0 4px 32px rgba(129,140,248,0.15), inset 0 1px 0 rgba(255,255,255,0.08);
        transform: translateY(-1px);
    }
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

    /* Staggered card entrance */
    @keyframes cardEntrance {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .stMetric:nth-child(1) { animation-delay: 0.00s; }
    .stMetric:nth-child(2) { animation-delay: 0.08s; }
    .stMetric:nth-child(3) { animation-delay: 0.16s; }
    .stMetric:nth-child(4) { animation-delay: 0.24s; }
    .stMetric:nth-child(5) { animation-delay: 0.32s; }

    /* Tab indicator slide animation */
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
        transition: color 0.25s ease, border-color 0.25s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom: 2px solid #818cf8 !important;
        background: transparent !important;
    }

    /* Smooth scroll for anchor links */
    html { scroll-behavior: smooth; }

    /* Scanlines — injected as real div below */

    /* Glowing section dividers */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(129,140,248,0.15) 20%,
            rgba(129,140,248,0.4) 50%,
            rgba(129,140,248,0.15) 80%,
            transparent 100%
        ) !important;
        box-shadow: 0 0 8px rgba(129,140,248,0.2);
        margin: 1rem 0;
    }
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
    if os.path.exists("for-demo/ga_history.csv"):
        try:
            return pd.read_csv("for-demo/ga_history.csv")
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def load_comparison():
    if os.path.exists("for-demo/comparison_results.csv"):
        try:
            return pd.read_csv("for-demo/comparison_results.csv")
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


# Anchor at absolute top — placed before everything so clicking scrolls to include the title
st.markdown('<div id="top"></div>', unsafe_allow_html=True)

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

# Scanlines overlay
st.markdown("""
<div style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;
            background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.025) 2px,rgba(0,0,0,0.025) 4px);">
</div>
""", unsafe_allow_html=True)


# Scroll to top — anchor link since JS cannot escape Streamlit's iframe sandbox
st.markdown("""
<a href="#top"
  style="position:fixed;bottom:2rem;right:2rem;
         width:110px;height:110px;border-radius:50%;
         background:rgba(15,15,30,0.85);
         border:1px solid rgba(129,140,248,0.35);
         color:#818cf8;font-size:2.5rem;
         z-index:10000;
         backdrop-filter:blur(8px);
         box-shadow:0 0 16px rgba(129,140,248,0.2);
         display:flex;align-items:center;justify-content:center;
         text-decoration:none;
         transition:border-color 0.3s,box-shadow 0.3s,transform 0.2s;"
  onmouseover="this.style.borderColor='rgba(129,140,248,0.7)';this.style.boxShadow='0 0 24px rgba(129,140,248,0.4)';this.style.transform='translateY(-2px)'"
  onmouseout="this.style.borderColor='rgba(129,140,248,0.35)';this.style.boxShadow='0 0 16px rgba(129,140,248,0.2)';this.style.transform='translateY(0)'"
  title="Back to top">↑</a>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🧬  GA PROGRESS", "📊  BASELINE vs GA", "⚡  SCALABILITY", "🗺️  HEATMAPS"])


# ══════════════════════════════════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════════════════════════════════
with tab1:
    df = load_ga()
    n_intersections, gene_cols_a = detect_network(df)

    # YOUR live header fragment — preserved exactly
    @st.fragment(run_every="1s")
    def render_header_section(df, n_intersections):
        top_left, top_right = st.columns([3, 1])

        with top_left:
            if n_intersections:
                badge_class = "badge-20" if n_intersections == 20 else "badge-3"
                st.markdown(
                    f'<span class="network-badge {badge_class}">'
                    f'🔲 {n_intersections}-Intersection Network &nbsp;·&nbsp; {n_intersections*2} Genes'
                    f'</span>', unsafe_allow_html=True)

        with top_right:
            if not df.empty and os.path.exists("for-demo/ga_history.csv"):
                mtime = os.path.getmtime("for-demo/ga_history.csv")
                elapsed = datetime.now() - datetime.fromtimestamp(mtime)
                total_seconds = int(elapsed.total_seconds())
                mins, secs = divmod(total_seconds, 60)
                is_recent = "color: #00ff00; font-weight: bold;" if total_seconds < 5 else ""
                st.markdown(
                    f'<div class="section-label">Last generation logged</div>'
                    f'<div class="timer-display" style="{is_recent}">{mins:02d}:{secs:02d} ago</div>',
                    unsafe_allow_html=True)

    render_header_section(df, n_intersections)

    st.divider()

    if not df.empty:
        latest, first = df.iloc[-1], df.iloc[0]
        max_gens     = 20
        current_gen  = int(latest['generation'])
        wait_val     = latest['avg_waiting_time']
        thru_val     = int(latest['throughput'])
        fit_val      = latest['fitness']
        impr_val     = abs((wait_val - first['avg_waiting_time']) / first['avg_waiting_time'] * 100)
        wait_delta   = wait_val - first['avg_waiting_time']
        thru_delta   = thru_val - int(first['throughput'])

        # UPGRADE 2: Animated KPI counters
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;margin-bottom:1rem;">
          <div class="stMetric" style="animation-delay:0.00s;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem;">Generation</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:#f0f4ff;">{current_gen} / {max_gens}</div>
          </div>
          <div class="stMetric" style="animation-delay:0.08s;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem;">Avg Wait Time</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:#f0f4ff;"><span id="cnt-wait">{wait_val:.1f}</span>s</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#ff6b6b;margin-top:0.2rem;">↓ {abs(wait_delta):.1f}s</div>
          </div>
          <div class="stMetric" style="animation-delay:0.16s;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem;">Throughput</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:#f0f4ff;"><span id="cnt-thru">{thru_val}</span> cars</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#00ff99;margin-top:0.2rem;">↑ +{thru_delta}</div>
          </div>
          <div class="stMetric" style="animation-delay:0.24s;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem;">Best Fitness</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:#f0f4ff;"><span id="cnt-fit">{fit_val:.2f}</span></div>
          </div>
          <div class="stMetric" style="animation-delay:0.32s;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem;">Improvement</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:#f0f4ff;"><span id="cnt-impr">{impr_val:.1f}</span>%</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#ff6b6b;margin-top:0.2rem;">wait time reduction</div>
          </div>
        </div>
        <script>
        function animateCount(id, target, decimals, duration) {{
            const el = document.getElementById(id);
            if (!el) return;
            const startTime = performance.now();
            function update(now) {{
                const progress = Math.min((now - startTime) / duration, 1);
                const ease = 1 - Math.pow(1 - progress, 3);
                el.textContent = (target * ease).toFixed(decimals);
                if (progress < 1) requestAnimationFrame(update);
            }}
            requestAnimationFrame(update);
        }}
        animateCount('cnt-wait', {wait_val:.2f}, 1, 800);
        animateCount('cnt-thru', {thru_val}, 0, 800);
        animateCount('cnt-fit',  {fit_val:.4f}, 2, 800);
        animateCount('cnt-impr', {impr_val:.2f}, 1, 800);
        </script>
        """, unsafe_allow_html=True)

        # UPGRADE 3: Progress bar
        pct       = current_gen / max_gens
        bar_color = "#00ff99" if pct >= 1.0 else "#818cf8"
        st.markdown(f"""
        <div style="margin-bottom:1.2rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#4b5563;text-transform:uppercase;letter-spacing:0.15em;">Evolution Progress</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#6b7280;">{current_gen} / {max_gens} generations</span>
          </div>
          <div style="background:#111122;border-radius:999px;height:6px;overflow:hidden;border:1px solid #1e1e3f;">
            <div style="width:{pct*100:.1f}%;height:100%;border-radius:999px;
                        background:linear-gradient(90deg,#4f46e5,{bar_color});
                        box-shadow:0 0 8px {bar_color}88;
                        transition:width 0.6s ease;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # UPGRADE 4+5: Auto-refresh charts + baseline dashed line
        @st.fragment(run_every="10s")
        def render_charts():
            df_live = load_ga()
            if df_live.empty:
                return
            col1, col2 = st.columns(2)

            with col1:
                fig_wait = px.line(df_live, x="generation", y="avg_waiting_time",
                                   title="Avg Wait Time per Generation", markers=True)
                fig_wait.update_traces(
                    line_color="#ff6b6b", line_width=3,
                    marker=dict(size=8, color="#ff6b6b", line=dict(width=2, color=DARK_BG)))
                fig_wait.update_layout(**base_layout("Avg Wait Time per Generation",
                                                      xtitle="Generation", ytitle="Seconds"))
                fig_wait.add_hline(
                    y=85.34,
                    line_dash="dash",
                    line_color="rgba(255,180,50,0.6)",
                    line_width=1.5,
                    annotation_text="Baseline 85.34s",
                    annotation_position="top right",
                    annotation_font=dict(family=FONT_MONO, size=10, color="rgba(255,180,50,0.8)"),
                )
                add_glow(fig_wait, df_live["generation"], df_live["avg_waiting_time"], "255,107,107")
                st.plotly_chart(fig_wait, use_container_width=True)

            with col2:
                fig_fit = px.line(df_live, x="generation", y="fitness",
                                  title="Fitness Score per Generation", markers=True)
                fig_fit.update_traces(
                    line_color="#00ff99", line_width=3,
                    marker=dict(size=8, color="#00ff99", line=dict(width=2, color=DARK_BG)))
                fig_fit.update_layout(**base_layout("Fitness Score per Generation",
                                                     xtitle="Generation", ytitle="Fitness"))
                add_glow(fig_fit, df_live["generation"], df_live["fitness"], "0,255,153")
                st.plotly_chart(fig_fit, use_container_width=True)

        render_charts()

        # Gene evolution grid — YOUR version preserved exactly
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
        <div style="font-family:'Syne',sans-serif;font-size:0.95rem;color:#cbd5e1;line-height:1.9;max-width:1100px;">

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;font-size:1.05rem;letter-spacing:0.03em;">What the fitness and wait time curves show</span><br>
                    
        Each data point represents the single best solution found across the entire population at that generation, not the average or median.
        The fitness score never decreases from one generation to the next, because the GA saves the top 3 solutions each generation (elitism).
        Wait time can fluctuate because the fitness function values both throughput and wait time.
        a solution with a higher average wait time can still achieve higher fitness if it moves more vehicles through the network.
        </p>

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;font-size:1.05rem;letter-spacing:0.03em;">The improvement metric is relative to generation 1, not a fixed baseline</span><br>
                    
        The Improvement KPI above compares the current best solution to the best randomized gen 1 solution.
        Generation 1 represents the best of 12 random timing plans, which typically performs similarly to SUMO's default 42s/42s timing. 
        
        For a validated improvement on a fixed-timing baseline, refer to the Baseline vs GA tab 
        </p>

        <p style="margin-bottom:0;">
        <span style="color:#00ff99;font-weight:700;font-size:1.05rem;letter-spacing:0.03em;">What the gene evolution charts show</span><br>

        Each small chart tracks how the green phase duration for one intersection changed across generations.
        Each intersection in the 4×5 grid has two lines:
        <br><br>
        &nbsp;&nbsp;— phase A (North-South)<br>
        &nbsp;&nbsp;— phase B (East-West)
        <br><br>
        A flat line means the GA committed to a value early and stopped exploring: that timing is solved.
        A line that changes significantly at a specific generation corresponds to the breakthrough moment where
        the GA discovered a better coordinated pattern involving that intersection.
        Intersections with noisy or unstable lines throughout the run are less critical to overall network performance.
        Changing their timing has little effect on fitness either way, so mutation kept randomizing them without penalty.
                    
        It's interesting to note that there's a wide diversity in intersection configurations that it came up with. 
        When we tested 3 intersections, those 3 became uniform. We expected a more expect a uniform distribution here as well, but the GA found this asymmetrical approach better, at least 20 generations in.
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

        st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:0.95rem;color:#cbd5e1;line-height:1.9;max-width:1100px;">

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">What is being compared</span><br>

        The baseline is SUMO's default fixed timing, which is 42 seconds of green per phase on every intersection, equal in both directions, with no optimization applied.           
        The GA condition uses the best timing plan found after 20 generations of evolution, applied identically across all runs.
        Both conditions are evaluated 20 times each with different random seeds, so the box plots show the full distribution across varied traffic conditions, not a single result.
        Some seeds produce heavier traffic than others.
        </p>

        <p style="margin-bottom:1.2rem;">
        <span style="color:#00ff99;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">Why the GA wait time here is higher than the GA Progress tab shows</span><br>

        The GA Progress tab reports the best single simulation result seen during optimization.
        This tab reports the mean across 20 independent runs with varied seeds, another safeguard to ensure honest results.
        Some seeds produce harder traffic conditions where even the optimized plan struggles, the mean accounts for that.
        </p>

        <p style="margin-bottom:0;">
        <span style="color:#00ff99;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">What statistical significance means here</span><br>

        Welch's t-test checks whether the two wait time distributions could plausibly come from the same underlying population.
        A p-value near zero means: if the GA plan and the default plan were actually identical in performance,
        the probability of observing a difference this large across 20 runs is essentially zero.
        The result holds consistently across all tested seeds. it's not a lucky run.
                    
        <br><br>
        <i>Note: this result is scoped to this synthetic simulation, not an exact 1 to 1 translation to real life.</i>
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
    <div style="font-family:'Syne',sans-serif;font-size:0.95rem;color:#cbd5e1;line-height:1.9;max-width:1100px;">

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">The Search Space Problem</span><br>

    The search space is every possible combination of timing plans. Each intersection has 2 phases (A green time duration, B green time duration),
    which can have a value from 10s-80s, approximated as 70 possible values per gene.

    For n intersections, we have 2n genes. Each gene has 70 options, so total combinations is:
    <br><br>
    &nbsp;&nbsp;    70<sup>2n</sup>
    <br><br>
    With 3 intersections, that's 6 genes, 70<sup>6</sup>.
                
    With 20 intersections, that's 40 genes, 70<sup>40</sup>.
                
    For a real-life small city, 113 intersections is 226 genes, 70<sup>226</sup>, a number so large it loses meaning.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">So why use a Genetic Algorithm?</span><br>

    The GA doesn't check every combination in this space. It maintains a population of 12 candidates, runs them through SUMO to see how good they are (fitness evaluation),
    then combines the best ones (crossover) and randomly tweaks others (mutation) to find better solutions over time.
    "Black-box simulation evaluation" means the GA doesn't need to understand anything except whether the different values lead to better results within the simulation.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">A naive approach: O(P × G × T)</span><br>
    
    We faced a computational bottleneck. Sequential GA evaluation scales as <strong>O(P × G × T)</strong> where P = population size, G = generations, T = simulation time per evaluation.

    T is the dominant term and grows with network size: more intersections produce more vehicles requiring more simulation steps,
    and TraCI must process vehicle state at every step.
    At 20 intersections with 1,000+ simultaneous vehicles, T ≈ 10–15 minutes.

    Sequential evaluation requires P × T minutes per generation.
    
    With P=12, T=10min,
    that's 120 minutes per generation, or approximately 2,400 minutes (40 hours) for a full 20-generation run. This revealed the fundamental barrier to scaling.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">Parallel Evaluation: O(G × T)</span><br>

    When we scaled from 3 intersections to 20 intersections, we realized that the naive sequential approach would take way too long.
    So we implemented a parallel architecture which eliminates P from the complexity by evaluating all P population members across 12 processes (per candidate).
    Each of the 12 population members is assigned to an independent SUMO process with its own TraCI port.
    Since they run concurrently, the generation completes in time T, not P×T.

    This reduces total complexity to <strong>O(G × T)</strong>, a factor-P reduction.
    With P=12 workers matching population size P=12, the theoretical maximum speedup is 12×.
    Observed speedup is approximately 8–12× (8× at 20 intersections, 12.5× at 3 intersections) due to process spawning overhead,
    file I/O latency from the worker cache, and non-uniform simulation completion times.
    Faster workers must wait for the slowest member of each generation.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">The Coordination Problem</span><br>

    Multi-intersection optimization is qualitatively harder than single-intersection optimization.
    At a single intersection, optimal green split depends only on local demand.
    In a connected grid, timing at one intersection directly affects queue buildup on roads shared with adjacent intersections.

    A long green phase at J<sub>0,0</sub> dispatches a platoon toward J<sub>1,0</sub>; if J<sub>1,0</sub> is not timed to receive them,
    they arrive at red and wait, undoing the benefit.
    The globally optimal solution requires coordinated timing across the entire network simultaneously.
    This is the coordination problem, and explains the two-phase convergence observed at 20 intersections:
    early generations eliminate poor random solutions, while the breakthrough at an early generation corresponds to the GA
    discovering a coherent green wave; a timing cascade where vehicles cleared at one intersection
    arrive at the next during its green phase, propagating throughput gains across the grid.
    </p>

    <p style="margin-bottom:1.2rem;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">Scaling to city-scale</span><br>

    Thunder Bay, Ontario has approximately 113 signalized intersections, requiring a 226-gene chromosome.
    The O(G × T) complexity means wall-clock time per generation is determined entirely by T.
    Chromosome length does not affect it since the GA itself is fast; the bottleneck is always simulation.
    Provisioning a cloud instance with 113+ cores would evaluate an entire Thunder Bay-scale generation in approximately time T,
    the same wall-clock time as the current 20-intersection run. (It took a single PC 4 hours to run 20 generations across 20 intersections.)
    </p>

    <p style="margin-bottom:0;">
    <span style="color:#818cf8;font-weight:700;font-size:1.15rem;letter-spacing:0.03em;">Big Data Methodology</span><br>

    The project addresses the computational tractability problem that defines big data challenges:

    the search space is too large to process exhaustively, the evaluation function is expensive,
    and the solution requires parallel distributed computation to execute within practical time constraints.

    Each 20-intersection GA run processes 12 × 20 = 240 full SUMO simulations,
    each sustaining 1,000+ vehicles across 8,000 timesteps, generating millions of vehicle-state data points per run.
                
    The strategy is: Distribute the heavy computational work across independent workers, collect the metrics, present the data.
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
            import re
            nums = list(map(int, re.findall(r'\d+', rgb_str)))
            l = 0.299*nums[0] + 0.587*nums[1] + 0.114*nums[2]
            return "#000000" if l > 140 else "#ffffff"

        def render_intersection_grid(mode="plasma_a"):
            CELL = 160
            PAD  = 12
            ARM  = 44
            ROAD = 28
            LEG_W = 36
            LEG_PAD = 8
            grid_offset_x = LEG_W + LEG_PAD + PAD
            total_w = COLS * CELL + PAD * 2 + LEG_W + LEG_PAD
            total_h = ROWS * CELL + PAD * 2

            is_delta = mode in ("delta_a", "delta_b")

            svg_parts = [
                f'<svg viewBox="0 0 {total_w} {total_h}" '
                f'xmlns="http://www.w3.org/2000/svg" '
                f'style="width:100%;background:#0a0a0f;border-radius:12px;">'
            ]

            leg_x = PAD
            leg_y = PAD + 20
            leg_h = ROWS * CELL - 40
            steps = 40

            leg_gid = f"leg_{mode}"
            svg_parts.append(f'<defs><linearGradient id="{leg_gid}" x1="0" y1="0" x2="0" y2="1">')
            for i in range(steps + 1):
                frac = i / steps
                if is_delta:
                    delta_val = 38 * (1 - frac) + (-35) * frac
                    c = val_to_rdylgn(delta_val)
                else:
                    v = 80 * (1 - frac) + 10 * frac
                    c = val_to_viridis(v)
                svg_parts.append(f'<stop offset="{frac*100:.1f}%" stop-color="{c}"/>')
            svg_parts.append(f'</linearGradient></defs>')

            svg_parts.append(
                f'<rect x="{leg_x}" y="{leg_y}" width="{LEG_W-4}" height="{leg_h}" '
                f'fill="url(#{leg_gid})" rx="3"/>')

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
                    else:
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
                    svg_parts.append(
                        f'<defs><radialGradient id="{gid}" cx="50%" cy="50%" r="50%">'
                        f'<stop offset="0%" stop-color="#ffffff" stop-opacity="0.09"/>'
                        f'<stop offset="60%" stop-color="#ffffff" stop-opacity="0.03"/>'
                        f'<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>'
                        f'</radialGradient></defs>')

                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy-half}" width="{ROAD}" height="{half-road}" fill="{color_ns}"/>')
                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy+road}" width="{ROAD}" height="{half-road}" fill="{color_ns}"/>')
                    svg_parts.append(
                        f'<rect x="{cx-half}" y="{cy-road}" width="{half-road}" height="{ROAD}" fill="{color_ew_actual}"/>')
                    svg_parts.append(
                        f'<rect x="{cx+road}" y="{cy-road}" width="{half-road}" height="{ROAD}" fill="{color_ew_actual}"/>')

                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy-road}" width="{ROAD}" height="{ROAD}" '
                        f'fill="{color_ns}" opacity="0.5"/>')
                    svg_parts.append(
                        f'<rect x="{cx-road}" y="{cy-road}" width="{ROAD}" height="{ROAD}" '
                        f'fill="{color_ew_actual}" opacity="0.5"/>')

                    full_span = CELL - 6
                    svg_parts.append(
                        f'<rect x="{cx - full_span//2}" y="{cy - full_span//2}" '
                        f'width="{full_span}" height="{full_span}" '
                        f'fill="url(#{gid})" pointer-events="none"/>')

                    svg_parts.append(
                        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#ffffff" opacity="0.75"/>')

                    svg_parts.append(
                        f'<text x="{cx}" y="{cy-road-6}" '
                        f'text-anchor="middle" font-size="9" font-family="monospace" '
                        f'stroke="#000000" stroke-width="2.5" paint-order="stroke" '
                        f'fill="#ffffff" font-weight="bold">{label_ns}</text>')

                    svg_parts.append(
                        f'<text x="{cx+road+4}" y="{cy+4}" '
                        f'text-anchor="start" font-size="9" font-family="monospace" '
                        f'stroke="#000000" stroke-width="2.5" paint-order="stroke" '
                        f'fill="#ffffff" font-weight="bold">{label_ew}</text>')

                    svg_parts.append(
                        f'<text x="{cx}" y="{cy+half-4}" '
                        f'text-anchor="middle" font-size="8" font-family="monospace" '
                        f'stroke="#000000" stroke-width="2" paint-order="stroke" '
                        f'fill="#e2e8f0">J_{col}_{row}</text>')

            svg_parts.append('</svg>')
            return ''.join(svg_parts)

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

        st.markdown("<h3 style='color:#f0f4ff;margin-bottom:0.3rem;'>Deviadirtion from Default Timing (42s baseline)</h3>",
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