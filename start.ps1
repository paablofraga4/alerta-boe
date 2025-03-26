# Activar entorno virtual
Write-Host "Activando entorno virtual..."
& .\venv\Scripts\Activate.ps1

# Lanzar backend (FastAPI)
Write-Host "Lanzando backend (FastAPI)..."
Start-Process powershell -ArgumentList "uvicorn app.main:app --reload" -NoNewWindow

# Esperar un poco antes del frontend
Start-Sleep -Seconds 2

# Lanzar frontend (Streamlit) SIN recarga en caliente
Write-Host "Lanzando frontend (Streamlit)..."
Start-Process powershell -ArgumentList "streamlit run frontend.py --server.runOnSave=false"

# Mensaje final
Write-Host "Todo corriendo. Abre http://localhost:8501 si no se abre solo."
