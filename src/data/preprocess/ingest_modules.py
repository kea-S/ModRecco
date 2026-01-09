from utils.paths import get_absolute_path
from src.data.schemas import Base, Module
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from pprint import pformat
import requests
import logging
import json
import os
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def make_get_request(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"""
        Successfully retrieving from {url}. Status Code: {response.status_code}
        """)

        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during GET request to {url}: {e}")

        return None


def save_json(filepath, data):
    """
    Saves JSON data to a specified file.

    Args:
        filepath (str): The path to the file where the JSON data will be saved.
        data (dict or list): The JSON-serializable data to save.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully saved to {filepath}")
    except IOError as e:
        print(f"Error saving data to {filepath}: {e}")


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

    # create tables if don't exist, if they do ignore
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    NUSMODS = "https://api.nusmods.com/v2"
    ACADEMIC_YEAR = "2025-2026"
    MODULE_LIST_DB = "moduleList.json"
    MODULES_PATH = "modules"

    moduleListapiPathString = f"{NUSMODS}/{ACADEMIC_YEAR}/{MODULE_LIST_DB}"

    rawModuleListResponse = make_get_request(moduleListapiPathString)

    moduleListJson = json.loads(rawModuleListResponse)

    specificModuleapiPathString = \
        "{NUSMODS}/{ACADEMIC_YEAR}/{MODULES_PATH}/{module_code}.json"

    for module in moduleListJson:
        moduleCode = module["moduleCode"]

        try:
            rawModuleInfoResponse = make_get_request(specificModuleapiPathString.
                                                     format(NUSMODS=NUSMODS,
                                                            ACADEMIC_YEAR=ACADEMIC_YEAR,
                                                            MODULES_PATH=MODULES_PATH,
                                                            module_code=moduleCode))

            if not rawModuleInfoResponse:
                logger.warning(f"Skipping {moduleCode}: No response from API")
                continue

            moduleInfo = json.loads(rawModuleInfoResponse)
            logging.debug("\n" + pformat(moduleInfo, 4, 80))

            module = Module(
                    module_code=moduleInfo["moduleCode"],
                    title=moduleInfo["title"],
                    description=moduleInfo["description"],
                    department=moduleInfo["department"],
                    faculty=moduleInfo["faculty"],
                    module_credit=int(float(moduleInfo["moduleCredit"])),
                    semester_data=moduleInfo["semesterData"],
                    prereq_tree=moduleInfo.get("prereqTree", None),
                    vector_embedding=[0.0] * 64   # or how many dims the vector is
                )

            logger.info(f"Succesfully created object for {moduleCode}")

            session.merge(module)

            logger.info(f"Succesfully merged object for {moduleCode} into database")

            session.commit()
            logger.info(f"Succesfully ingested {moduleCode}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to process {moduleCode}: {str(e)}")
            continue

    session.close()
    logger.info("Ingestion complete")


if __name__ == "__main__":
    main()
