from flask import Flask, render_template

import mysql.connector as sql

conn = sql.connect(host = "localhost", user = "root", passwd="Pavitra@01", database = "vital_nest_flask_solution")
if(conn.is_connected):
    print("Connected Successfully")
else:
    print("Connection is interrupted")


app = Flask(__name__)



@app.route('/')
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug = True)