import streamlit as st
import asyncio
import os

# AUTO-INSTALL PLAYWRIGHT BROWSER DI CLOUD SERVER
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

# --- KONFIGURASI TAMPILAN DASHBOARD MEWAH & RAPIH ---
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
    .request-card {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .request-card:hover {
        box-shadow: 0 6px 22px rgba(0,0,0,0.08);
        border-color: #CBD5E1;
    }
    .badge-new {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-rescore {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
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

# Inisialisasi Database Antrean Sesi Sementara
if "permintaan_konsumen" not in st.session_state:
    st.session_state.permintaan_konsumen = [
        {
            "id": 1, 
            "nama": "H. Ahmad Suyudi", 
            "unit_kerja": "BRI Unit Ciwaringin", 
            "layanan": "Rescoring (Skoring Ulang)", 
            "jumlah": 50,
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
    st.markdown("### 📋 Form Permintaan Layanan Konsumen")
    st.markdown("Silakan isi data nama, unit kerja, pilih jenis pengerjaan, dan jumlah pengguna yang diinginkan. Permintaan akan diproses setelah disetujui oleh **Operator Muhamad Roadi**.")
    
    with st.form("form_mandiri_konsumen"):
        col1, col2 = st.columns(2)
        with col1:
            nama_input = st.text_input("Nama Konsumen / Pemohon:", placeholder="Contoh: Budi Santoso")
            unit_kerja_input = st.text_input("Unit Kerja / Nama Mantri:", placeholder="Contoh: BRI Unit Ciwaringin / Mantri Ahmad")
        with col2:
            pilihan_layanan = st.selectbox(
                "Permintaan Pengerjaan:",
                ("Rescoring (Skoring Ulang)", "New Scoring (Pendaftaran Baru)")
            )
            jumlah_pengguna_input = st.number_input("Jumlah Pengguna:", min_value=1, max_value=200, value=50, step=1)
            
        url_tujuan_input = st.text_input(
            "URL Target LinkUMKM Mantri BRI:", 
            value="https://linkumkm.bri.co.id/umkmscore/mantri/175964",
            help="Masukkan link target mantri tempat data akan diproses."
        )
            
        submit_form = st.form_submit_button("📤 Kirim Permintaan ke Operator", type="primary", use_container_width=True)
        
        if submit_form:
            if nama_input and unit_kerja_input and url_tujuan_input:
                new_id = len(st.session_state.permintaan_konsumen) + 1
                st.session_state.permintaan_konsumen.append({
                    "id": new_id,
                    "nama": nama_input,
                    "unit_kerja": unit_kerja_input,
                    "layanan": pilihan_layanan,
                    "jumlah": int(jumlah_pengguna_input),
                    "url_target": url_tujuan_input,
                    "status": "Menunggu Persetujuan Operator"
                })
                st.success(f"✅ Berhasil! Permintaan dari **{nama_input}** ({pilihan_layanan} - {jumlah_pengguna_input} Pengguna) telah dikirim ke Operator Muhamad Roadi.")
            else:
                st.warning("⚠️ Mohon lengkapi Nama Konsumen, Unit Kerja, dan URL Target Mantri.")

# ==========================================
# 2. PORTAL OPERATOR (MUHAMAD ROADI)
# ==========================================
with tab_operator:
    if not st.session_state.operator_logged_in:
        # LOGIN SCREEN OPERATOR
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
        st.markdown("### 📥 Daftar Permintaan Pengerjaan dari Konsumen")
        st.markdown("Tinjau detail pengajuan konsumen di bawah ini. Eksekusi otomatisasi hanya berjalan setelah operator menyetujui.")
        
        if not st.session_state.permintaan_konsumen:
            st.info("Belum ada permintaan dari konsumen.")
        else:
            for idx, item in enumerate(st.session_state.permintaan_konsumen):
                # Tentukan badge warna berdasarkan jenis layanan
                badge_html = f'<span class="badge-new">{item["layanan"]}</span>' if "New" in item['layanan'] else f'<span class="badge-rescore">{item["layanan"]}</span>'
                
                # Tentukan warna status
                status_color = "#D97706" if item['status'] == "Menunggu Persetujuan Operator" else "#059669"
                
                # Render Kartu Rapi
                st.markdown(f"""
                    <div class="request-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                            <div>
                                <h3 style="margin: 0; color: #0A192F; font-size: 18px;">👤 {item['nama']}</h3>
                                <p style="margin: 3px 0 0 0; color: #64748B; font-size: 14px;">🏢 Unit Kerja: <b>{item['unit_kerja']}</b></p>
                            </div>
                            <div>
                                {badge_html}
                            </div>
                        </div>
                        <hr style="margin: 10px 0; border: none; border-top: 1px solid #F1F5F9;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px; color: #334155; margin-bottom: 15px;">
                            <div>👥 <b>Jumlah Pengguna:</b> <span style="background: #F1F5F9; padding: 2px 8px; border-radius: 6px; font-weight: bold;">{item['jumlah']} User</span></div>
                            <div>📌 <b>Status:</b> <span style="color: {status_color}; font-weight: bold;">{item['status']}</span></div>
                        </div>
                        <div style="font-size: 13px; color: #64748B; background: #F8FAFC; padding: 8px 12px; border-radius: 8px; word-break: break-all;">
                            🎯 <b>Target URL:</b> <a href="{item['url_target']}" target="_blank" style="color: #0284C7; text-decoration: none;">{item['url_target']}</a>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Tombol Aksi di Luar HTML agar Native Streamlit Bekerja Sempurna
                col_sp, col_btn = [st.columns([2.5, 1])[0], st.columns([2.5, 1])[1]]
                with col_btn:
                    if item['status'] == "Menunggu Persetujuan Operator":
                        if st.button(f"✅ Setujui & Jalankan", key=f"run_btn_{idx}", type="primary", use_container_width=True):
                            st.markdown("---")
                            st.markdown(f"### 📊 Live Eksekusi: {item['layanan']} ({item['jumlah']} Pengguna)")
                            
                            with st.status("⚡ Menjalankan Mesin Automation Playwright & OCR...", expanded=True) as status_box:
                                try:
                                    if "New Scoring" in item['layanan']:
                                        import NEWSCORINGPERFECT as target_script
                                    else:
                                        import RESCORINGPERFEC as target_script
                                        
                                    target_script.URL_TARGET = item['url_target']
                                    target_script.JUMLAH_PENGGUNA = item['jumlah']
                                    
                                    st.write(f"🤖 Memproses {item['jumlah']} pengguna untuk {item['nama']} ({item['unit_kerja']})...")
                                    asyncio.run(target_script.main())
                                    
                                    st.session_state.permintaan_konsumen[idx]['status'] = "✅ Selesai Diproses"
                                    status_box.update(label="✅ Eksekusi Berhasil Selesai Tuntas!", state="complete", expanded=False)
                                    st.success(f"🎉 Berhasil memproses {item['jumlah']} pengguna untuk konsumen {item['nama']}!")
                                    st.rerun()
                                except Exception as err:
                                    status_box.update(label="❌ Terjadi Kendala Saat Eksekusi", state="error", expanded=True)
                                    st.error(f"Error: {err}")
                    else:
                        st.markdown("<div style='text-align: right; color: #059669; font-weight: bold; padding-top: 5px;'>✅ Selesai Diproses</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
