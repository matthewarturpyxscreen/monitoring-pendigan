import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Instalasi IFP",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.cache_data.clear()

# ======================================================
# HELPER FUNCTIONS
# ======================================================
def normalize_status(val):
    """
    NORMALISASI KE 2 STATUS SAJA
    """
    if pd.isna(val) or str(val).strip() == "":
        return "Belum Dikerjakan"

    val = str(val).upper()
    if "SELESAI" in val:
        return "Selesai"
    return "Belum Dikerjakan"


def get_status_priority(status):
    """
    PRIORITAS UNTUK DEDUP
    """
    priority = {
        "Selesai": 1,
        "Belum Dikerjakan": 2
    }
    return priority.get(status, 99)


def get_status_color(status):
    return "#10b981" if status == "Selesai" else "#94a3b8"


def get_status_emoji(status):
    return "✅" if status == "Selesai" else "⏳"


def load_google_sheet(sheet_url):
    """
    LOAD GOOGLE SHEET KE DATAFRAME
    """
    if "docs.google.com" not in sheet_url:
        st.error("URL Google Sheet tidak valid")
        return None

    csv_url = sheet_url.replace("/edit", "/export?format=csv")
    response = requests.get(csv_url)

    if response.status_code != 200:
        st.error("Gagal mengambil data dari Google Sheet")
        return None

    return pd.read_csv(BytesIO(response.content))


# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title("⚙️ Pengaturan")

sheet_url = st.sidebar.text_input(
    "🔗 Google Sheet URL",
    placeholder="https://docs.google.com/spreadsheets/..."
)

status_filter = st.sidebar.selectbox(
    "📊 Filter Status",
    ["Semua Status", "Belum Dikerjakan", "Selesai"]
)

refresh = st.sidebar.button("🔄 Refresh Data")

# ======================================================
# LOAD DATA
# ======================================================
if sheet_url:
    with st.spinner("⏳ Mengambil data..."):
        df = load_google_sheet(sheet_url)

    if df is None or df.empty:
        st.stop()

    # ==================================================
    # VALIDASI KOLOM WAJIB
    # ==================================================
    required_cols = ["NPSN", "Status_Text"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom wajib tidak ditemukan: {col}")
            st.stop()

    # ==================================================
    # NORMALISASI STATUS
    # ==================================================
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)
    df["Priority"] = df["Status_Category"].apply(get_status_priority)

    # ==================================================
    # DEDUP BERDASARKAN NPSN
    # ==================================================
    df = (
        df.sort_values("Priority")
          .drop_duplicates(subset="NPSN", keep="first")
          .reset_index(drop=True)
    )

    # ==================================================
    # FILTER STATUS
    # ==================================================
    if status_filter != "Semua Status":
        df = df[df["Status_Category"] == status_filter]

    # ==================================================
    # METRICS
    # ==================================================
    total_data = len(df)
    total_selesai = (df.Status_Category == "Selesai").sum()
    total_belum = (df.Status_Category == "Belum Dikerjakan").sum()

    st.title("📊 Dashboard Monitoring Instalasi IFP")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📄 TOTAL DATA", total_data)

    with col2:
        st.metric(
            "⏳ BELUM DIKERJAKAN",
            total_belum,
            f"{(total_belum / total_data * 100):.1f}%" if total_data else "0%"
        )

    with col3:
        st.metric(
            "✅ SELESAI",
            total_selesai,
            f"{(total_selesai / total_data * 100):.1f}%" if total_data else "0%"
        )

    # ==================================================
    # PROGRESS BAR
    # ==================================================
    if total_data > 0:
        st.subheader("📈 Progress Pengerjaan")
        st.progress(total_selesai / total_data)
        st.caption(f"{total_selesai} dari {total_data} sekolah selesai")

    # ==================================================
    # TABLE VIEW
    # ==================================================
    st.subheader("📋 Data Detail")

    def render_status(val):
        color = get_status_color(val)
        emoji = get_status_emoji(val)
        return f"<span style='color:{color}; font-weight:600'>{emoji} {val}</span>"

    df_display = df.copy()
    df_display["Status"] = df_display["Status_Category"].apply(render_status)

    show_cols = [c for c in df_display.columns if c not in ["Priority", "Status_Text", "Status_Category"]]
    show_cols.insert(0, "Status")

    st.write(
        df_display[show_cols].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    # ==================================================
    # FOOTER
    # ==================================================
    st.caption(
        f"🕒 Terakhir update: {datetime.now().strftime('%d %b %Y %H:%M:%S')}"
    )

else:
    st.info("⬅️ Masukkan URL Google Sheet untuk memulai")
