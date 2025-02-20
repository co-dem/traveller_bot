from pymysql. cursors import DictCursor
import pymysql


db_host = "127.0.0.1"
db_password = "JamSpaceSShooter7774"
db_user = "postgres"
db_name = "testDB"
    
import psycopg2
from psycopg2 import OperationalError

def create_connection():
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port="5432"
        )
        return conn
    except OperationalError as e:
        print(f"Ошибка подключения: {e}")
        return None
    
#             port=3306,