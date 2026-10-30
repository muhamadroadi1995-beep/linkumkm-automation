import asyncio
import importlib
import io
import random
import re
import threading
import gc
from PIL import Image
from faker import Faker
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from playwright.async_api import async_playwright
import uvicorn

# --- OCR ENGINE CHECK ---
try:
    ddddocr = importlib.import_module("ddddocr")
    ocr_engine = ddddocr.DdddOcr(show_ad=False)
except Exception:
    ocr_engine = None

fake = Faker('id_ID')
DAFTAR_SEKTOR_USAHA = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

# --- GLOBAL STATE MANAGEMENT ---
state_global = {
    "status_proses": "IDLE",       # IDLE, PENDING_APPROVAL, RUNNING, PENDING_STOP, FINISHED, CANCELLED
    "mode_pilihan": "NEW_SCORING",  # NEW_SCORING / RESCORING
    "operator_nama": "MUHAMAD ROADI",
    "customer_nama": "",
    "target_url": "https://linkumkm.bri.co.id/umkmscore/mantri/",
    "target_jumlah": 30,
    "max_concurrent": 2,          # Optimal untuk Cloud Hosting Ringan (RAM 1-2GB)
    "tarif_per_entry": 1000,       # Tarif Flat Rp 1.000
    
    # --- PENGATURAN PILIHAN KONFIRMASI ---
    "auto_konfirmasi": True,     # True = Otomatis Eksekusi di Cloud
    
    # Counter Progres Pesanan Aktif
    "diproses": 0,
    "berhasil": 0,
    "gagal": 0,
    "list_proses": [],
    "list_berhasil": [],          # Menyimpan dict: {"nama":..., "email":..., "nik":..., "telepon":...}
    "logs": [],
    
    # QUEUE / ANTREAN PESANAN
    "antrean_pesanan": [],        # List dict
    "pesanan_aktif_id": None
}

event_tutup_browser = asyncio.Event()
event_stop_proses = asyncio.Event()
lock_queue = asyncio.Lock()

def add_log(message):
    state_global["logs"].append(message)
    if len(state_global["logs"]) > 200:
        state_global["logs"].pop(0)
    print(f"[LOG SERVER] {message}")

app = FastAPI()

# --- API ENDPOINTS ---
@app.get("/api/status")
def get_status():
    total = state_global["target_jumlah"]
    berhasil = state_global["berhasil"]
    pendapatan = berhasil * state_global["tarif_per_entry"]
    
    return {
        **state_global,
        "estimasi_pendapatan": pendapatan,
        "persentase": int((berhasil / total) * 100) if total > 0 else 0
    }

@app.post("/api/toggle-confirm")
async def toggle_confirm(request: Request):
    body = await request.json()
    status = bool(body.get("auto_konfirmasi", True))
    state_global["auto_konfirmasi"] = status
    mode_str = "OTOMATIS (Tanpa Konfirmasi Manual)" if status else "MANUAL"
    add_log(f"⚙️ Mode eksekusi diubah ke: {mode_str}")
    return {"status": "success", "message": f"Mode eksekusi diubah ke: {mode_str}"}

@app.post("/api/add-queue")
async def add_queue(request: Request):
    body = await request.json()
    customer = body.get("customer", "").strip() or "Umum"
    mode = body.get("mode", "NEW_SCORING")
    url = body.get("url", "https://linkumkm.bri.co.id/umkmscore/mantri/")
    jumlah = int(body.get("jumlah", 30))

    item_id = len(state_global["antrean_pesanan"]) + 1
    pesanan_baru = {
        "id": item_id,
        "customer": customer,
        "mode": mode,
        "url": url,
        "jumlah": jumlah,
        "status": "MENUNGGU"
    }

    async with lock_queue:
        state_global["antrean_pesanan"].append(pesanan_baru)

    add_log(f"📥 PESANAN BARU DITAMBAHKAN KE ANTREAN (#{item_id}): Klien {customer} ({jumlah} Data)")

    if state_global["status_proses"] in ["IDLE", "FINISHED", "CANCELLED"]:
        asyncio.create_task(jalankan_sistem_antrean())

    return {"status": "success", "message": f"Pesanan {customer} berhasil ditambahkan ke antrean!"}

