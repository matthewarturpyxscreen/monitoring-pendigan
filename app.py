import streamlit as st
import pandas as pd
import requests
import re
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
def parse_gsheet_url(url):
    """
    Terima SEMUA format link Google Sheets,
    kembalikan base_url dan gid
    """
    if not url:
        return None, None

    file_id_match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if not file_id_match:
        return None, None

    file_id = file_id_match.group(1)
    base_url = f"https://docs.google.com/spreadsheets/d/{file_id}"

    gid_match = re.search(r"gid=([0-9]+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    return base_url, gid


def normalize_status(val):
    if pd.isna(val):
        return "Belum Dikerjakan"

    val = str(val).upper()

    if "SELESAI" in val:
        return "Selesai"
    if "BAPP" in val:
        return "BAPP"
    if "PROSES" in val:
        return "Proses Pengerjaan"
    if "FOTO" in val:
        return "Kekurangan Foto"
    if "KENDALA" in val:
        return "Kendala"

    return "Belum Dikerjakan"


def get_status_priority(status):
    priority = {
        "Selesai": 1,
        "BAPP": 2,
        "Proses Pengerjaan": 3,
        "Kekurangan Foto": 4,
        "Kendala": 5,
        "Belum Dikerjakan": 6
    }
    return priority.get(status, 99)


@st.cache_data(ttl=300)
def load_sheet_by_gid(base_url, gid):
    """
    Load 1 sheet Google Spreadsheet via CSV export
    """
    try:
        csv_url = f"{base_url}/export?format=csv&gid={gid}"
        res = requests.get(csv_url, timeout=20)

        if res.status_code != 200:
            return None

        df = pd.read_csv(BytesIO(res.content))
        df["__gid__"] = gid
        return df

    except Exception:
        return None


# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title("⚙️ Pengaturan")

gsheet_url = st.sidebar.text_input(
    "🔗 Google Sheets Link",
    placeholder="Paste link Google Sheets di sini"
)

status_filter = st.sidebar.selectbox(
    "📊 Filter Status",
    [
        "Semua Status",
        "Belum Dikerjakan",
        "Proses Pengerjaan",
        "Kekurangan Foto",
        "BAPP",
        "Kendala",
        "Selesai"
    ]
)

# ======================================================
# LOAD & PROCESS DATA
# ======================================================
base_url, gid = parse_gsheet_url(gsheet_url)

if base_url and gid:

    with st.spinner("⏳ Mengambil data dari Google Sheets..."):
        df = load_sheet_by_gid(base_url, gid)

    if df is None or df.empty:
        st.error("❌ Data tidak bisa diakses. Pastikan sheet PUBLIC (Anyone with link → Viewer).")
        st.stop()

    # ==================================================
    # VALIDASI KOLOM WAJIB
    # ==================================================
    required_cols = ["NPSN", "Status_Text"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"❌ Kolom wajib tidak ditemukan: {col}")
            st.stop()

    # ==================================================
    # NORMALISASI STATUS
    # ==================================================
    df["Status_Category"] = df["Status_Text"].apply(normalize_status)
    df["Priority"] = df["Status_Category"].apply(get_status_priority)

    # ==================================================
    # DEDUP BY NPSN (AMBIL STATUS TERBAIK)
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
    selesai = (df["Status_Category"] == "Selesai").sum()
    belum = total - selesai

    st.title("📊 Dashboard Monitoring Instalasi IFP")

    c1, c2, c3 = st.columns(3)
    c1.metric("📄 TOTAL DATA", total)
    c2.metric("⏳ BELUM SELESAI", belum)
    c3.metric("✅ SELESAI", selesai)

    if total > 0:
        st.progress(selesai / total)
        st.caption(f"{selesai} dari {total} sekolah selesai")

    # ==================================================
    # TABLE
    # ==================================================
    st.subheader("📋 Data Detail")

    def render_status(s):
        icon = {
            "Selesai": "✅",
            "BAPP": "🔵",
            "Proses Pengerjaan": "🟡",
            "Kekurangan Foto": "🟣",
            "Kendala": "🔴",
            "Belum Dikerjakan": "⏳"
        }
        return f"{icon.get(s, '⏳')} {s}"

    df_show = df.copy()
    df_show.insert(0, "Status", df_show["Status_Category"].apply(render_status))

    hide_cols = ["Status_Text", "Status_Category", "Priority", "__gid__"]
    show_cols = [c for c in df_show.columns if c not in hide_cols]

    st.dataframe(
        df_show[show_cols],
        use_container_width=True,
        height=600
    )

    st.caption(
        f"🕒 Update terakhir: {datetime.now().strftime('%d %b %Y %H:%M:%S')}"
    )

else:
    st.info("⬅️ Paste link Google Sheets untuk mulai")
