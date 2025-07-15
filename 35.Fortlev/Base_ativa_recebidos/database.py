from sqlalchemy import create_engine
from config import DB_SERVER, DB_DATABASE,DB_USER,DB_PASSWORD
import urllib

def get_engine():
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
	f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=yes"
	)
    params = urllib.parse.quote_plus(connection_string)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return engine
