from datetime import datetime, timedelta
from app.services.boe_fetcher import fetch_boe_json

def pedir_fecha(texto, por_defecto):
    entrada = input(f"{texto} (por defecto: {por_defecto.strftime('%Y-%m-%d')}): ")
    try:
        return datetime.strptime(entrada.strip(), "%Y-%m-%d") if entrada.strip() else por_defecto
    except ValueError:
        print("⚠️ Formato inválido, se usará la fecha por defecto.")
        return por_defecto

def main():
    
    DAYS = 30
    hoy = datetime.today()
    hace_30 = hoy - timedelta(days=DAYS)

    print("📆 Selección de fechas")
    desde = pedir_fecha("Desde (YYYY-MM-DD)", hace_30)
    hasta = pedir_fecha("Hasta (YYYY-MM-DD)", hoy)

    if desde > hasta:
        print("❌ Fecha 'desde' no puede ser posterior a 'hasta'")
        return

    fechas = [
        (desde + timedelta(days=i)).strftime("%Y%m%d")
        for i in range((hasta - desde).days + 1)
    ]

    print(f"\n🗓️ Procesando BOEs desde {desde.strftime('%Y-%m-%d')} hasta {hasta.strftime('%Y-%m-%d')}\n")
    
    total = 0
    for idx, fecha in enumerate(fechas, 1):
        print(f"[{idx}/{len(fechas)}] 📂 Fecha: {fecha}")
        try:
            fetch_boe_json(fecha)
            total += 1
        except Exception as e:
            print(f"❌ Error en {fecha}: {e}")
    
    print(f"\n✅ Proceso completo: {total} fechas procesadas correctamente.")

if __name__ == "__main__":
    main()
