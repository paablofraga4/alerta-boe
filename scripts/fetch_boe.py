from app.services.boe_fetcher import fetch_boe_json

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.fetch_boe YYYYMMDD")
    else:
        fetch_boe_json(sys.argv[1])
