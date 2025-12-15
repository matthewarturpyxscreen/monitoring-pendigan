import streamlit as st
import pandas as pd
import re
import requests
from io import StringIO

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard Monitoring Pekerjaan",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_INTERVAL = 300  # 5 menit

# Custom CSS untuk design modern
st.markdown("""
    <style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    
    /* Title styling */
    h1 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        font-weight: 700 !important;
    }
    
    h2, h3 {
        color: white !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Info box */
    .stAlert {
        border-radius: 8px;
        background: white;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Auto refresh
st.markdown(
    f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>",
    unsafe_allow_html=True
)

# ======================================================
# HEADER
# ======================================================
st.title("📊 Dashboard Monitoring Pekerjaan")
st.markdown("### *Real-time Monitoring System*")

# ======================================================
# SIDEBAR - INPUT & SETTINGS
# ======================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920277.png", width=100)
    st.markdown("## ⚙️ Pengaturan")
    
    sheet_url = st.text_input(
        "🔗 Link Google Spreadsheet",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxx/edit",
        help="Pastikan spreadsheet diatur ke 'Anyone with the link can view'"
    )
    
    # Ekstrak Sheet ID
    sheet_id = None
    if sheet_url:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if match:
            sheet_id = match.group(1)
    
    # Jika ada sheet_id, tampilkan pilihan sheet
    selected_sheets = []
    if sheet_id:
        try:
            # Fetch daftar sheet menggunakan Google Sheets API endpoint
            sheets_list_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
            
            st.markdown("---")
            st.markdown("### 📑 Pilih Sheet")
            
            # Input manual untuk nama sheet (karena kita tidak bisa list tanpa API key)
            sheet_input = st.text_area(
                "Masukkan nama sheet (pisahkan dengan enter untuk multiple sheets)",
                placeholder="Sheet1\nSheet2\nSheet3",
                help="Masukkan nama sheet persis seperti di Google Spreadsheet"
            )
            
            if sheet_input:
                selected_sheets = [s.strip() for s in sheet_input.split('\n') if s.strip()]
                st.success(f"✅ {len(selected_sheets)} sheet dipilih")
        except:
            pass
    
    st.markdown("---")
    load_btn = st.button("📥 Load Data", use_container_width=True)
    
    st.markdown("---")
    st.caption("⏱️ Auto refresh: 5 menit")
    st.caption("💡 Tip: Gunakan filter di halaman utama")

# ======================================================
# UTIL: CONVERT TO CSV
# ======================================================
def convert_to_csv_url(sheet_id: str, gid: str = "0") -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

def get_sheet_gid(sheet_url: str) -> dict:
    """Extract GID from URL if available"""
    gid_match = re.search(r"gid=(\d+)", sheet_url)
    return gid_match.group(1) if gid_match else "0"

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=REFRESH_INTERVAL)
def load_data(sheet_id, sheet_name=None, gid="0"):
    try:
        csv_url = convert_to_csv_url(sheet_id, gid)
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error loading sheet: {str(e)}")
        return None

# ======================================================
# MAIN LOGIC
# ======================================================
if not sheet_url:
    st.info("👈 Silakan masukkan link Google Spreadsheet di sidebar")
    st.stop()

if not load_btn and 'df_combined' not in st.session_state:
    st.warning("👈 Klik **Load Data** di sidebar untuk memulai")
    st.stop()

if load_btn or 'df_combined' in st.session_state:
    if load_btn:
        try:
            all_dfs = []
            
            if not selected_sheets:
                # Jika tidak ada sheet yang dipilih, load sheet default (gid=0)
                df = load_data(sheet_id, gid="0")
                if df is not None:
                    all_dfs.append(df)
            else:
                # Load multiple sheets
                progress_bar = st.progress(0)
                for idx, sheet_name in enumerate(selected_sheets):
                    st.caption(f"Loading: {sheet_name}...")
                    # Coba load dengan nama sheet
                    # Note: Untuk mendapatkan GID spesifik, user perlu menyediakannya
                    # Atau kita gunakan default gid untuk setiap sheet
                    df = load_data(sheet_id, sheet_name=sheet_name, gid=str(idx))
                    if df is not None:
                        df['_source_sheet'] = sheet_name  # Tambah kolom sumber
                        all_dfs.append(df)
                    progress_bar.progress((idx + 1) / len(selected_sheets))
            
            if all_dfs:
                df_combined = pd.concat(all_dfs, ignore_index=True)
                st.session_state['df_combined'] = df_combined
                st.success(f"✅ Data berhasil dimuat ({len(df_combined)} baris)")
            else:
                st.error("❌ Tidak ada data yang berhasil dimuat")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ Gagal memuat data: {str(e)}")
            st.stop()
    
    df = st.session_state['df_combined']
    
    # ======================================================
    # FIELD VALIDATION
    # ======================================================
    required_columns = [
        "Trans. ID", "Nama", "Jenjang", "Kabupaten", 
        "Propinsi", "Status", "Instalasi", "Selesai", 
        "Keterangan", "Petugas"
    ]
    
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        st.error(f"❌ Kolom tidak ditemukan: {', '.join(missing_cols)}")
        st.caption("Kolom yang tersedia: " + ", ".join(df.columns.tolist()))
        st.stop()
    
    # ======================================================
    # STATUS CALCULATION
    # ======================================================
    def categorize_status(val):
        val = str(val).upper()
        if "BAPP" in val or "KURANG" in val:
            return "Kurang BAPP"
        elif "PROSES" in val or "INSTALASI" in val:
            return "Sedang Diproses"
        elif "SELESAI" in val:
            return "Selesai"
        else:
            return "Belum Dikerjakan"
    
    df['Status_Category'] = df['Status'].apply(categorize_status)
    
    # ======================================================
    # METRICS CARDS
    # ======================================================
    st.markdown("## 📈 Ringkasan Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        belum = (df['Status_Category'] == 'Belum Dikerjakan').sum()
        st.metric(
            label="⚪ Belum Dikerjakan",
            value=belum,
            delta=f"{belum/len(df)*100:.1f}%"
        )
    
    with col2:
        kurang = (df['Status_Category'] == 'Kurang BAPP').sum()
        st.metric(
            label="🔵 Kurang BAPP",
            value=kurang,
            delta=f"{kurang/len(df)*100:.1f}%"
        )
    
    with col3:
        proses = (df['Status_Category'] == 'Sedang Diproses').sum()
        st.metric(
            label="🟡 Sedang Diproses",
            value=proses,
            delta=f"{proses/len(df)*100:.1f}%"
        )
    
    with col4:
        selesai = (df['Status_Category'] == 'Selesai').sum()
        st.metric(
            label="🟢 Selesai",
            value=selesai,
            delta=f"{selesai/len(df)*100:.1f}%"
        )
    
    # ======================================================
    # FILTER SECTION
    # ======================================================
    st.markdown("---")
    st.markdown("## 🔎 Filter Data")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        provinsi_options = sorted(df["Propinsi"].dropna().unique())
        provinsi_filter = st.multiselect(
            "📍 Provinsi",
            provinsi_options,
            default=provinsi_options
        )
    
    with col_f2:
        jenjang_options = sorted(df["Jenjang"].dropna().unique())
        jenjang_filter = st.multiselect(
            "🎓 Jenjang",
            jenjang_options,
            default=jenjang_options
        )
    
    with col_f3:
        status_options = ['Belum Dikerjakan', 'Kurang BAPP', 'Sedang Diproses', 'Selesai']
        status_filter = st.multiselect(
            "📊 Status",
            status_options,
            default=status_options
        )
    
    # Apply filters
    filtered_df = df[
        (df["Propinsi"].isin(provinsi_filter)) &
        (df["Jenjang"].isin(jenjang_filter)) &
        (df["Status_Category"].isin(status_filter))
    ]
    
    # ======================================================
    # DATA TABLE
    # ======================================================
    st.markdown("---")
    st.markdown(f"## 📋 Detail Monitoring ({len(filtered_df)} data)")
    
    # Status styling
    def status_style(val):
        val = str(val).upper()
        if "BAPP" in val or "KURANG" in val:
            return "background-color:#3b82f6;color:white;font-weight:600"
        elif "PROSES" in val or "INSTALASI" in val:
            return "background-color:#facc15;color:black;font-weight:600"
        elif "SELESAI" in val:
            return "background-color:#22c55e;color:white;font-weight:600"
        else:
            return "background-color:#e5e7eb;color:black;font-weight:600"
    
    # Display columns
    display_cols = required_columns.copy()
    if '_source_sheet' in filtered_df.columns:
        display_cols.insert(0, '_source_sheet')
    
    st.dataframe(
        filtered_df[display_cols].style.applymap(status_style, subset=["Status"]),
        use_container_width=True,
        height=500
    )
    
    # ======================================================
    # DOWNLOAD BUTTON
    # ======================================================
    st.markdown("---")
    col_dl1, col_dl2 = st.columns([3, 1])
    
    with col_dl2:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="monitoring_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # ======================================================
    # FOOTER
    # ======================================================
    st.markdown("---")
    st.caption("🚀 Powered by Streamlit | 📊 Dashboard Monitoring v2.0")
