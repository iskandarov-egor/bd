#!/usr/bin/python
from app import app, conn, cursor
app.run(debug = True)

cursor.close()
conn.close()
