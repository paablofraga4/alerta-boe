from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Publication
from app.schemas.publication import PublicationOut
from typing import List
from datetime import date

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[PublicationOut])
def get_publications(db: Session = Depends(get_db)):
    return db.query(Publication).all()

@router.get("/fecha/{fecha}", response_model=List[PublicationOut])
def get_publications_by_date(fecha: date, db: Session = Depends(get_db)):
    return db.query(Publication).filter(Publication.date == fecha).all()

