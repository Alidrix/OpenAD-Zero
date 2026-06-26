from app.db.session import SessionLocal
from app.demo.seed_demo import seed_demo

def main():
    db=SessionLocal()
    try:
        mission=seed_demo(db)
        print(f"Demo mission seeded: {mission.id}")
    finally:
        db.close()
if __name__=='__main__': main()
