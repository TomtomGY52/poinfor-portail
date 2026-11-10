import os
import json
import uuid
import time
import zipfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Portail POINFOR x GTLA", version="2.0.0")

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
      max-width: 680px;
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
      border-radius: 16px;
      padding: 30px 20px;
      text-align: center;
      background: #f8fafc;
      transition: all 0.2s ease;
      position: relative;
    }
    .drop-zone.dragover {
      border-color: #2563eb;
      background: #eff6ff;
      transform: scale(1.01);
    }
    .drop-zone-icon {
      font-size: 42px;
      margin-bottom: 10px;
      display: block;
    }
    .drop-zone-text {
      font-size: 15px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 4px;
    }
    .drop-zone-hint {
      font-size: 12px;
      color: #64748b;
      margin-bottom: 16px;
    }
    .drop-zone-buttons {
      display: flex;
      gap: 12px;
      justify-content: center;
      flex-wrap: wrap;
    }
    .btn-select {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid transparent;
    }
    .btn-select-file {
      background: #eff6ff;
      color: #1d4ed8;
      border-color: #bfdbfe;
    }
    .btn-select-file:hover {
      background: #dbeafe;
      border-color: #93c5fd;
    }
    .btn-select-folder {
      background: #f5f3ff;
      color: #6d28d9;
      border-color: #ddd6fe;
    }
    .btn-select-folder:hover {
      background: #ede9fe;
      border-color: #c4b5fd;
    }
    .selected-summary {
      display: none;
      margin-top: 14px;
      padding: 14px 18px;
      background: #ecfdf5;
      border: 1.5px solid #a7f3d0;
      border-radius: 12px;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .summary-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .summary-icon {
      font-size: 26px;
      flex-shrink: 0;
    }
    .summary-title {
      font-size: 13px;
      font-weight: 700;
      color: #065f46;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 380px;
    }
    .summary-details {
      font-size: 12px;
      color: #047857;
      margin-top: 2px;
    }
    .btn-remove {
      background: transparent;
      border: 1px solid #fecaca;
      background: #fef2f2;
      color: #dc2626;
      font-size: 12px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.2s;
    }
    .btn-remove:hover {
      background: #fee2e2;
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
      margin-top: 10px;
    }
    .btn-submit:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(37, 99, 235, 0.4);
    }
    .btn-submit:disabled {
      opacity: 0.6;
      cursor: not-allowed;
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
      <p>Déposez vos documents de formation (fichiers PDF, scans multi-pages, dossiers complets ou archives .ZIP) pour analyse, redressement, dissociation et contrôle des signatures par Vision IA.</p>
    </div>

    <div class="content" id="formContainer">
      <form id="uploadForm">
        <div class="form-group">
          <label for="email">Votre adresse email professionnelle (réception des livrables) *</label>
          <input type="email" id="email" name="email" class="input-text" placeholder="prenom.nom@poinfor.fr ou @gtla.fr" required>
        </div>

        <div class="form-group">
          <label>Dossiers ou documents à analyser (PDF, Dossier ou ZIP) *</label>
          <div class="drop-zone" id="dropZone">
            <span class="drop-zone-icon">📂</span>
            <div class="drop-zone-text">Glissez-déposez vos fichiers ou dossiers ici</div>
            <div class="drop-zone-hint">Compatible scans PDF (mono ou multi-pages), dossiers complets et archives .ZIP</div>

            <div class="drop-zone-buttons">
              <button type="button" class="btn-select btn-select-file" id="btnPickFiles">
                <span>📄</span> Sélectionner des fichiers (PDF / ZIP)
              </button>
              <button type="button" class="btn-select btn-select-folder" id="btnPickFolder">
                <span>📁</span> Sélectionner un dossier complet
              </button>
            </div>

            <!-- Inputs cachés -->
            <input type="file" id="filesInput" multiple accept=".pdf,.zip" style="display: none;">
            <input type="file" id="folderInput" webkitdirectory directory multiple style="display: none;">
          </div>

          <div class="selected-summary" id="selectedSummary">
            <div class="summary-left">
              <span class="summary-icon" id="summaryIcon">📄</span>
              <div>
                <div class="summary-title" id="summaryTitle">Fichier sélectionné</div>
                <div class="summary-details" id="summaryDetails">0 Mo</div>
              </div>
            </div>
            <button type="button" class="btn-remove" id="btnRemove">✕ Retirer</button>
          </div>

          <div class="progress-bar-container" id="progressContainer">
            <div class="progress-bar-fill" id="progressBar"></div>
          </div>
        </div>

        <button type="submit" class="btn-submit" id="submitBtn">
          <span class="spinner" id="spinner"></span>
          <span id="btnText">🚀 Transmettre pour analyse & tri IA</span>
        </button>
      </form>

      <div class="features-list">
        <span>🔄 Redressement auto des scans (0°, 90°, 180°)</span>
        <span>✂️ Découpage & fusion automatique par stagiaire</span>
        <span>🧠 Modèle IA local Qwen 2.5 7B</span>
        <span>✍️ Contrôle des signatures par Vision IA</span>
        <span>📊 Tableur Excel & Archive ZIP par email</span>
        <span>🔒 Traitement 100% sécurisé et souverain</span>
      </div>
    </div>

    <!-- Écran de confirmation après envoi -->
    <div class="content success-screen" id="successScreen">
      <div class="success-icon">✅</div>
      <h3>Documents transmis avec succès !</h3>
      <p>
        Vos documents ont bien été réceptionnés sur la plateforme sécurisée. Le moteur d'intelligence artificielle locale procède au redressement, à la dissociation des scans volumineux, à la classification et au contrôle des signatures manuscrites.
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
        Déposer d'autres documents
      </button>
    </div>
  </div>

  <script>
    const dropZone = document.getElementById('dropZone');
    const filesInput = document.getElementById('filesInput');
    const folderInput = document.getElementById('folderInput');
    const btnPickFiles = document.getElementById('btnPickFiles');
    const btnPickFolder = document.getElementById('btnPickFolder');
    const selectedSummary = document.getElementById('selectedSummary');
    const summaryIcon = document.getElementById('summaryIcon');
    const summaryTitle = document.getElementById('summaryTitle');
    const summaryDetails = document.getElementById('summaryDetails');
    const btnRemove = document.getElementById('btnRemove');
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnText');
    const formContainer = document.getElementById('formContainer');
    const successScreen = document.getElementById('successScreen');
    const targetEmail = document.getElementById('targetEmail');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');

    // Liste des fichiers prêts à être envoyés : [{ file: File, path: string }]
    let collectedItems = [];

    btnPickFiles.addEventListener('click', (e) => {
      e.stopPropagation();
      filesInput.click();
    });

    btnPickFolder.addEventListener('click', (e) => {
      e.stopPropagation();
      folderInput.click();
    });

    filesInput.addEventListener('change', () => {
      if (filesInput.files && filesInput.files.length > 0) {
        const items = [];
        for (let i = 0; i < filesInput.files.length; i++) {
          const f = filesInput.files[i];
          items.push({ file: f, path: f.name });
        }
        setSelection(items);
      }
    });

    folderInput.addEventListener('change', () => {
      if (folderInput.files && folderInput.files.length > 0) {
        const items = [];
        for (let i = 0; i < folderInput.files.length; i++) {
          const f = folderInput.files[i];
          items.push({ file: f, path: f.webkitRelativePath || f.name });
        }
        setSelection(items);
      }
    });

    btnRemove.addEventListener('click', () => {
      clearSelection();
    });

    function formatSize(bytes) {
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
      return (bytes / (1024 * 1024)).toFixed(2) + ' Mo';
    }

    function clearSelection() {
      collectedItems = [];
      filesInput.value = '';
      folderInput.value = '';
      selectedSummary.style.display = 'none';
    }

    function setSelection(items) {
      // Filtrer les fichiers indésirables système (.DS_Store, Thumbs.db, etc.)
      const filtered = items.filter(it => {
        const p = it.path;
        return !p.includes('.DS_Store') && !p.includes('Thumbs.db') && !p.includes('__MACOSX');
      });

      if (!filtered.length) {
        alert("Aucun document valide n'a été détecté.");
        clearSelection();
        return;
      }

      collectedItems = filtered;
      const totalBytes = collectedItems.reduce((acc, it) => acc + (it.file.size || 0), 0);
      const count = collectedItems.length;

      // Détecter la nature de la sélection
      const hasZip = collectedItems.some(it => it.file.name.toLowerCase().endsWith('.zip'));
      const hasFolder = collectedItems.some(it => it.path.includes('/'));

      if (count === 1 && hasZip) {
        summaryIcon.textContent = '📦';
        summaryTitle.textContent = collectedItems[0].file.name;
        summaryDetails.textContent = 'Archive ZIP compressée • ' + formatSize(totalBytes);
      } else if (hasFolder) {
        summaryIcon.textContent = '📁';
        const rootFolder = collectedItems[0].path.split('/')[0];
        summaryTitle.textContent = 'Dossier : ' + rootFolder;
        summaryDetails.textContent = count + ' document(s) trouvé(s) • ' + formatSize(totalBytes);
      } else if (count === 1) {
        summaryIcon.textContent = '📄';
        summaryTitle.textContent = collectedItems[0].file.name;
        summaryDetails.textContent = 'Document PDF scanné • ' + formatSize(totalBytes);
      } else {
        summaryIcon.textContent = '📑';
        summaryTitle.textContent = count + ' fichiers sélectionnés';
        summaryDetails.textContent = formatSize(totalBytes) + ' au total';
      }

      selectedSummary.style.display = 'flex';
    }

    // Gestion Drag & Drop (avec support récursif des dossiers)
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
      });
    });

    dropZone.addEventListener('drop', async (e) => {
      const items = e.dataTransfer.items;
      if (!items || !items.length) {
        if (e.dataTransfer.files && e.dataTransfer.files.length) {
          const list = [];
          for (let i = 0; i < e.dataTransfer.files.length; i++) {
            const f = e.dataTransfer.files[i];
            list.push({ file: f, path: f.name });
          }
          setSelection(list);
        }
        return;
      }

      const queue = [];
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
        if (entry) queue.push({ entry, currentPath: '' });
      }

      if (!queue.length) {
        const list = [];
        for (let i = 0; i < e.dataTransfer.files.length; i++) {
          const f = e.dataTransfer.files[i];
          list.push({ file: f, path: f.name });
        }
        setSelection(list);
        return;
      }

      // Parcours asynchrone des répertoires et fichiers
      const collected = [];

      async function readAllEntries(dirReader) {
        const entries = [];
        let batch;
        do {
          batch = await new Promise((res, rej) => dirReader.readEntries(res, rej));
          if (batch && batch.length) entries.push(...batch);
        } while (batch && batch.length > 0);
        return entries;
      }

      async function processEntry(entry, curPath) {
        if (entry.isFile) {
          const file = await new Promise((res, rej) => entry.file(res, rej));
          collected.push({ file, path: curPath + file.name });
        } else if (entry.isDirectory) {
          const reader = entry.createReader();
          const children = await readAllEntries(reader);
          for (const c of children) {
            await processEntry(c, curPath + entry.name + '/');
          }
        }
      }

      for (const item of queue) {
        await processEntry(item.entry, item.currentPath);
      }

      setSelection(collected);
    });

    // Envoi du formulaire
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();

      if (!collectedItems.length) {
        alert('Veuillez sélectionner au moins un fichier PDF, un dossier ou une archive ZIP.');
        return;
      }

      submitBtn.disabled = true;
      spinner.style.display = 'inline-block';
      btnText.textContent = 'Téléversement en cours...';
      progressContainer.style.display = 'block';

      const formData = new FormData();
      formData.append('email', email);

      const paths = [];
      collectedItems.forEach(it => {
        formData.append('files', it.file);
        paths.push(it.path);
      });
      formData.append('file_paths', JSON.stringify(paths));

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
          let msg = xhr.responseText;
          try {
            const j = JSON.parse(xhr.responseText);
            if (j.detail) msg = j.detail;
          } catch (_) {}
          alert("Erreur lors de la transmission : " + msg);
          submitBtn.disabled = false;
          spinner.style.display = 'none';
          btnText.textContent = "🚀 Transmettre pour analyse & tri IA";
          progressContainer.style.display = 'none';
        }
      };

      xhr.onerror = function() {
        alert("Erreur réseau lors de l'envoi.");
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = "🚀 Transmettre pour analyse & tri IA";
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
async def upload_file(
    email: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    file_paths: str = Form(default="[]"),
    zipfile_legacy: UploadFile = File(default=None, alias="zipfile")
):
    upload_list = list(files)
    if zipfile_legacy and zipfile_legacy.filename:
        upload_list.append(zipfile_legacy)

    if not upload_list:
        raise HTTPException(status_code=400, detail="Aucun document n'a été transmis.")

    try:
        parsed_paths = json.loads(file_paths)
    except Exception:
        parsed_paths = []

    valid_items = []
    for i, f in enumerate(upload_list):
        fname = f.filename or ""
        rpath = parsed_paths[i] if i < len(parsed_paths) else fname
        if not rpath:
            rpath = fname
        rpath = rpath.replace("\\", "/").lstrip("/")
        if any(bad in rpath for bad in [".DS_Store", "Thumbs.db", "__MACOSX"]):
            continue
        valid_items.append((f, rpath))

    if not valid_items:
        raise HTTPException(status_code=400, detail="Aucun document valide trouvé dans le dépôt.")

    job_id = str(uuid.uuid4())[:8]

    # Cas 1 : Archive ZIP unique déjà compressée
    if len(valid_items) == 1 and valid_items[0][0].filename.lower().endswith(".zip"):
        f, rpath = valid_items[0]
        safe_filename = f"{job_id}_{Path(f.filename).name}"
        target_path = UPLOADS_DIR / safe_filename
        contents = await f.read()
        target_path.write_bytes(contents)
        file_size = len(contents)
        orig_name = f.filename

    # Cas 2 : Un ou plusieurs fichiers PDF, ou un dossier complet
    else:
        safe_filename = f"{job_id}_dossier_stagiaires.zip"
        target_path = UPLOADS_DIR / safe_filename

        # Nom lisible du dépôt
        if len(valid_items) == 1:
            orig_name = Path(valid_items[0][0].filename).name
        else:
            first_path = valid_items[0][1]
            if "/" in first_path:
                orig_name = f"{first_path.split('/')[0]}.zip"
            else:
                orig_name = "lot_documents_stagiaires.zip"

        with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f, rpath in valid_items:
                contents = await f.read()
                zf.writestr(rpath, contents)

        file_size = target_path.stat().st_size

    jobs = get_jobs()
    job_data = {
        "job_id": job_id,
        "email": email.strip(),
        "original_filename": orig_name,
        "stored_filename": safe_filename,
        "file_size_bytes": file_size,
        "status": "PENDING",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    jobs.append(job_data)
    save_jobs(jobs)

    return JSONResponse(content={
        "success": True,
        "job_id": job_id,
        "message": "Dossier(s) enregistré(s) avec succès dans la file d'attente de traitement."
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
