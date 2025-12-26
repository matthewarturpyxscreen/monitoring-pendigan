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
    if pd.isna(val) or str(val).strip() == "":
        return "Belum Dikerjakan"

    val = str(val).upper()
    if "SELESAI" in val:
        return "Selesai"
    return "Belum Dikerjakan"


def get_status_priority(status):
    return 1 if status == "Selesai" else 2


def load_sheet_by_gid(base_url, gid):
    """
    LOAD SATU TAB BERDASARKAN GID
    """
    try:
        csv_url = f"{base_url}/export?format=csv&gid={gid}"
        res = requests.get(csv_url, timeout=20)

        if res.status_code != 200:
            st.warning(f"Gagal load gid {gid} (HTTP {res.status_code})")
            return None

        df = pd.read_csv(BytesIO(res.content))
        df["__gid__"] = gid
        return df

    except Exception as e:
        st.warning(f"Error gid {gid}: {e}")
        return None


# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title("⚙️ Pengaturan")

base_url = st.sidebar.text_input(
    "🔗 Google Sheet URL (tanpa /edit)",
    placeholder="https://docs.google.com/spreadsheets/d/FILE_ID"
)

gid_input = st.sidebar.text_input(
    "📄 Daftar GID (pisahkan koma)",
    placeholder="0,123456789,987654321"
)

status_filter = st.sidebar.selectbox(
    "📊 Filter Status",
    ["Semua Status", "Belum Dikerjakan", "Selesai"]
)

# ======================================================
# LOAD DATA MULTI GID
# ======================================================
if base_url and gid_input:
    gids = [g.strip() for g in gid_input.split(",") if g.strip().isdigit()]

    if not gids:
        st.error("❌ GID tidak valid")
        st.stop()

    with st.spinner("⏳ Mengambil data dari semua GID..."):
        df_list = []
        for gid in gids:
            df_part = load_sheet_by_gid(base_url, gid)
            if df_part is not None and not df_part.empty:
                df_list.append(df_part)

    if not df_list:
        st.error("❌ Tidak ada data yang berhasil dimuat")
        st.stop()

    df = pd.concat(df_list, ignore_index=True)

    # ==================================================
    # VALIDASI KOLOM
    # ==================================================
    for col in ["NPSN", "Status_Text"]:
        if col not in df.columns:
            st.error(f"❌ Kolom wajib tidak ditemukan: {col}")
            st.stop()

    # ==================================================
    # NORMALISASI STATUS
    # ==================================================
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)
    df["Priority"] = df["Status_Category"].apply(get_status_priority)

    # ==================================================
    # DEDUP BY NPSN
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
    total = len(df)
    selesai = (df.Status_Category == "Selesai").sum()
    belum = total - selesai

    st.title("📊 Dashboard Monitoring Instalasi IFP (Multi GID)")

    c1, c2, c3 = st.columns(3)
    c1.metric("📄 TOTAL DATA", total)
    c2.metric("⏳ BELUM DIKERJAKAN", belum)
    c3.metric("✅ SELESAI", selesai)

    if total > 0:
        st.progress(selesai / total)
        st.caption(f"{selesai} dari {total} sekolah selesai")

    # ==================================================
    # TABLE
    # ==================================================
    st.subheader("📋 Data Detail")

    def render_status(s):
        return "✅ Selesai" if s == "Selesai" else "⏳ Belum Dikerjakan"

    df_show = df.copy()
    df_show.insert(0, "Status", df_show["Status_Category"].apply(render_status))

    hide_cols = ["Status_Text", "Status_Category", "Priority"]
    show_cols = [c for c in df_show.columns if c not in hide_cols]

    st.dataframe(df_show[show_cols], use_container_width=True)

    st.caption(
        f"🕒 Update: {datetime.now().strftime('%d %b %Y %H:%M:%S')}"
    )

else:
    st.info("⬅️ Masukkan URL Google Sheet & daftar GID")
