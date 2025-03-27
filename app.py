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

# === Curve descriptions ===
curve_info = {
    "GR": "Gamma Ray (shale content indicator)",
    "CALI": "Caliper (borehole diameter)",
    "RT": "True Resistivity (formation resistivity)",
    "RHOB": "Bulk Density",
    "NPHI": "Neutron Porosity",
    "DTC": "Compressional Sonic Travel Time",
    "DTS": "Shear Sonic Travel Time",
    "RXO": "Resistivity of flushed zone",
    "DRHO": "Density correction",
    "TVD": "True Vertical Depth",
    "TVDSS": "TVD Sub Sea",
    "BS": "Bit Size or Borehole Size",
    "DCAL": "Delta Caliper",
    "HAZI": "Hole Azimuth",
    "HDEVI": "Hole Deviation",
}

# === Unit conversion map ===
unit_conversions = {
    "m": ("ft", lambda x: x * 3.28084),
    "g/cm3": ("lb/ft3", lambda x: x * 62.428),
    "us/ft": ("us/ft", lambda x: x),
    "ohm.m": ("ohm.m", lambda x: x),
    "in": ("in", lambda x: x),
    "m3/m3": ("v/v", lambda x: x),
}

# === Load and parse LAS ===
if uploaded_file:
    try:
        stringio = StringIO(uploaded_file.read().decode("utf-8", errors="ignore"))
        las = lasio.read(stringio)
        st.success(f"Loaded LAS file: {uploaded_file.name}")
    except Exception as e:
        st.error(f"Failed to read LAS file: {e}")
        st.stop()

    curves = las.curves
    available = [curve.mnemonic for curve in curves]

    # === Search bar for quick curve selection ===
    search_query = st.sidebar.text_input("🔍 Search Curves", "")
    filtered_curves = [c for c in available if search_query.lower() in c.lower()] if search_query else available

    st.sidebar.subheader("📈 Select Curves")
    st.sidebar.markdown("**Available Curves in LAS File:**")
    st.sidebar.write(", ".join(available))

    # Function to auto-select defaults if they exist, otherwise pick first N available
    def get_default_curves(preferred, available, num=2):
        defaults = [c for c in preferred if c in available]
        return defaults if defaults else available[:num]

    # Dynamic selection with search filtering
    track1 = st.sidebar.multiselect("Track 1 (e.g. GR)", filtered_curves, default=get_default_curves(["GR"], available, 1))
    track2 = st.sidebar.multiselect("Track 2 (e.g. RHOB/NPHI)", filtered_curves, default=get_default_curves(["RHOB", "NPHI"], available, 2))
    track3 = st.sidebar.multiselect("Track 3 (e.g. RT)", filtered_curves, default=get_default_curves(["RT"], available, 1))


    # === Depth conversion ===
    depth_mnemonics = ["DEPT", "DEPTH", "MD", "TVD"]
    depth_curve = next((mn for mn in depth_mnemonics if mn in las.keys()), None)
    
    if depth_curve:
        depth = las[depth_curve]
    else:
        st.error("No valid depth column found (Checked: DEPT, DEPTH, MD, TVD). Cannot proceed.")
    st.stop()

    depth_unit = "m"
    if unit_system == "Imperial":
        depth = depth * 3.28084
        depth_unit = "ft"

    # === Formation tops overlay (User input) ===
    st.sidebar.subheader("📌 Formation Tops")
    tops_data = st.sidebar.text_area("Enter formation tops (Format: Name, Depth)", "Top1, 1000\nTop2, 1500")
    tops = [line.split(",") for line in tops_data.split("\n") if len(line.split(",")) == 2]

    # Convert to dictionary (formation: depth)
    tops_dict = {name.strip(): float(depth.strip()) for name, depth in tops}

    # === Plotting Function ===
    def make_track(curve_names, title, highlight_shale=False):
        fig = go.Figure()

        for curve in curve_names:
            if curve in las.curves:
                data = las[curve]
                unit = las.curves[curve].unit
                if unit_system == "Imperial" and unit in unit_conversions:
                    unit_label, convert_fn = unit_conversions[unit]
                    data = convert_fn(data)
                else:
                    unit_label = unit

                mask = data != -999.25
                fig.add_trace(go.Scatter(
                    x=data[mask],
                    y=depth[mask],
                    mode="lines",
                    name=f"{curve} ({unit_label})"
                ))

                # Shale highlight
                if highlight_shale and curve == "GR":
                    gr_threshold = 75
                    shale_mask = (data > gr_threshold) & (data != -999.25)
                    fig.add_trace(go.Scatter(
                        x=data[shale_mask],
                        y=depth[shale_mask],
                        mode="lines",
                        line=dict(color="rgba(0,100,0,0.2)", width=10),
                        name="Shale Zone",
                        showlegend=False
                    ))

        # Add formation tops
        for top_name, top_depth in tops_dict.items():
            fig.add_shape(type="line", x0=min(data), x1=max(data), y0=top_depth, y1=top_depth,
                          line=dict(color="red", width=2, dash="dash"))
            fig.add_annotation(x=max(data), y=top_depth, text=top_name, showarrow=False, font=dict(color="red"))

        fig.update_layout(
            title=title,
            yaxis=dict(title=f"Depth ({depth_unit})", autorange="reversed"),
            height=800,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=True
        )
        return fig

    # === Plot Layout ===
    st.subheader("📊 Log Tracks")
    
    # Plot each track separately, one below the other
    if track1:
        st.plotly_chart(make_track(track1, "Track 1 (e.g. GR)", highlight_shale=True), use_container_width=True)
    
    if track2:
        st.plotly_chart(make_track(track2, "Track 2 (e.g. RHOB/NPHI)"), use_container_width=True)
    
    if track3:
        st.plotly_chart(make_track(track3, "Track 3 (e.g. RT)"), use_container_width=True)


    # === CSV Export ===
    st.sidebar.subheader("📥 Export Data")
    selected_curves = track1 + track2 + track3
    if selected_curves:
        df = pd.DataFrame({curve: las[curve] for curve in selected_curves})
        df["Depth"] = depth
        st.sidebar.download_button("Download CSV", df.to_csv(index=False), "las_data.csv", "text/csv")

else:
    st.info("👈 Upload a `.las` file to get started")
