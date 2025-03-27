# Activar entorno virtual
Write-Host "Activando entorno virtual..."
& .\venv\Scripts\Activate.ps1

# Lanzar backend (FastAPI) en una nueva terminal (mantiene la ventana abierta)
Write-Host "Lanzando backend (FastAPI) en nueva terminal..."
Start-Process powershell -ArgumentList "-NoExit", "uvicorn app.main:app --reload"

# Esperar un par de segundos antes de lanzar el frontend
Start-Sleep -Seconds 2

# Lanzar frontend (Streamlit) en otra nueva terminal (mantiene la ventana abierta)
Write-Host "Lanzando frontend (Streamlit) en nueva terminal..."
Start-Process powershell -ArgumentList "-NoExit", "streamlit run frontend.py --server.runOnSave=false"

# Mensaje final
Write-Host "Todo corriendo. Abre http://localhost:8501 si no se abre solo."
