from dotenv import load_dotenv
import os

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("DB_SERVER:", DB_SERVER)
print("DB_DATABASE:", DB_DATABASE)

if __name__ == "__main__":
    print("Executando config.py diretamente")