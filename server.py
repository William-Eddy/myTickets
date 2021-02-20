from flask import Flask
from flask_mysqldb import MySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Kettering1'
app.config['MYSQL_DB'] = 'myTickets'

mysql = MySQL(app)

app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
