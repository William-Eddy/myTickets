from flask import Flask

DATABASE = "myTickets.db"

app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
