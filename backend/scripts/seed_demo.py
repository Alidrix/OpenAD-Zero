from app.db.session import SessionLocal
from app.demo.seed_demo import seed_demo
if __name__ == '__main__':
    db=SessionLocal()
    try:
        print(seed_demo(db))
    finally:
        db.close()
