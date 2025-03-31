import argparse
from datetime import datetime
from sqlalchemy import or_
from app.db.session import SessionLocal
from app.db.models import Publication
from app.services.summarizer import extraer_texto_desde_html
from app.services.summarizer_groq import resumir_texto, resumir_texto_tiktok
from tqdm import tqdm
from colorama import Fore, init

import time  # ya lo tendrás en el proyecto seguramente

start_time = time.time()

init(autoreset=True)  # colores

def generar_resumenes(from_date=None, to_date=None, limit=None):
    session = SessionLocal()

    query = session.query(Publication).filter(
        or_(
            Publication.resumen.is_(None),
            Publication.resumen == "",
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

    print(f"\n🔍 Publicaciones con resúmenes incompletos: {len(publicaciones)}\n")

    actualizadas = 0
    con_resumen = 0
    con_tiktok = 0
    solo_tiktok = 0
    solo_resumen = 0
    fallidas = 0

    for idx, pub in enumerate(tqdm(publicaciones, desc="🌀 Procesando publicaciones"), 1):
        print(f"\n📄 ({idx}/{len(publicaciones)}) Publicación ID {pub.id} — {pub.title[:80]}")

        if not pub.url_html:
            print(Fore.YELLOW + "⚠️  Sin URL HTML — salto")
            continue

        texto = extraer_texto_desde_html(pub.url_html)
        if not texto.strip():
            print(Fore.YELLOW + "⚠️  Texto vacío extraído — salto")
            continue

        resumen = None
        resumen_tiktok = None

        if not pub.resumen:
            print("🧠 Generando resumen largo...")
            resumen = resumir_texto(texto)
            if resumen:
                pub.resumen = resumen
                print(Fore.GREEN + "✅ Resumen guardado")
                con_resumen += 1
            else:
                print(Fore.RED + "❌ No se generó resumen")

        else:
            print(Fore.BLUE + "📌 Resumen ya existe — salto")

        if not pub.resumen_tiktok:
            print("🎬 Generando resumen TikTok...")
            resumen_tiktok = resumir_texto_tiktok(texto)
            if resumen_tiktok:
                pub.resumen_tiktok = resumen_tiktok
                print(Fore.CYAN + "🎯 Tiktok-resumen guardado")
                con_tiktok += 1
            else:
                print(Fore.RED + "❌ No se generó TikTok resumen")
        else:
            print(Fore.BLUE + "📌 Resumen TikTok ya existe — salto")

        if resumen or resumen_tiktok:
            session.commit()
            actualizadas += 1
            if resumen and not resumen_tiktok:
                solo_resumen += 1
            elif resumen_tiktok and not resumen:
                solo_tiktok += 1
        else:
            fallidas += 1

    session.close()


    # 📊 Informe final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    print(f"📝 Publicaciones procesadas:     {len(publicaciones)}")
    print(f"✅ Publicaciones actualizadas:   {actualizadas}")
    print(f"   - Con resumen:                {con_resumen}")
    print(f"   - Con resumen tiktok:         {con_tiktok}")
    print(f"   - Solo resumen:               {solo_resumen}")
    print(f"   - Solo tiktok:                {solo_tiktok}")
    print(f"❌ Fallidas (ningún resumen):    {fallidas}")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resumidor offline de publicaciones BOE")
    parser.add_argument("--from", dest="from_date", help="Fecha inicial (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="Fecha final (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, help="Máximo número de publicaciones")
    args = parser.parse_args()

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date() if args.from_date else None
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date() if args.to_date else None

    generar_resumenes(
        from_date=from_date,
        to_date=to_date,
        limit=args.limit
    )

    elapsed = time.time() - start_time
    minutos = int(elapsed // 60)
    segundos = int(elapsed % 60)

    print(f"\n⏱️ Tiempo total: {minutos} min {segundos} s\n")
