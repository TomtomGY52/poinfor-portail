import os
import json
import uuid
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Portail POINFOR x GTLA", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
JOBS_FILE = DATA_DIR / "jobs.json"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
if not JOBS_FILE.exists():
    JOBS_FILE.write_text("[]", encoding="utf-8")

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "gtla-poinfor-secret-2026")

def get_jobs():
    try:
        return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_jobs(jobs):
    JOBS_FILE.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")

def check_auth(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante."
        )

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>POINFOR - Tri & Validation IA des Dossiers Stagiaires</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      color: #334155;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .container {
      width: 100%;
      max-width: 640px;
      background: #ffffff;
      border-radius: 20px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .header {
      background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
      padding: 30px 25px;
      color: #ffffff;
      text-align: center;
      position: relative;
    }
    .logo-container {
      background: #ffffff;
      padding: 8px 18px;
      border-radius: 12px;
      display: inline-block;
      margin-bottom: 14px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    }
    .logo-img {
      height: 48px;
      width: auto;
      display: block;
      object-fit: contain;
    }
    .badge-env {
      display: inline-block;
      background: rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(8px);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.5px;
      margin-bottom: 12px;
      text-transform: uppercase;
    }
    .header h1 {
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
    }
    .header p {
      font-size: 13px;
      color: #bfdbfe;
      line-height: 1.5;
    }
    .content {
      padding: 35px 30px;
    }
    .form-group {
      margin-bottom: 22px;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 8px;
    }
    .input-text {
      width: 100%;
      padding: 14px 16px;
      border: 1.5px solid #e2e8f0;
      border-radius: 12px;
      font-size: 14px;
      font-family: inherit;
      color: #1e293b;
      transition: all 0.2s;
      outline: none;
    }
    .input-text:focus {
      border-color: #2563eb;
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }
    .drop-zone {
      border: 2px dashed #cbd5e1;
      border-radius: 14px;
      padding: 35px 20px;
      text-align: center;
      background: #f8fafc;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }
    .drop-zone:hover, .drop-zone.dragover {
      border-color: #2563eb;
      background: #eff6ff;
    }
    .drop-zone-icon {
      font-size: 40px;
      margin-bottom: 10px;
      display: block;
    }
    .drop-zone-text {
      font-size: 14px;
      font-weight: 600;
      color: #334155;
      margin-bottom: 4px;
    }
    .drop-zone-hint {
      font-size: 12px;
      color: #64748b;
    }
    .file-input {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      opacity: 0;
      cursor: pointer;
    }
    .selected-file {
      display: none;
      margin-top: 12px;
      padding: 10px 14px;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      border-radius: 10px;
      font-size: 13px;
      color: #065f46;
      font-weight: 500;
      align-items: center;
      justify-content: space-between;
    }
    .btn-submit {
      width: 100%;
      padding: 16px;
      background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
      color: #ffffff;
      border: none;
      border-radius: 12px;
      font-size: 15px;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }
    .btn-submit:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(37, 99, 235, 0.4);
    }
    .btn-submit:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .features-list {
      margin-top: 25px;
      padding-top: 20px;
      border-top: 1px solid #f1f5f9;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      font-size: 12px;
      color: #64748b;
    }
    .features-list span {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .success-screen {
      display: none;
      text-align: center;
      padding: 30px 15px;
    }
    .success-icon {
      width: 70px;
      height: 70px;
      background: #ecfdf5;
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 34px;
      margin-bottom: 18px;
    }
    .success-screen h3 {
      font-size: 20px;
      color: #065f46;
      margin-bottom: 10px;
    }
    .success-screen p {
      font-size: 14px;
      color: #475569;
      line-height: 1.6;
      margin-bottom: 20px;
    }
    .success-details {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 16px;
      text-align: left;
      font-size: 13px;
      color: #334155;
    }
    .progress-bar-container {
      display: none;
      width: 100%;
      height: 8px;
      background: #e2e8f0;
      border-radius: 4px;
      margin-top: 15px;
      overflow: hidden;
    }
    .progress-bar-fill {
      width: 0%;
      height: 100%;
      background: #2563eb;
      transition: width 0.3s;
    }
    .spinner {
      display: none;
      width: 20px;
      height: 20px;
      border: 2px solid #ffffff;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
</head>
<body>

  <div class="container">
    <div class="header">
      <div class="logo-container">
        <img class="logo-img" src="https://static.wixstatic.com/media/b1b8ab_d6d685da76e246f19fb15f1960691ca0~mv2.jpg/v1/fit/w_2500,h_1330,al_c/b1b8ab_d6d685da76e246f19fb15f1960691ca0~mv2.jpg" alt="Logo POINFOR">
      </div>
      <div>
        <span class="badge-env">POINFOR Formation • IA de Contrôle</span>
      </div>
      <h1>Plateforme de Tri & Validation des Dossiers Stagiaires</h1>
      <p>Déposez vos dossiers de formation (archive .zip) pour classification automatique, redressement des scans, vérification des signatures par Vision IA et génération des livrables.</p>
    </div>

    <div class="content" id="formContainer">
      <form id="uploadForm" enctype="multipart/form-data">
        <div class="form-group">
          <label for="email">Votre adresse email professionnelle (réception des livrables) *</label>
          <input type="email" id="email" name="email" class="input-text" placeholder="prenom.nom@poinfor.fr ou @gtla.fr" required>
        </div>

        <div class="form-group">
          <label>Dossier compressé des stagiaires (.zip) *</label>
          <div class="drop-zone" id="dropZone">
            <span class="drop-zone-icon">📁</span>
            <div class="drop-zone-text">Glissez-déposez votre archive ZIP ici</div>
            <div class="drop-zone-hint">ou cliquez pour sélectionner sur votre ordinateur</div>
            <input type="file" id="zipfile" name="zipfile" class="file-input" accept=".zip" required>
          </div>
          <div class="selected-file" id="selectedFile">
            <span id="fileName">mon_archive.zip</span>
            <span id="fileSize" style="color: #64748b; font-size: 12px;"></span>
          </div>
          <div class="progress-bar-container" id="progressContainer">
            <div class="progress-bar-fill" id="progressBar"></div>
          </div>
        </div>

        <button type="submit" class="btn-submit" id="submitBtn">
          <span class="spinner" id="spinner"></span>
          <span id="btnText">🚀 Transmettre le dossier pour analyse IA</span>
        </button>
      </form>

      <div class="features-list">
        <span>🔄 Redressement auto des scans (0°, 90°, 180°)</span>
        <span>🧠 Modèle IA local Qwen 2.5 7B</span>
        <span>✍️ Contrôle des signatures par Vision IA</span>
        <span>📊 Tableur Excel & Archive ZIP par email</span>
      </div>
    </div>

    <!-- Écran de confirmation après envoi -->
    <div class="content success-screen" id="successScreen">
      <div class="success-icon">✅</div>
      <h3>Dossier transmis avec succès !</h3>
      <p>
        Votre archive de stagiaires a bien été réceptionnée sur la plateforme sécurisée. Le moteur d'intelligence artificielle locale procède au redressement, à la classification et au contrôle minutieux des signatures manuscrites.
      </p>
      <div class="success-details">
        <p style="margin-bottom: 6px;"><strong>📬 Email de notification :</strong> <span id="targetEmail" style="color: #2563eb;"></span></p>
        <p style="margin-bottom: 6px;"><strong>📦 Livrables qui vous seront expédiés :</strong></p>
        <ul style="padding-left: 20px; line-height: 1.6; color: #64748b;">
          <li>Tableau Excel complet (Journal de tri & Matrice avec formules dynamiques).</li>
          <li>Archive ZIP avec tous les dossiers stagiaires classés et documents redressés.</li>
          <li>Rapport visuel HTML complet avec le détail des pièces manquantes.</li>
        </ul>
      </div>
      <button onclick="window.location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #e2e8f0; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; color: #334155;">
        Déposer un autre dossier
      </button>
    </div>
  </div>

  <script>
    const fileInput = document.getElementById('zipfile');
    const dropZone = document.getElementById('dropZone');
    const selectedFile = document.getElementById('selectedFile');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnText');
    const formContainer = document.getElementById('formContainer');
    const successScreen = document.getElementById('successScreen');
    const targetEmail = document.getElementById('targetEmail');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        fileName.textContent = '📄 ' + file.name;
        fileSize.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' Mo';
        selectedFile.style.display = 'flex';
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, e => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, e => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
      });
    });

    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const file = fileInput.files[0];

      if (!file) {
        alert('Veuillez sélectionner une archive ZIP.');
        return;
      }

      submitBtn.disabled = true;
      spinner.style.display = 'inline-block';
      btnText.textContent = 'Téléversement en cours...';
      progressContainer.style.display = 'block';

      const formData = new FormData();
      formData.append('email', email);
      formData.append('zipfile', file);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/upload', true);

      xhr.upload.onprogress = function(evt) {
        if (evt.lengthComputable) {
          const percent = Math.round((evt.loaded / evt.total) * 100);
          progressBar.style.width = percent + '%';
          btnText.textContent = 'Téléversement : ' + percent + '%';
        }
      };

      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
          targetEmail.textContent = email;
          formContainer.style.display = 'none';
          successScreen.style.display = 'block';
        } else {
          alert("Erreur lors de la transmission du dossier : " + xhr.responseText);
          submitBtn.disabled = false;
          spinner.style.display = 'none';
          btnText.textContent = "🚀 Transmettre le dossier pour analyse IA";
          progressContainer.style.display = 'none';
        }
      };

      xhr.onerror = function() {
        alert("Erreur réseau lors de l'envoi.");
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = "🚀 Transmettre le dossier pour analyse IA";
        progressContainer.style.display = 'none';
      };

      xhr.send(formData);
    });
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/upload")
async def upload_file(email: str = Form(...), zipfile: UploadFile = File(...)):
    if not zipfile.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .zip sont autorisés.")
    
    job_id = str(uuid.uuid4())[:8]
    safe_filename = f"{job_id}_{Path(zipfile.filename).name}"
    target_path = UPLOADS_DIR / safe_filename

    contents = await zipfile.read()
    target_path.write_bytes(contents)

    jobs = get_jobs()
    job_data = {
        "job_id": job_id,
        "email": email.strip(),
        "original_filename": zipfile.filename,
        "stored_filename": safe_filename,
        "file_size_bytes": len(contents),
        "status": "PENDING",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    jobs.append(job_data)
    save_jobs(jobs)

    return JSONResponse(content={
        "success": True,
        "job_id": job_id,
        "message": "Dossier enregistré avec succès dans la file d'attente de traitement."
    })

# API Sécurisée pour l'agent IA Local sur votre PC
@app.get("/api/jobs/pending")
def list_pending_jobs(x_api_key: str = Header(None)):
    check_auth(x_api_key)
    jobs = get_jobs()
    pending = [j for j in jobs if j.get("status") == "PENDING"]
    return JSONResponse(content={"pending_jobs": pending})

@app.get("/api/jobs/{job_id}/download")
def download_job_file(job_id: str, x_api_key: str = Header(None)):
    check_auth(x_api_key)
    jobs = get_jobs()
    target_job = next((j for j in jobs if j["job_id"] == job_id), None)
    if not target_job:
        raise HTTPException(status_code=404, detail="Dossier non trouvé.")
    
    file_path = UPLOADS_DIR / target_job["stored_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier physique introuvable.")
    
    return FileResponse(
        path=str(file_path),
        filename=target_job["original_filename"],
        media_type="application/zip"
    )

@app.post("/api/jobs/{job_id}/status")
def update_job_status(job_id: str, payload: dict, x_api_key: str = Header(None)):
    check_auth(x_api_key)
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Statut manquant.")
    
    jobs = get_jobs()
    updated = False
    for j in jobs:
        if j["job_id"] == job_id:
            j["status"] = new_status
            j["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Dossier introuvable.")
    
    save_jobs(jobs)
    return JSONResponse(content={"success": True, "job_id": job_id, "new_status": new_status})
