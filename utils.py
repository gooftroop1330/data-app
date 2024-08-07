from pathlib import Path
from typing import Optional
import pandas as pd
from io import BytesIO
import duckdb
from datetime import datetime, date, timedelta

DATA_DIR = Path(__file__).parent.resolve().joinpath("data")
DB = DATA_DIR.joinpath("a.duckdb")

__all__ = [
    "create_load_db",
    "load_all_data",
    "insert_uploaded_file_to_db",
]


def create_load_db():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir()

    db_conn = duckdb.connect(database="a.duckdb")
    db_conn.execute(
        "CREATE TABLE IF NOT EXISTS income_data (date DATE, total FLOAT, name VARCHAR(255), company VARCHAR(255));"
    )
    db_conn.commit()
    return db_conn


def load_all_data(db_conn: duckdb.DuckDBPyConnection):
    df = db_conn.execute(
        "SELECT * FROM income_data",
    ).fetchdf()
    return df


def clean_row(row: pd.Series):

    name = row["Name"]
    company = row["Company"]
    ddate = row["Date"]
    total = float(row["Total"])

    return dict(name=name, date=ddate, company=company, total=float(total))


def only_new(current: pd.DataFrame, uploaded: pd.DataFrame) -> pd.DataFrame:
    cleaned = []

    for _, row in uploaded.iterrows():
        cleaned.append(clean_row(row))
    del uploaded
    clean_df = pd.DataFrame(cleaned)
    clean_df = clean_df[~clean_df.apply(tuple, 1).isin(current.apply(tuple, 1))]
    clean_df["Date"] = pd.to_datetime(clean_df["Date"]).dt.to_datetime64
    return clean_df


def insert_uploaded_file_to_db(uploaded_file, db_conn: duckdb.DuckDBPyConnection):
    current = load_all_data(db_conn=db_conn)

    endswith = uploaded_file.name.split(".")[-1]
    uploaded = pd.DataFrame()

    if endswith == "csv":
        uploaded = pd.read_csv(uploaded_file, parse_dates=True)
    elif endswith == "xlsx":
        uploaded = pd.read_excel(uploaded_file, parse_dates=True)

    uploaded["Total"] = uploaded["Total"].apply(
        lambda x: float(x.replace("$", "").replace(",", ""))
    )
    uploaded["Date"] = pd.to_datetime(uploaded["Date"]).dt.date
    if len(current) != 0:
        only_new_df = only_new(current, uploaded)
    else:
        only_new_df = uploaded

    for _, row in only_new_df.iterrows():
        try:
            print(row)
            db_conn.execute(
                f"INSERT INTO income_data (date, total, name, company) VALUES({row['Date']}, {row['Total']},'{row['Name']}','{row['Company']}')"
            )
        except Exception as ex:
            raise ex
    db_conn.commit()


def delete_company_from_db(company: str, db_conn: duckdb.DuckDBPyConnection) -> int:
    try:
        db_conn.execute(f"DELETE FROM income_data WHERE company = '{company}'")
        db_conn.commit()
        return 0
    except Exception as ex:
        raise ex
    finally:
        return -1


def export_db_to(
    db_conn: duckdb.DuckDBPyConnection, fmt: str = "csv", where: Optional[str] = None
) -> bytes:
    buffer = BytesIO()
    if where is not None:
        df = db_conn.execute(f"SELECT * FROM income_data WHERE {where};").fetchdf()
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
