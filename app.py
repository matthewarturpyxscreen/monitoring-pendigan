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
    Load satu sheet Google Spreadsheet berdasarkan GID (CSV Export)
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

base_url = st.sidebar.text_input(
    "🔗 Google Sheet URL (tanpa /edit)",
    placeholder="https://docs.google.com/spreadsheets/d/FILE_ID"
)

gid_input = st.sidebar.text_input(
    "📄 Daftar GID (pisahkan koma)",
    placeholder="0,123456789"
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
if base_url and gid_input:
    gids = [g.strip() for g in gid_input.split(",") if g.strip().isdigit()]

    if not gids:
        st.error("❌ GID tidak valid")
        st.stop()

    with st.spinner("⏳ Mengambil data dari Google Sheets..."):
        df_list = []
        for gid in gids:
            part = load_sheet_by_gid(base_url, gid)
            if part is not None and not part.empty:
                df_list.append(part)

    if not df_list:
        st.error("❌ Tidak ada data yang berhasil dimuat")
        st.stop()

    df = pd.concat(df_list, ignore_index=True)

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
    # DEDUP BY NPSN (STATUS TERBAIK)
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
    st.info("⬅️ Masukkan URL Google Sheet & GID untuk mulai")
