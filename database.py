#pip install mysql-connector-python

import mysql.connector

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Rachitha@18',
    database='notes_app'
)

cursor = db.cursor()