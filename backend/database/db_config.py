from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# UPDATE PASSWORD HERE (very important)
DB_USER = "postgres"
DB_PASSWORD = "1234"  # change this
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "aegis_mdlbs_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)