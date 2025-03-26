from datetime import datetime, timedelta
from app.services.boe_fetcher import fetch_boe_json

# Número de días hacia atrás desde hoy
DIAS = 35

def main():
    hoy = datetime.today()
    fechas = [
        (hoy - timedelta(days=i)).strftime("%Y%m%d")
        for i in range(DIAS)
    ]
    fechas.sort()  # Orden cronológico ascendente

    for fecha in fechas:
        print(f"📆 Procesando {fecha}...")
        try:
            fetch_boe_json(fecha)
        except Exception as e:
            print(f"❌ Error procesando {fecha}: {e}")

if __name__ == "__main__":
    main()
