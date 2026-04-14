from .models import Base
from .db_config import engine

def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("All database tables created successfully!")

if __name__ == "__main__":
    create_all_tables()