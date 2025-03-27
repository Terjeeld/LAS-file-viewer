import streamlit as st
import lasio
import plotly.graph_objs as go
import numpy as np
import pandas as pd
from io import StringIO
from PIL import Image

# === Set page layout ===
st.set_page_config(page_title="Petrophysical LAS Viewer", layout="wide")

# === Load logo and title ===
logo = Image.open("logo.png")  # Ensure logo.png is in the repo
col1, col2 = st.columns([1, 10])
with col1:
    st.image(logo, width=100)
with col2:
    st.markdown("<h1 style='margin-bottom: 0;'>Petrophysical LAS Viewer</h1>", unsafe_allow_html=True)

# === Sidebar controls ===
st.sidebar.header("⚙️ Options")
uploaded_file = st.sidebar.file_uploader("Upload a .las file", type=["las"])
unit_system = st.sidebar.radio("Select Unit System", ("Metric", "Imperial"))

# 🔧 Ensure Strip Log Mode toggle appears!
strip_log_mode = st.sidebar.checkbox("Enable Strip Log Mode (Side-by-Side Tracks)", value=False)
track_width = st.sidebar.slider("Track Width", min_value=300, max_value=800, value=500)


# === Load and parse LAS ===
if uploaded_file:
    try:
        # Read and parse LAS file
        stringio = StringIO(uploaded_file.read().decode("utf-8", errors="ignore"))
        las = lasio.read(stringio)
        st.success(f"✅ Loaded LAS file: {uploaded_file.name}")
    except Exception as e:
        st.error(f"❌ Failed to read LAS file: {e}")
        st.stop()

    # === Extract Well Information ===
    well_info_keys = ["WELL", "COMP", "FLD", "LOC", "UWI", "DATE"]
    well_info = {key: las.well[key].value if key in las.well.keys() else "N/A" for key in well_info_keys}

    # Display Well Information
    st.markdown("## 🏭 Well Information")
    st.write(pd.DataFrame([well_info]))

    # === Detect Depth Column ===
    depth_mnemonics = ["DEPT", "DEPTH", "MD", "TVD"]
    depth_curve = next((mn for mn in depth_mnemonics if mn in las.keys()), None)

    if depth_curve:
        depth = las[depth_curve]
    else:
        st.error("⚠️ No valid depth column found (Checked: DEPT, DEPTH, MD, TVD). Cannot proceed.")
        st.stop()

    # === Curve Selection ===
    available = [curve.mnemonic for curve in las.curves] if hasattr(las, "curves") else []
    
    if available:
        st.sidebar.subheader("📈 Select Curves")
        st.sidebar.markdown("**Available Curves in LAS File:**")
        st.sidebar.write(", ".join(available))
        track1 = st.sidebar.multiselect("Track 1", available)
        track2 = st.sidebar.multiselect("Track 2", available)
        track3 = st.sidebar.multiselect("Track 3", available)
    else:
        st.sidebar.error("⚠️ No curves found in this LAS file.")

    # === Depth Conversion ===
    depth_unit = "m"
    if unit_system == "Imperial":
        depth = depth * 3.28084
        depth_unit = "ft"

    # === Plotting Function ===
    def make_track(curve_names, title):
        fig = go.Figure()
        for curve in curve_names:
            if curve in las.keys():
                data = las[curve]
                unit = las.curves[curve].unit
                mask = (data != -999.25) & (~np.isnan(data))
                if mask.sum() == 0:
                    st.warning(f"⚠️ No valid data for {curve}, skipping plot.")
                    continue
                fig.add_trace(go.Scatter(x=data[mask], y=depth[mask], mode="lines", name=f"{curve} ({unit})"))
        fig.update_layout(title=title, yaxis=dict(title=f"Depth ({depth_unit})", autorange="reversed"), height=800, showlegend=True)
        return fig

    # === Plot Layout ===
    st.subheader("📊 Log Tracks")
    if strip_log_mode:
        col1, col2, col3 = st.columns([1, 1, 1])
        if track1: col1.plotly_chart(make_track(track1, "Track 1"), use_container_width=True)
        if track2: col2.plotly_chart(make_track(track2, "Track 2"), use_container_width=True)
        if track3: col3.plotly_chart(make_track(track3, "Track 3"), use_container_width=True)
    else:
        if track1: st.plotly_chart(make_track(track1, "Track 1"), use_container_width=True)
        if track2: st.plotly_chart(make_track(track2, "Track 2"), use_container_width=True)
        if track3: st.plotly_chart(make_track(track3, "Track 3"), use_container_width=True)

    # === CSV Export ===
    st.sidebar.subheader("📥 Export Data")
    selected_curves = track1 + track2 + track3
    if selected_curves:
        df = pd.DataFrame({curve: las[curve] for curve in selected_curves})
        df["Depth"] = depth
        st.sidebar.download_button("Download CSV", df.to_csv(index=False), "las_data.csv", "text/csv")
else:
    st.info("👈 Upload a `.las` file to get started")