@app.post("/api/cancel-queue/{queue_id}")
async def cancel_queue(queue_id: int):
    async with lock_queue:
        before_len = len(state_global["antrean_pesanan"])
        state_global["antrean_pesanan"] = [item for item in state_global["antrean_pesanan"] if not (item["id"] == queue_id and item["status"] == "MENUNGGU")]
        
        if len(state_global["antrean_pesanan"]) < before_len:
            add_log(f"❌ PESANAN #{queue_id} berhasil dihapus dari antrean.")
            return {"status": "success", "message": "Pesanan berhasil dihapus dari antrean."}
            
    return JSONResponse({"status": "error", "message": "Pesanan tidak dapat dihapus atau sedang diproses."}, status_code=400)

@app.post("/api/reset")
def reset_system():
    if state_global["status_proses"] in ["RUNNING", "PENDING_APPROVAL", "PENDING_STOP"]:
        return JSONResponse({
            "status": "error",
            "message": "⚠️ Tidak dapat meriset sistem saat proses sedang berjalan!"
        }, status_code=400)

    state_global["status_proses"] = "IDLE"
    state_global["diproses"] = 0
    state_global["berhasil"] = 0
    state_global["gagal"] = 0
    state_global["list_proses"] = []
    state_global["list_berhasil"] = []
    state_global["logs"] = []
    state_global["antrean_pesanan"] = [item for item in state_global["antrean_pesanan"] if item["status"] == "SELESAI"]
    state_global["pesanan_aktif_id"] = None
    
    event_stop_proses.clear()
    event_tutup_browser.clear()
    
    gc.collect()
    add_log("🔄 SISTEM DI-RESET: Antrean aktif dibersihkan.")
    return {"status": "success", "message": "Sistem berhasil di-reset!"}

@app.post("/api/close-browser")
def trigger_close_browser():
    if state_global["status_proses"] != "RUNNING":
        return JSONResponse({"status": "error", "message": "Sistem tidak sedang berjalan."}, status_code=400)
        
    state_global["status_proses"] = "CANCELLED"
    event_stop_proses.set()
    event_tutup_browser.set()
    add_log("🛑 PERINTAH STOP DITERIMA: Menghentikan otomatisasi...")
    return {"status": "success", "message": "Otomatisasi berhasil dihentikan."}

# --- PROCESS QUEUE ENGINE ---
async def jalankan_sistem_antrean():
    while True:
        pesanan_berikutnya = None
        async with lock_queue:
            for item in state_global["antrean_pesanan"]:
                if item["status"] == "MENUNGGU":
                    pesanan_berikutnya = item
                    break
        
        if not pesanan_berikutnya:
            state_global["status_proses"] = "IDLE"
            add_log("🏁 Seluruh antrean pesanan telah selesai diproses.")
            break

        async with lock_queue:
            pesanan_berikutnya["status"] = "DIPROSES"
            state_global["pesanan_aktif_id"] = pesanan_berikutnya["id"]

        state_global["customer_nama"] = pesanan_berikutnya["customer"]
        state_global["mode_pilihan"] = pesanan_berikutnya["mode"]
        state_global["target_url"] = pesanan_berikutnya["url"]
        state_global["target_jumlah"] = pesanan_berikutnya["jumlah"]
        state_global["tarif_per_entry"] = 1000

        state_global["berhasil"] = 0
        state_global["gagal"] = 0
        state_global["diproses"] = 0
        state_global["list_proses"] = []
        state_global["list_berhasil"] = []
        state_global["status_proses"] = "RUNNING"

        event_tutup_browser.clear()
        event_stop_proses.clear()

        await jalankan_otomatisasi_main()

        async with lock_queue:
            pesanan_berikutnya["status"] = "SELESAI"

