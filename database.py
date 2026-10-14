#pip install mysql-connector-python

import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()
db = mysql.connector.connect(
    host='localhost',
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database='notes_app'
)

cursor = db.cursor()