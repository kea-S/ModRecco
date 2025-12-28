from utils.paths import get_absolute_path, ensure_path_exists

import requests
import logging
import json


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
    NUSMODS = "https://api.nusmods.com/v2"
    ACADEMIC_YEAR = "2025-2026"
    DATABASE = "moduleInfo.json"

    apiPathString = f"{NUSMODS}/{ACADEMIC_YEAR}/{DATABASE}"

    rawModuleInfoResponse = make_get_request(apiPathString)

    moduleInfoJson = json.loads(rawModuleInfoResponse)

    saveDataPathString = get_absolute_path("data/dev/raw/moduleInfo.json")

    ensure_path_exists(saveDataPathString)

    save_json(saveDataPathString, moduleInfoJson)


if __name__ == "__main__":
    main()
