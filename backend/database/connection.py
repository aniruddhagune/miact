import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="miact",
        user="postgres",
        password="password",
        host="localhost",
        port="5432"
    )