"""Seed departments and demo authority/citizen accounts (test accounts only).
Run:  python -m app.seed
"""
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Department, User
from app.models.enums import UserRole

DEPARTMENTS = [
    ("Roads", "Road damage and potholes"),
    ("Sanitation", "Garbage and waste management"),
    ("Water", "Water supply and leakage"),
    ("Electrical", "Streetlights and public electrical assets"),
]

USERS = [
    ("Demo Citizen", "citizen@demo.sevasetu", UserRole.CITIZEN),
    ("Demo Authority", "authority@demo.sevasetu", UserRole.AUTHORITY),
]


def run():
    db = SessionLocal()
    try:
        for name, desc in DEPARTMENTS:
            if not db.query(Department).filter_by(name=name).first():
                db.add(Department(name=name, description=desc))
        for name, email, role in USERS:
            if not db.query(User).filter_by(email=email).first():
                db.add(User(name=name, email=email, role=role,
                            password_hash=hash_password("demo1234")))
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