# --- DASHBOARD UI ELECTRIC BLUE THEME ---
@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CLOUDHOSING DATA ENTRY - MANAGEMENT SYSTEM</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
        
        <style>
            :root {
                --bg-dark: #030a16;
                --card-bg: rgba(8, 24, 52, 0.75);
                --card-border: rgba(14, 165, 233, 0.25);
                --blue-primary: #0284c7;
                --blue-bright: #38bdf8;
                --blue-glow: rgba(56, 189, 248, 0.5);
                --cyan-neon: #00f0ff;
                --accent-green: #10B981;
                --accent-red: #EF4444;
                --accent-yellow: #F59E0B;
                --text-main: #FFFFFF;
                --text-muted: #94A3B8;
            }

            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            
            body {
                background-color: var(--bg-dark);
                color: var(--text-main);
                min-height: 100vh;
                position: relative;
                background-image: 
                    radial-gradient(circle at 15% 15%, rgba(14, 165, 233, 0.18) 0%, transparent 45%),
                    radial-gradient(circle at 85% 75%, rgba(0, 240, 255, 0.12) 0%, transparent 45%);
            }

            .wrapper { position: relative; z-index: 1; max-width: 1280px; margin: 0 auto; padding: 20px; }

            header {
                display: flex; justify-content: space-between; align-items: center;
                background: rgba(8, 24, 52, 0.85); backdrop-filter: blur(20px);
                border: 1px solid var(--card-border); padding: 18px 24px; border-radius: 20px;
                margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            }

            .header-title-container { display: flex; align-items: center; gap: 14px; }
            .header-icon {
                background: linear-gradient(135deg, var(--blue-primary), var(--blue-bright));
                color: #fff; font-weight: 800; font-size: 20px; padding: 10px 16px;
                border-radius: 14px; box-shadow: 0 0 20px var(--blue-glow);
            }
            .header-title h1 { font-size: 16px; font-weight: 800; color: #fff; }
            .header-title p { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

            .status-pill {
                display: inline-flex; align-items: center; gap: 8px;
                background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4);
                padding: 6px 14px; border-radius: 30px; font-size: 11px; font-weight: 700; color: var(--accent-green);
            }
            .status-pill.busy {
                background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.5); color: var(--accent-yellow);
            }
            .status-dot {
                width: 8px; height: 8px; border-radius: 50%; background: var(--accent-green);
                box-shadow: 0 0 10px var(--accent-green); animation: blink 1.5s infinite;
            }

            @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

            .main-grid { display: grid; grid-template-columns: 1fr; gap: 20px; }
            @media (min-width: 992px) { .main-grid { grid-template-columns: 380px 1fr; } }

            .card {
                background: var(--card-bg); border: 1px solid var(--card-border);
                border-radius: 20px; padding: 22px; backdrop-filter: blur(20px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            }

            .card-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 18px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06);
            }
            .card-title { font-size: 14px; font-weight: 800; display: flex; align-items: center; gap: 10px; color: #fff; }
            .card-title i { color: var(--blue-bright); }

            .form-group { margin-bottom: 14px; }
            label { font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; display: block; }
            input, select {
                width: 100%; padding: 12px 14px; border-radius: 12px;
                background: rgba(3, 10, 22, 0.75); border: 1px solid var(--card-border);
                color: #fff; font-size: 12px; font-weight: 600; outline: none;
            }
            input:focus, select:focus { border-color: var(--blue-bright); }

            .btn-container { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
            .btn-row { display: flex; gap: 10px; }
            .btn {
                flex: 1; padding: 12px 16px; border-radius: 12px; border: none; font-weight: 800;
                font-size: 12px; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 8px;
                transition: all 0.3s ease; text-decoration: none;
            }
            .btn-blue { background: linear-gradient(135deg, var(--blue-primary), var(--blue-bright)); color: #fff; }
            .btn-blue:hover { transform: translateY(-2px); filter: brightness(1.15); }
            .btn-reset { background: linear-gradient(135deg, #10B981, #059669); color: #fff; }
            .btn-danger { background: linear-gradient(135deg, #EF4444, #B91C1C); color: #fff; }

            .stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; }
            @media (min-width: 600px) { .stats-grid { grid-template-columns: repeat(4, 1fr); } }
            
            .stat-card {
                background: rgba(8, 24, 52, 0.65); border: 1px solid var(--card-border);
                border-radius: 16px; padding: 16px; text-align: center;
            }
            .stat-val { font-size: 22px; font-weight: 800; margin-top: 6px; }
            .stat-label { font-size: 10px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; }

            .progress-card { margin-bottom: 20px; }
            .progress-header { display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; margin-bottom: 8px; }
            .progress-track {
                height: 12px; background: rgba(255,255,255,0.05); border-radius: 20px; overflow: hidden;
                border: 1px solid rgba(255,255,255,0.08);
            }
            .progress-fill {
                height: 100%; width: 0%; background: linear-gradient(90deg, #0284c7, var(--blue-bright), var(--cyan-neon));
                border-radius: 20px; transition: width 0.5s ease-in-out;
            }

            .table-wrap {
                overflow-x: auto; max-height: 250px; border-radius: 12px;
                border: 1px solid var(--card-border); background: rgba(3, 10, 22, 0.4);
            }
            table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11px; }
            th {
                background: rgba(2, 132, 199, 0.25); color: #38bdf8; font-weight: 800;
                padding: 12px 14px; text-align: left; position: sticky; top: 0; backdrop-filter: blur(10px);
                border-bottom: 2px solid var(--card-border);
            }
            td { padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); color: #E2E8F0; }

            .badge { padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: 800; }
            .badge-waiting { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B; }
            .badge-running { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }
            .badge-done { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; }

            .log-box {
                height: 140px; overflow-y: auto; font-family: 'Consolas', monospace;
                font-size: 11px; background: rgba(0,0,0,0.6); border-radius: 12px; padding: 12px;
                display: flex; flex-direction: column; gap: 6px; border: 1px solid rgba(56,189,248,0.15);
            }
            .log-line { border-bottom: 1px solid rgba(255,255,255,0.02); padding-bottom: 4px; }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <header>
                <div class="header-title-container">
                    <div class="header-icon"><i class="fa-solid fa-cloud"></i></div>
                    <div class="header-title">
                        <h1>CLOUDHOST DATA ENTRY AUTOMATION<h1>
                        <p>Sistem referral otomatis terintegrasi cloud server 24/7</p>
                    </div>
                </div>
                <div>
                    <div class="status-pill" id="status-pill">
                        <span class="status-dot"></span>
                        <span id="lbl-status">STANDBY</span>
                    </div>
                </div>
            </header>

            <div class="main-grid">
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title"><i class="fa-solid fa-plus-circle"></i> Tambah Pesanan Baru</div>
                        </div>

                        <div class="form-group">
                            <label><i class="fa-solid fa-user-tie"></i> Nama Konsumen / Klien</label>
                            <input type="text" id="inp-customer" placeholder="Input Nama Customer...">
                        </div>

                        <div class="form-group">
                            <label><i class="fa-solid fa-gears"></i> Mode Otomatisasi</label>
                            <select id="inp-mode">
                                <option value="NEW_SCORING">NEW SCORING (1x Skoring)</option>
                                <option value="RESCORING">RESCORING (2x Skoring)</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label><i class="fa-solid fa-link"></i> URL Link Referral Target</label>
                            <input type="text" id="inp-url" value="https://linkumkm.bri.co.id/umkmscore/mantri/">
                        </div>

                        <div style="display: flex; gap: 10px;">
                            <div class="form-group" style="flex:1;">
                                <label><i class="fa-solid fa-bullseye"></i> Target (Data)</label>
                                <input type="number" id="inp-jumlah" value="30">
                            </div>
                            <div class="form-group" style="flex:1;">
                                <label><i class="fa-solid fa-tag"></i> Tarif / Data</label>
                                <input type="text" value="Rp 1.000" readonly>
                            </div>
                        </div>

                        <div class="btn-container">
                            <button class="btn btn-blue" onclick="addQueue()">
                                <i class="fa-solid fa-folder-plus"></i> TAMBAH KE ANTREAN
                            </button>
                            <div class="btn-row">
                                <button class="btn btn-danger" onclick="stopProcess()">
                                    <i class="fa-solid fa-stop"></i> STOP PROSES
                                </button>
                                <button class="btn btn-reset" onclick="resetTask()">
                                    <i class="fa-solid fa-rotate-right"></i> RESET ALL
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title"><i class="fa-solid fa-layer-group"></i> Antrean Pesanan Cloud</div>
                        </div>
                        <div class="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 45px; text-align: center;">#</th>
                                        <th>Nama Klien</th>
                                        <th>Metode</th>
                                        <th style="text-align: center;">Target</th>
                                        <th style="text-align: center;">Status</th>
                                        <th style="text-align: center;">Aksi</th>
                                    </tr>
                                </thead>
                                <tbody id="queue-table-body">
                                    <tr>
                                        <td colspan="6" style="text-align:center; color: var(--text-muted); padding: 15px;">
                                            Belum ada pesanan dalam antrean.
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Target Data</div>
                            <div class="stat-val" id="st-target">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Diproses</div>
                            <div class="stat-val" style="color: var(--blue-bright);" id="st-proses">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Berhasil</div>
                            <div class="stat-val" style="color: var(--accent-green);" id="st-sukses">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Estimasi Tagihan</div>
                            <div class="stat-val" style="color: var(--cyan-neon);" id="st-kas">Rp 0</div>
                        </div>
                    </div>

                    <div class="card progress-card">
                        <div class="progress-header">
                            <span>PROGRES SELESAI PESANAN AKTIF</span>
                            <span id="st-persen" style="color: var(--blue-bright);">0%</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill" id="progress-bar"></div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <div class="card-title"><i class="fa-solid fa-terminal"></i> Realtime Cloud Server Logs</div>
                        </div>
                        <div class="log-box" id="log-box"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function addQueue() {
                const customerVal = document.getElementById('inp-customer').value.trim();
                if (!customerVal) {
                    alert('Mohon isi Nama Customer / Klien terlebih dahulu!');
                    return;
                }

                const payload = {
                    customer: customerVal,
                    mode: document.getElementById('inp-mode').value,
                    url: document.getElementById('inp-url').value,
                    jumlah: document.getElementById('inp-jumlah').value
                };
                
                const res = await fetch('/api/add-queue', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                alert(data.message);
                document.getElementById('inp-customer').value = '';
            }

            async function cancelQueueItem(id) {
                if (confirm(`Hapus pesanan #${id} dari antrean?`)) {
                    const res = await fetch(`/api/cancel-queue/${id}`, { method: 'POST' });
                    const data = await res.json();
                    alert(data.message);
                }
            }

            async function stopProcess() {
                if (confirm('Hentikan proses otomatisasi saat ini?')) {
                    const res = await fetch('/api/close-browser', { method: 'POST' });
                    const data = await res.json();
                    alert(data.message);
                }
            }

            async function resetTask() {
                if (confirm('Reset seluruh status dan antrean aktif?')) {
                    const res = await fetch('/api/reset', { method: 'POST' });
                    const data = await res.json();
                    alert(data.message);
                }
            }

            function renderQueueTable(queueList) {
                const qBody = document.getElementById('queue-table-body');
                if (queueList && queueList.length > 0) {
                    qBody.innerHTML = queueList.map(q => {
                        let badgeClass = 'badge-waiting';
                        if (q.status === 'DIPROSES') badgeClass = 'badge-running';
                        if (q.status === 'SELESAI') badgeClass = 'badge-done';

                        const cancelBtn = (q.status === 'MENUNGGU') 
                            ? `<button onclick="cancelQueueItem(${q.id})" style="background:none; border:none; color:var(--accent-red); cursor:pointer;"><i class="fa-solid fa-trash"></i></button>` 
                            : `-`;

                        return `
                            <tr>
                                <td style="text-align:center; font-weight:bold;">#${q.id}</td>
                                <td style="font-weight:bold; color:#fff;">${q.customer}</td>
                                <td style="color:var(--cyan-neon); font-size:10px;">${q.mode}</td>
                                <td style="text-align:center; font-weight:bold;">${q.jumlah}</td>
                                <td style="text-align:center;"><span class="badge ${badgeClass}">${q.status}</span></td>
                                <td style="text-align:center;">${cancelBtn}</td>
                            </tr>
                        `;
                    }).join('');
                } else {
                    qBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 15px;">Belum ada pesanan dalam antrean.</td></tr>`;
                }
            }

            async function refreshDashboard() {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();

                    const statusPill = document.getElementById('status-pill');
                    const lblStatus = document.getElementById('lbl-status');

                    if (data.status_proses === 'RUNNING') {
                        statusPill.classList.add('busy');
                        lblStatus.innerText = 'SEDANG DIPROSES...';
                    } else {
                        statusPill.classList.remove('busy');
                        lblStatus.innerText = data.status_proses;
                    }

                    document.getElementById('st-target').innerText = data.target_jumlah;
                    document.getElementById('st-proses').innerText = data.diproses;
                    document.getElementById('st-sukses').innerText = data.berhasil;
                    document.getElementById('st-kas').innerText = 'Rp ' + data.estimasi_pendapatan.toLocaleString('id-ID');
                    document.getElementById('st-persen').innerText = data.persentase + '%';
                    document.getElementById('progress-bar').style.width = data.persentase + '%';

                    renderQueueTable(data.antrean_pesanan || []);

                    const logBox = document.getElementById('log-box');
                    logBox.innerHTML = data.logs.slice().reverse().map(l => `<div class="log-line">${l}</div>`).join('');
                } catch(e) {}
            }

            setInterval(refreshDashboard, 1000);
        </script>
    </body>
    </html>
    """

# --- ENGINE HELPER FUNCTIONS ---
def generate_single_user(user_id):
    nik_acak = '32' + str(random.randint(10, 99)) + ''.join([str(random.randint(0, 9)) for _ in range(12)])
    telepon_acak = '08' + str(random.randint(11, 99)) + ''.join([str(random.randint(0, 9)) for _ in range(8)])
    tanggal_lahir_acak = fake.date_of_birth(minimum_age=25, maximum_age=60).strftime('%Y-%m-%d')
    username_clean = re.sub(r'[^a-zA-Z0-9]', '', fake.first_name().lower())
    email_gmail = f"{username_clean}{random.randint(100000, 999999)}@gmail.com"

    return {
        "id": user_id,
        "nama": fake.name(),
        "email": email_gmail,
        "telepon": telepon_acak,
        "nik": nik_acak,
        "password": "Abcd123*",
        "tanggal_lahir": tanggal_lahir_acak,
        "sektor_usaha": random.choice(DAFTAR_SEKTOR_USAHA),
        "url": state_global["target_url"]
    }

async def solve_captcha_ai(page):
    try:
        captcha_img = page.locator("form img").first
        await captcha_img.wait_for(state="visible", timeout=6000)
        img_bytes = await captcha_img.screenshot()
        if ocr_engine:
            result = ocr_engine.classification(img_bytes)
            result_text = result.get("text", "") if isinstance(result, dict) else str(result)
            return re.sub(r'[^A-Z0-9]', '', result_text.upper())[:5].strip()
    except Exception:
        pass
    return ""

async def safe_click(page, locator, delay=1.2):
    try:
        await locator.scroll_into_view_if_needed()
        await locator.click(timeout=8000)
        await asyncio.sleep(delay)
        return True
    except Exception:
        return False

# --- LOGIKA OTOMATISASI UNTUK CLOUD (HEADLESS) ---
async def jalankan_per_pengguna(browser, user, semaphore):
    async with semaphore:
        if event_stop_proses.is_set():
            return False

        state_global["diproses"] += 1
        user_str = f"#{user['id']} - {user['nama']}"
        add_log(f"🔄 START ({state_global['mode_pilihan']}): {user_str}")

        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(user['url'], wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(1)

            await page.get_by_role("textbox", name="Masukkan nama anda").press_sequentially(user['nama'], delay=20)
            await page.get_by_role("textbox", name="Masukkan nomor telepon anda").press_sequentially(user['telepon'], delay=20)
            await page.get_by_placeholder("Masukkan Email anda").press_sequentially(user['email'], delay=20)
            await page.get_by_placeholder("Masukkan NIK anda").press_sequentially(user['nik'], delay=20)

            pass_field = page.locator("form").filter(has_text="Nama Lengkap Nomor Telepon").locator("input[name=\"password\"]")
            await pass_field.press_sequentially(user['password'], delay=20)
            await page.locator("input[name=\"password_retype\"]").press_sequentially(user['password'], delay=20)

            hasil_captcha = await solve_captcha_ai(page)
            if hasil_captcha:
                captcha_input = page.locator("input[name*='captcha' i]").first
                if await captcha_input.is_visible():
                    await captcha_input.fill(hasil_captcha)
            
            await safe_click(page, page.get_by_role("button", name="Daftar"), delay=3)

            tgl_input = page.get_by_placeholder("Masukkan Tanggal Lahir")
            await tgl_input.wait_for(state="visible", timeout=15000)
            await tgl_input.fill(user['tanggal_lahir'])

            sector_select = page.locator("select[name=\"business_sector\"]")
            await sector_select.select_option(user['sektor_usaha'])
            
            await page.locator("textarea[name=\"produced\"]").fill("ADA")
            await page.locator("textarea[name=\"business_address\"]").fill("ADA")

            dropdowns = [
                ("select[name=\"province\"]", "32"),
                ("select[name=\"regency\"]", "3209"),
                ("select[name=\"subdistrict\"]", "3209141"),
                ("select[name=\"village\"]", "3209141002"),
                ("select[name=\"postal_code\"]", "30282")
            ]
            for selector, val in dropdowns:
                await page.locator(selector).select_option(val)
                await asyncio.sleep(0.2)

            await page.get_by_role("radio", name="Tidak").check()
            await page.locator("#syarat").check()
            await safe_click(page, page.get_by_role("button", name="Lanjut"), delay=2)
            await safe_click(page, page.get_by_role("button", name="Saya Setuju"), delay=2)

            # SURVEY SKORING AWAL
            await safe_click(page, page.get_by_role("link", name="Mulai Skoring"), delay=2)
            await page.locator("label").filter(has_text="Kurang dari Rp100 juta/tahun").wait_for(state="visible", timeout=15000)
            
            await page.locator("label").filter(has_text="Kurang dari Rp100 juta/tahun").click()
            await safe_click(page, page.get_by_text("Di bawah atau sama dengan"))
            await safe_click(page, page.get_by_text("1 Orang"))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Tidak", exact=True).first)
            await safe_click(page, page.get_by_text("Tidak", exact=True).nth(1))
            await safe_click(page, page.get_by_text("Tidak", exact=True).nth(2))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Tidak", exact=True).first)
            await safe_click(page, page.get_by_text("Ya, Sebagian").nth(1))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Tidak, masih di satu provinsi"))
            await safe_click(page, page.get_by_text("Menggunakan media sosial ("))
            await safe_click(page, page.get_by_text("Ya, Sebagian").first)
            await safe_click(page, page.get_by_text("Ya, Sebagian").nth(1))
            await safe_click(page, page.get_by_text("Ya, Sebagian").nth(2))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Membuat prosedur tertulis"))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Ya", exact=True).first)
            await safe_click(page, page.get_by_text("Tidak", exact=True).nth(1))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Tidak", exact=True).first)
            await safe_click(page, page.get_by_text("Tidak, belum secara khusus"))
            await safe_click(page, page.get_by_text("Tidak", exact=True).nth(1))
            await safe_click(page, page.get_by_text("Tidak", exact=True).nth(2))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Belum memiliki dokumen"))
            await safe_click(page, page.get_by_text("NPWP atas nama badan usaha"))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Memastikan agar karyawan"))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Ya, tapi baru sebagian."))
            await safe_click(page, page.get_by_text("Tahu nama-nama atau merek"))
            await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.5)

            await safe_click(page, page.get_by_text("Belum ada prosedur khusus"))
            await safe_click(page, page.get_by_text("Belum ada prosedur atau tim"))
            await safe_click(page, page.get_by_text("Saldo cadangan kas usaha saya"))
            await safe_click(page, page.get_by_text("Akses internet yang handal ("))

            btn_hitung = page.get_by_role("link", name="Hitung Nilai Survey")
            await btn_hitung.wait_for(state="visible", timeout=20000)
            await safe_click(page, btn_hitung, delay=2)

            btn_hasil = page.get_by_role("link", name="Lihat Hasil Level UMKM Saya")
            await btn_hasil.wait_for(state="visible", timeout=20000)
            await safe_click(page, btn_hasil, delay=2)

            state_global["berhasil"] += 1
            state_global["list_berhasil"].append({
                "nama": user["nama"],
                "email": user["email"],
                "nik": user["nik"],
                "telepon": user["telepon"]
            })
            add_log(f"✅ SUKSES ({state_global['mode_pilihan']}): {user_str}")
            return True

        except Exception as e:
            add_log(f"⚠️ GAGAL: {user_str} - {str(e)[:50]}")
            return False
        finally:
            state_global["diproses"] -= 1
            try:
                await context.clear_cookies()
                await page.close()
                await context.close()
            except Exception:
                pass
            gc.collect()

async def jalankan_otomatisasi_main():
    semaphore = asyncio.Semaphore(state_global["max_concurrent"])
    next_id = 1
    
    async with async_playwright() as p:
        # Headless=True WAJIB untuk deployment di Cloud Server tanpa GUI
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        
        while state_global["berhasil"] < state_global["target_jumlah"] and not event_stop_proses.is_set():
            sisa_target = state_global["target_jumlah"] - state_global["berhasil"]
            users = [generate_single_user(next_id + i) for i in range(sisa_target)]
            next_id += sisa_target

            add_log(f"🚀 Memproses batch {len(users)} data...")
            tasks = [jalankan_per_pengguna(browser, usr, semaphore) for usr in users]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(2)

        if state_global["berhasil"] >= state_global["target_jumlah"]:
            state_global["status_proses"] = "FINISHED"
            add_log(f"🎉 PESANAN KLIEN {state_global['customer_nama']} SELESAI 100%!")
        
        await browser.close()
        gc.collect()

if __name__ == "__main__":
    # Jalankan server FastAPI langsung
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```eof

---

### Langkah Penyiapan & Cara Menjalankan di Cloudhost Cheap / VPS Murah

Agar program dapat berjalan **100% stabil di cloud hosting murah** (seperti VPS Ubuntu RAM 1GB / \$3-\$5 per bulan dari Biznet Gio, DigitalOcean, Hetzner, atau Linode):

#### 1. Persiapan Server VPS (Ubuntu 22.04 LTS / 24.04 LTS)
Masuk via SSH ke VPS Anda, lalu install dependensi dasar Python dan Chromium Playwright:

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install Python & Pip
sudo apt install -y python3-pip python3-venv ffmpeg libsm6 libxext6

# Clone atau buat folder aplikasi
mkdir app && cd app

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install library Python yang dibutuhkan
pip install fastapi uvicorn playwright faker pillow ddddocr

# Install browser Chromium headless pendukung Playwright beserta dependensi linuxnya
playwright install chromium
playwright install-deps