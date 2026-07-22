import mysql.connector
import os

# configuring the database by connecting it to the mysql server by a local host and a root
# by using a database named gyanpusthak in the mysql server
def get_db_connection():
    try:
        connection = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="user@123",
    database="gyanpusthak",  
    port=3306
)
        return connection
    except mysql.connector.Error as err:
        print("❌ DATABASE CONNECTION FAILED")
        print(f"Error: {err}")
        return None