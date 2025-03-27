from app.db.session import SessionLocal
from app.db.models import Scope, Region

db = SessionLocal()

print("🌍 Insertando scopes y regiones...")

scopes = ["Nacional", "Autonómico", "Europeo"]
regions = [
    ("España", "ESP"),
    ("Andalucía", "AND"),
    ("Aragón", "ARA"),
    ("Asturias", "AST"),
    ("Islas Baleares", "BAL"),
    ("Canarias", "CAN"),
    ("Cantabria", "CB"),
    ("Castilla-La Mancha", "CLM"),
    ("Castilla y León", "CYL"),
    ("Cataluña", "CAT"),
    ("Comunidad Valenciana", "VAL"),
    ("Extremadura", "EXT"),
    ("Galicia", "GAL"),
    ("Madrid", "MAD"),
    ("Murcia", "MUR"),
    ("Navarra", "NAV"),
    ("País Vasco", "PV"),
    ("La Rioja", "LR"),
    ("Ceuta", "CEU"),
    ("Melilla", "MEL"),
    ("Unión Europea", "UE")
]

# Insert scopes
for name in scopes:
    if not db.query(Scope).filter_by(name=name).first():
        db.add(Scope(name=name))

# Insert regions
for name, code in regions:
    if not db.query(Region).filter_by(code=code).first():
        db.add(Region(name=name, code=code))

db.commit()
db.close()

print("✅ Scopes y regiones insertados.")
