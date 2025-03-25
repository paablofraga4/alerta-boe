# 🛠️ Script de arranque para AlertaBOE
# Abre 2 ventanas: una para FastAPI y otra para Streamlit

Write-Host "✅ Lanzando API en nueva ventana..."
Start-Process powershell -ArgumentList "cd $(Get-Location); .\venv\Scripts\activate; uvicorn app.main:app --reload"

Start-Sleep -Seconds 2

Write-Host "✅ Lanzando interfaz web (Streamlit)..."
Start-Process powershell -ArgumentList "cd $(Get-Location); .\venv\Scripts\activate; streamlit run frontend.py"
