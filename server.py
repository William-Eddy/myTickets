from flask import Flask, redirect, request,render_template, jsonify, send_from_directory
import mysql.connector

app = Flask(__name__)

def getDatabaseConnection():
    dbConnection = mysql.connector.connect(
      host="localhost",
      user="root",
      password="Kettering1",
      database="myTickets"
    )
    return dbConnection

def executeQuery(query, values=[]):
    connection = getDatabaseConnection()
    cursor = connection.cursor()
    cursor.execute(query,values)
    data = cursor.fetchall()
    connection.close()
    return data

@app.route("/upcomingEvents")
def upcomingEvents():
    if request.method =='GET':
        eventData = executeQuery("SELECT eventID, eventName, eventPerformer FROM events")
        return render_template("upcomingEvents.html", events=eventData)


if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
