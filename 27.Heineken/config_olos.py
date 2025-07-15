from dotenv import load_dotenv
import os

load_dotenv()

DB_SERVER = os.getenv("DBOLOS_SERVER")
DB_DATABASE = os.getenv("DBOLOS_DATABASE")
DB_USER = os.getenv("DBOLOS_USER")
DB_PASSWORD = os.getenv("DBOLOS_PASSWORD")

print("DBOLOS_SERVER:", DB_SERVER)
print("DBOLOS_DATABASE:", DB_DATABASE)

if __name__ == "__main__":
    print("Executando config_olos.py diretamente")