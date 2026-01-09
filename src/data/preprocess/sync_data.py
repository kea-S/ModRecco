from utils.paths import get_absolute_path
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def main():
    load_dotenv(dotenv_path=get_absolute_path(".env"))

    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME")
    DB_HOST = os.environ.get("DB_HOST")

    database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

    engine = create_engine(database_url)

    # check if pgvector installed
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Session = sessionmaker(bind=engine)
    session = Session()

    session.close()


if __name__ == "__main__":
    main()
