import streamlit as st
import asyncio
import os

# AUTO-INSTALL PLAYWRIGHT BROWSER DI CLOUD SERVER
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

# --- KONFIGURASI TAMPILAN DASHBOARD MEWAH ---
st.set_page_config(
    page_title="Portal Layanan LinkUMKM BRI", 
    page_icon="⚡", 
    layout="wide"
)

st.markdown("""
    <style>
    .main-banner {
        background: linear-gradient(135deg, #0A192F 0%, #172A45 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .card-box {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .login-box {
        max-width: 400px;
        margin: 40px auto;
        padding: 30px;
        background: #ffffff;
        border-radius: 14px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Database Antrean Sesi Sementara (Session State)
if "permintaan_konsumen" not in st.session_state:
    st.session_state.permintaan_konsumen = [
        {
            "id": 1, 
            "nama": "H. Ahmad Suyudi", 
            "telepon": "081234567890", 
            "sektor": "1", 
            "layanan": "New Scoring (Pendaftaran Baru)", 
            "url_target": "https://linkumkm.bri.co.id/umkmscore/mantri/175964",
            "status": "Menunggu Persetujuan Operator"
        }
    ]

if "operator_logged_in" not in st.session_state:
    st.session_state.operator_logged_in = False

# --- HEADER UTAMA ---
st.markdown("""
    <div class="main-banner">
        <h1 style="margin:0; font-size: 28px; font-weight: 700;">⚡ Portal Layanan & Otomatisasi LinkUMKM BRI</h1>
        <p style="margin:6px 0 0 0; opacity: 0.8; font-size: 14px;">Pengajuan Mandiri Konsumen & Verifikasi Eksekutif Operator (Muhamad Roadi)</p>
    </div>
""", unsafe_allow_html=True)

# NAVIGASI TAB UTAMA
tab_konsumen, tab_operator = st.tabs(["📝 Form Pendaftaran Konsumen", "🔐 Portal Operator (Muhamad Roadi)"])

# ==========================================
# 1. FORM PENDAFTARAN KONSUMEN
# ==========================================
with tab_konsumen:
    st.markdown("### 📋 Pengajuan Layanan Otomatisasi LinkUMKM")
    st.markdown("Silakan isi data Anda, pilih jenis layanan yang diinginkan, dan masukkan URL Mantri BRI tujuan Anda. Data akan masuk ke sistem dan **h akan diproses setelah disetujui oleh Operator**.")
    
    with st.form("form_mandiri_konsumen"):
        col1, col2 = st.columns(2)
        with col1:
            nama_input = st.text_input("Nama Lengkap Usaha/Konsumen:")
            telepon_input = st.text_input("Nomor WhatsApp/Telepon Aktif:")
            sektor_input = st.selectbox(
                "Sektor Usaha:",
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                format_func=lambda x: f"Sektor Kategori {x}"
            )
        with col2:
            pilihan_layanan = st.selectbox(
                "Pilih Jenis Pengerjaan:",
                ("New Scoring (Pendaftaran Baru)", "Rescoring (Skoring Ulang)")
            )
            url_tujuan_konsumen = st.text_input(
                "URL Target Mantri BRI Tujuan:", 
                value="https://linkumkm.bri.co.id/umkmscore/mantri/175964",
                help="Masukkan link/URL mantri BRI tempat data Anda akan masuk."
            )
            
        submit_form = st.form_submit_button("📤 Kirim Permintaan ke Operator", type="primary", use_container_width=True)
        
        if submit_form:
            if nama_input and telepon_input and url_tujuan_konsumen:
                new_id = len(st.session_state.permintaan_konsumen) + 1
                st.session_state.permintaan_konsumen.append({
                    "id": new_id,
                    "nama": nama_input,
                    "telepon": telepon_input,
                    "sektor": sektor_input,
                    "layanan": pilihan_layanan,
                    "url_target": url_tujuan_konsumen,
                    "status": "Menunggu Persetujuan Operator"
                })
                st.success(f"✅ Berhasil! Permintaan atas nama **{nama_input}** ({pilihan_layanan}) telah dikirim. Menunggu persetujuan Operator Muhamad Roadi.")
            else:
                st.warning("⚠️ Mohon lengkapi Nama, Nomor Telepon, dan URL Target Mantri.")

# ==========================================
# 2. PORTAL OPERATOR (MUHAMAD ROADI)
# ==========================================
with tab_operator:
    if not st.session_state.operator_logged_in:
        # LOGIN SCREEN
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1.2, 1])
        with c2:
            st.markdown("""
                <div class="login-box">
                    <h3 style="text-align: center; color: #0A192F; margin-bottom: 5px;">🔐 Login Operator</h3>
                    <p style="text-align: center; color: #646b74; font-size: 13px; margin-bottom: 20px;">Otorisasi Khusus: Muhamad Roadi</p>
            """, unsafe_allow_html=True)
            
            u_name = st.text_input("Nama Pengguna:")
            p_pass = st.text_input("Kata Sandi:", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Masuk Dashboard", type="primary", use_container_width=True):
                if u_name == "Muhamad Roadi" and p_pass == "13Mei2022":
                    st.session_state.operator_logged_in = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("❌ Nama pengguna atau sandi salah!")
            st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        # DASHBOARD UTAMA OPERATOR
        top_c1, top_c2 = st.columns([4, 1])
        with top_c1:
            st.markdown("### 🛡️ Panel Kendali & Persetujuan Operator")
            st.write("Operator Aktif: **Muhamad Roadi** | Bank BRI AWN 2")
        with top_c2:
            if st.button("🚪 Keluar", use_container_width=True):
                st.session_state.operator_logged_in = False
                st.rerun()
                
        st.markdown("---")
        st.markdown("### 📥 Daftar Permintaan Layanan Masuk dari Konsumen")
        st.markdown("Setiap baris konsumen memiliki **Target URL** dan **Jenis Layanan** pilihannya masing-masing. Sistem otomatisasi hanya akan berjalan jika operator menekan tombol **Setujui & Jalankan**.")
        
        if not st.session_state.permintaan_konsumen:
            st.info("Belum ada permintaan dari konsumen.")
        else:
            for idx, item in enumerate(st.session_state.permintaan_konsumen):
                with st.container():
                    st.markdown(f"""
                        <div style="background: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 10px;">
                            <b>👤 Konsumen:</b> {item['nama']} ({item['telepon']})<br>
                            <b>⚙️ Layanan:</b> <span style="color: #003366; font-weight: bold;">{item['layanan']}</span><br>
                            <b>🎯 Target URL:</b> <a href="{item['url_target']}" target="_blank">{item['url_target']}</a><br>
                            <b>📌 Status:</b> <i>{item['status']}</i>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Aksi Persetujuan Eksekusi Langsung per Konsumen
                    col_act1, col_act2 = st.columns([2, 1])
                    with col_act1:
                        st.write("") # Spacer
                    with col_act2:
                        if item['status'] == "Menunggu Persetujuan Operator":
                            if st.button("✅ Setujui & Jalankan", key=f"run_btn_{idx}", type="primary", use_content_width=True):
                                st.markdown("---")
                                st.markdown(f"### 📊 Live Eksekusi untuk: {item['nama']}")
                                
                                with st.status("⚡ Menjalankan Mesin Automation...", expanded=True) as status_box:
                                    try:
                                        if "New Scoring" in item['layanan']:
                                            import NEWSCORINGPERFECT as target_script
                                        else:
                                            import RESCORINGPERFEC as target_script
                                            
                                        # Set target sesuai pilihan konsumen tersebut
                                        target_script.URL_TARGET = item['url_target']
                                        target_script.JUMLAH_PENGGUNA = 1 # Diproses 1 per 1 sesuai data konsumen
                                        
                                        st.write(f"🤖 Memproses data atas nama {item['nama']}...")
                                        asyncio.run(target_script.main())
                                        
                                        st.session_state.permintaan_konsumen[idx]['status'] = "✅ Selesai Diproses"
                                        status_box.update(label="✅ Eksekusi Berhasil Selesai!", state="complete", expanded=False)
                                        st.success(f"🎉 Data {item['nama']} sukses diproses!")
                                        st.rerun()
                                    except Exception as err:
                                        status_box.update(label="❌ Terjadi Kendala", state="error", expanded=True)
                                        st.error(f"Error: {err}")
                        else:
                            st.success("Status: Selesai / Telah Dieksekusi")
                
                st.markdown("---")
