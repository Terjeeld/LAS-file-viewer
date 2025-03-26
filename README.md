# 🌍 LAS File Viewer (Web App)

A simple web-based viewer for `.las` well log files built using Python and Streamlit. Upload `.las` files and view available curves with interactive depth plots.

## 🚀 Try it Live
👉 [Launch App on Streamlit](https://share.streamlit.io/) *(Link appears after deployment)*

## 📦 Features
- Upload `.las` files directly in your browser
- Display header info and available curves
- Plot any curve against depth (auto-detects depth column)

## 🛠️ Built With
- [Streamlit](https://streamlit.io)
- [lasio](https://lasio.readthedocs.io/)
- [matplotlib](https://matplotlib.org/)

## 📋 Run Locally

```bash
git clone https://github.com/Terjeeld/LAS-file-viewer.git
cd LAS-file-viewer
pip install -r requirements.txt
streamlit run app.py
