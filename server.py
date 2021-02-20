from flask import Flask, redirect, request,render_template, jsonify, send_from_directory, make_response
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

def executeQuery(query, values=()):
    connection = getDatabaseConnection()
    cursor = connection.cursor(prepared=True)
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
        eventID = int(eventID)
        performanceData = executeQuery("SELECT p.performanceID, v.venueCity, v.venueName, DATE_FORMAT(p.performanceDateTime, '%D %M %Y')AS date FROM performances p INNER JOIN venues v ON p.venueID = v.venueID WHERE p.eventID = %s",(eventID,))
        return render_template("viewDates.html", performances=performanceData)

@app.route('/basket', methods = ['GET'])
def loadBasket():
    if request.method == 'GET':
        return render_template("basket.html", basket=request.cookies.get('basket'))

@app.route('/basket/add', methods = ['POST'])
def addToBasket():
   if request.method == 'POST':
       print("----- RUNNING -----")
       performanceID = request.form['performanceID']
       quantity = request.form['quantity']
       exisitngItems = ""
       if 'basket' in request.cookies:
           exisitngItems = request.cookies.get('basket')

       resp = make_response(render_template('basket.html'))
       resp.set_cookie('basket', exisitngItems + performanceID+"."+quantity+"/")
       return resp


if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
