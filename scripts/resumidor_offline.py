import argparse
from datetime import datetime
from sqlalchemy import or_
from app.db.session import SessionLocal
from app.db.models import Publication
from app.services.summarizer import extraer_texto_desde_html
from app.services.summarizer_groq import resumir_texto_tiktok
from tqdm import tqdm
from colorama import Fore, init
import time

start_time = time.time()
init(autoreset=True)

def generar_resumenes_tiktok(from_date=None, to_date=None, limit=None):
    session = SessionLocal()

    query = session.query(Publication).filter(
        or_(
            Publication.resumen_tiktok.is_(None),
            Publication.resumen_tiktok == ""
        )
    )

    if from_date:
        query = query.filter(Publication.date >= from_date)
    if to_date:
        query = query.filter(Publication.date <= to_date)
    if limit:
        query = query.limit(limit)

    publicaciones = query.all()

    print(f"\n🔍 Publicaciones sin resumen TikTok: {len(publicaciones)}\n")

    actualizadas = 0
    con_tiktok = 0
    fallidas = 0

    for idx, pub in enumerate(tqdm(publicaciones, desc="🎬 Generando TikTok resumenes"), 1):
        print(f"\n📄 ({idx}/{len(publicaciones)}) Publicación ID {pub.id} — {pub.title[:80]}")

        if not pub.url_html:
            print(Fore.YELLOW + "⚠️  Sin URL HTML — salto")
            continue

        texto = extraer_texto_desde_html(pub.url_html)
        if not texto.strip():
            print(Fore.YELLOW + "⚠️  Texto vacío extraído — salto")
            continue

        print("🎬 Generando resumen TikTok...")
        resumen_tiktok = resumir_texto_tiktok(texto)

        if resumen_tiktok:
            pub.resumen_tiktok = resumen_tiktok
            session.commit()
            print(Fore.CYAN + "🎯 Tiktok-resumen guardado")
            con_tiktok += 1
            actualizadas += 1
        else:
            print(Fore.RED + "❌ No se generó TikTok resumen")
            fallidas += 1

        # Pausa cada 40 publicaciones si el límite es mayor a 40
        if limit and limit > 40 and idx % 40 == 0 and idx < len(publicaciones):
            print(Fore.MAGENTA + "⏸️ Pausa de 1.5 minutos para evitar sobrecarga...")
            time.sleep(120)

    session.close()

    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    print(f"📝 Publicaciones procesadas:     {len(publicaciones)}")
    print(f"✅ Resúmenes TikTok generados:    {con_tiktok}")
    print(f"❌ Fallidas:                      {fallidas}")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resumidor TikTok de publicaciones BOE")
    parser.add_argument("--from", dest="from_date", help="Fecha inicial (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="Fecha final (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, help="Máximo número de publicaciones")
    args = parser.parse_args()

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date() if args.from_date else None
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date() if args.to_date else None

    generar_resumenes_tiktok(
        from_date=from_date,
        to_date=to_date,
        limit=args.limit
    )

    elapsed = time.time() - start_time
    minutos = int(elapsed // 60)
    segundos = int(elapsed % 60)
    print(f"\n⏱️ Tiempo total: {minutos} min {segundos} s\n")