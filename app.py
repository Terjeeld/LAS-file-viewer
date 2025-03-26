import streamlit as st
import lasio
import matplotlib.pyplot as plt
import io

st.title("🌍 LAS File Viewer")

uploaded_file = st.file_uploader("Upload a .las file", type=["las"])

if uploaded_file:
    
    las = lasio.read(io.StringIO(uploaded_file.getvalue().decode("utf-8")))
    
    st.subheader("Header Info")
    st.text(str(las.header))

    st.subheader("Available Curves")
    curves = list(las.curves.keys())
    st.write(curves)

    # Select which logs to plot
    selected = st.multiselect("Select logs to plot vs depth", curves)

    depth = las['DEPT']
    for curve in selected:
        plt.figure()
        plt.plot(las[curve], depth)
        plt.gca().invert_yaxis()
        plt.xlabel(curve)
        plt.ylabel("Depth")
        plt.title(f"{curve} vs Depth")
        st.pyplot(plt)
