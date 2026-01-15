import json
import uuid
import os
import logging
from datetime import datetime
from typing import get_type_hints, get_args, get_origin, Union, List

import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Mapped
from pydantic import TypeAdapter
from dotenv import load_dotenv

from utils.paths import get_absolute_path, ensure_path_exists
from src.data.schemas import Module, UserInteraction, SemesterData, PrereqTree

# Aligning with ingest_modules.py logging style
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adapters for our single-source-of-truth models
semester_adapter = TypeAdapter(List[SemesterData])
prereq_adapter = TypeAdapter(PrereqTree)


def get_arrow_type(hint):
    """Maps Python types from schemas.py to Arrow types."""
    if get_origin(hint) is Mapped:
        hint = get_args(hint)[0]
    if get_origin(hint) is Union:
        args = [a for a in get_args(hint) if a is not type(None)]
        hint = args[0] if args else str

    if hint is str: return pa.string()
    if hint is int: return pa.int64()
    if hint is float: return pa.float32()
    if hint is uuid.UUID: return pa.string()
    if hint is datetime: return pa.timestamp('us')

    # Handle pgvector Vector type or other list-like embedding types
    hint_str = str(hint)
    if "Vector" in hint_str or "vector" in hint_str:
        return pa.list_(pa.float32())

    # handle list
    origin = get_origin(hint)
    if origin is list or hint is list:
        args = get_args(hint)

        if args and hasattr(args[0], "model_fields"):
            return pa.string()

        inner = pa.float32() if not args else get_arrow_type(args[0])
        return pa.list_(inner)

    return pa.string()


def sync_table(session, model, output_path):
    logger.info(f"Syncing {model.__tablename__} to Parquet...")

    hints = get_type_hints(model)
    fields = []
    for name, col in model.__table__.columns.items():
        arrow_type = get_arrow_type(hints.get(name))
        fields.append(pa.field(name, arrow_type, nullable=col.nullable))
    schema = pa.schema(fields)

    records = session.query(model).all()

    rows = []
    for obj in records:
        row = {}
        for field in schema:
            val = getattr(obj, field.name)

            try:
                if field.name == "semester_data" and val:
                    row[field.name] = semester_adapter.dump_json(
                        semester_adapter.validate_python(val)
                    ).decode()
                elif field.name == "prereq_tree" and val:
                    row[field.name] = prereq_adapter.dump_json(
                        prereq_adapter.validate_python(val),
                        by_alias=True
                    ).decode()
                elif field.name == "vector_embedding":
                    # Convert numpy array from pgvector to standard Python list
                    row[field.name] = val.tolist() if hasattr(val, "tolist") else val

                elif isinstance(val, uuid.UUID):
                    row[field.name] = str(val)
                elif hasattr(val, 'value'):
                    row[field.name] = val.value
                elif isinstance(val, (dict, list)):
                    row[field.name] = json.dumps(val)
                else:
                    row[field.name] = val
            except Exception as e:
                logger.error(f"Error processing field {field.name}: {e}")
                raise

        rows.append(row)

    if rows:
        table = pa.Table.from_pylist(rows, schema=schema)
        pq.write_table(table, output_path, compression='snappy')
        logger.info(f"Successfully exported {len(rows)} records to {output_path}")
    else:
        logger.warning(f"No records found in {model.__tablename__} to export.")


def main():
    load_dotenv(dotenv_path=get_absolute_path(".env"))

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")

    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        logger.error("Missing database environment variables.")
        return

    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        path_string = "data/dev/raw/modules.parquet"
        ensure_path_exists(path_string)
        sync_table(session, Module, get_absolute_path(path_string))
        # sync_table(session, UserInteraction, "user_interactions.parquet")
    except Exception as e:
        logger.error(f"Sync process failed: {str(e)}")
    finally:
        session.close()
        logger.info("Database session closed")


if __name__ == "__main__":
    main()
