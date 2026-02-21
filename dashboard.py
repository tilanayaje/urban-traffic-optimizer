import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Urban Traffic Optimization Dashboard",
    layout="wide",
    page_icon="🚦"
)

st.title("Real-Time Traffic Flow Optimization")
st.markdown("Monitoring Genetic Algorithm progress on the **J11 Urban Traffic Network**")

# Create a placeholder for the live-updating content
dashboard_placeholder = st.empty()

# --- HELPER FUNCTION TO LOAD DATA ---
def load_data():
    if os.path.exists("ga_history.csv"):
        try:
            # We use try-except just in case Streamlit tries to read the file 
            # at the exact millisecond the simulation is writing to it.
            return pd.read_csv("ga_history.csv")
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# --- REAL-TIME LOOP ---
while True:
    df = load_data()
    
    with dashboard_placeholder.container():
        # Check if we have data to show
        if not df.empty and len(df) > 0:
            latest = df.iloc[-1]
            first = df.iloc[0]
            
            # --- ROW 1: KEY PERFORMANCE INDICATORS ---
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            kpi1.metric(
                label="Current Generation",
                value=int(latest['generation'])
            )
            
            # Wait Time Delta (Current vs First)
            wait_delta = latest['avg_waiting_time'] - first['avg_waiting_time']
            kpi2.metric(
                label="Avg Waiting Time (s)",
                value=f"{latest['avg_waiting_time']:.1f}",
                delta=f"{wait_delta:.1f} s",
                delta_color="inverse" # Green means lower time (which is good for traffic)
            )
            
            # Throughput Delta
            thru_delta = latest['throughput'] - first['throughput']
            kpi3.metric(
                label="Throughput (Cars)",
                value=int(latest['throughput']),
                delta=int(thru_delta)
            )

            kpi4.metric(
                label="Best Fitness Score",
                value=f"{latest['fitness']:.2f}"
            )

            # --- ROW 2: CHARTS ---
            col1, col2 = st.columns(2)
            
            with col1:
                # Chart 1: Waiting Time Reduction (Proves the algorithm works)
                fig_wait = px.line(
                    df, 
                    x='generation', 
                    y='avg_waiting_time',
                    title='📉 Average Waiting Time (Lower is Better)',
                    markers=True,
                    template="plotly_dark"
                )
                fig_wait.update_traces(line_color='#FF4B4B')
                st.plotly_chart(fig_wait, use_container_width=True, key=f"wait_chart_{time.time()}")

            with col2:
                # Chart 2: Traffic Light Timing Evolution (Shows the genes mutating)
                fig_timings = px.line(
                    df,
                    x='generation',
                    y=['green_north', 'green_east'],
                    title='⏱️ Traffic Light Phase Evolution (Genes)',
                    markers=True,
                    template="plotly_dark"
                )
                st.plotly_chart(fig_timings, use_container_width=True, key=f"time_chart_{time.time()}")
        
        else:
            # Show a loading message if the CSV isn't ready yet
            st.info("Waiting for simulation data... The dashboard will update automatically.")
            
    # Refresh the dashboard every 2 seconds
    time.sleep(2)