from pathlib import Path
from typing import Optional
import pandas as pd
import sqlite3
from io import BytesIO

DATA_DIR = Path(__file__).parent.resolve().joinpath("data")
DB = DATA_DIR.joinpath("a.db")

__all__ = [
    "create_load_db",
    "load_all_data",
    "insert_uploaded_file_to_db",
]


def create_load_db():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir()

    db_conn = sqlite3.connect(DB)
    db_conn.execute(
        "CREATE TABLE IF NOT EXISTS income_data (id INTEGER PRIMARY KEY AUTOINCREMENT, date DATE, total FLOAT, name VARCHAR, company VARCHAR);"
    )
    db_conn.commit()
    return db_conn


def load_all_data(db_conn: sqlite3.Connection):
    return pd.read_sql_table("income_data", db_conn)


def clean_row_for_db(row: pd.Series):
    if all(["Name", "Date", "Company", "Total"] in row.columns):
        name = row["Name"]
        company = row["Company"]
        date = row["Date"]
        total = row["Total"]

        if not isinstance(total, float):
            total: str = total
            total_split = total.split("$")
            for t in total_split:
                try:
                    total = float(t)
                except:
                    continue
        if isinstance(total, float):
            return dict(name=name, date=date, company=company, total=total)
        raise Exception("`Total` could not be parsed to type `float`.")
    raise Exception(
        f"Row does not contain all columns required. Required columns: ['Name','Date','Company','Total']"
    )


def insert_uploaded_file_to_db(uploaded_file, db_conn: sqlite3.Connection):
    endswith = uploaded_file.name.split(".")[-1]
    df = pd.DataFrame()
    if endswith == "csv":
        df = pd.read_csv(uploaded_file.getvalue())
    elif endswith == "xlsx":
        df = pd.read_excel(uploaded_file.getvalue())

    for _, row in df.iterrows():
        clean_row = clean_row_for_db(row)
        try:
            db_conn.execute(
                f"INSERT INTO income_data (date, total, name, company) VALUES({clean_row['date']},{clean_row['total']},'{clean_row['name']}','{clean_row['company']}')"
            )
        except Exception as ex:
            db_conn.rollback()
    db_conn.commit()


def delete_company_from_db(company: str, db_conn: sqlite3.Connection) -> int:
    try:
        db_conn.execute(f"DELETE FROM income_data WHERE company = '{company}'")
        db_conn.commit()
        return 0
    except Exception as ex:
        db_conn.rollback()
        raise ex
    finally:
        return -1


def export_db_to(
    db_conn: sqlite3.Connection, fmt: str = "csv", where: Optional[str] = None
) -> bytes:
    buffer = BytesIO()
    if where is not None:
        df = pd.read_sql(f"SELECT * FROM income_data WHERE {where};", db_conn)
    else:
        df = load_all_data(db_conn)

    if fmt == "csv":
        df.to_csv(buffer, index=False)
    elif fmt == "xlsx":
        df.to_excel(buffer, index=False)
    elif fmt == "json":
        df.to_json(buffer, index=False)
    else:
        df.to_csv(buffer, index=False)

    return buffer.getvalue()
