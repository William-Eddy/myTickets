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

@app.route("/upcomingEvents/viewDates/<eventID>")
def viewDates(eventID):
    if request.method =='GET':
        performanceData = executeQuery("SELECT p.performanceID, v.venueCity, v.venueName, DATE_FORMAT(p.performanceDateTime, "%D %M %Y")AS date FROM performances p INNER JOIN venues v ON p.venueID = v.venueID WHERE p.eventID = ?",[eventID])
        return render_template("viewDates.html", date=performanceData)


if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
