import streamlit as st
import lasio
import plotly.graph_objs as go
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Petrophysical LAS Viewer", layout="wide")
st.title("🛢️ Petrophysical LAS Viewer")

# Sidebar
st.sidebar.header("⚙️ Options")
uploaded_file = st.sidebar.file_uploader("Upload a .las file", type=["las"])
unit_system = st.sidebar.radio("Select Unit System", ("Metric", "Imperial"))

unit_conversions = {
    "m": ("ft", lambda x: x * 3.28084),
    "g/cm3": ("lb/ft3", lambda x: x * 62.428),
    "us/ft": ("us/ft", lambda x: x),
    "ohm.m": ("ohm.m", lambda x: x),
    "in": ("in", lambda x: x),
    "m3/m3": ("v/v", lambda x: x)
}

if uploaded_file:
    try:
        # Convert file to binary stream
        file_bytes = uploaded_file.read()
        las = lasio.read(BytesIO(file_bytes))  # Use BytesIO for binary stream
        st.success(f"Loaded LAS file: {uploaded_file.name}")
    except Exception as e:
        st.error(f"Failed to read LAS file: {e}")
        st.stop()

    curves = las.curves
    available = [curve.mnemonic for curve in curves]
    st.sidebar.subheader("📈 Select Curves")
    track1 = st.sidebar.multiselect("Track 1 (e.g. GR)", available, default=["GR"] if "GR" in available else [available[0]])
    track2 = st.sidebar.multiselect("Track 2 (e.g. RHOB/NPHI)", available, default=["RHOB", "NPHI"])
    track3 = st.sidebar.multiselect("Track 3 (e.g. RT)", available, default=["RT"] if "RT" in available else [])

    depth = las["DEPT"]
    depth_unit = "m"
    if unit_system == "Imperial":
        depth = depth * 3.28084
        depth_unit = "ft"

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

                # Shale shading
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

        fig.update_layout(
            title=title,
            yaxis=dict(title=f"Depth ({depth_unit})", autorange="reversed"),
            height=800,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=True
        )
        return fig

    # Layout with 3 tracks
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(make_track(track1, "Track 1", highlight_shale=True), use_container_width=True)
    with col2:
        st.plotly_chart(make_track(track2, "Track 2"), use_container_width=True)
    with col3:
        st.plotly_chart(make_track(track3, "Track 3"), use_container_width=True)

else:
    st.info("👈 Upload a .las file from the sidebar to get started!")
