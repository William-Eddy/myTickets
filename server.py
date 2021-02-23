from flask import Flask, redirect, request,render_template, jsonify, send_from_directory, make_response, url_for, session
import mysql.connector
import re
import time

app = Flask(__name__)
app.secret_key = 'L9cYyP73ZwT8G5Nk'

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

def executeQueryOne(query, values=()):
    connection = getDatabaseConnection()
    cursor = connection.cursor(prepared=True)
    cursor.execute(query,values)
    data = cursor.fetchone()
    connection.close()
    return data

def executeStatement(query, values=()):
    connection = getDatabaseConnection()
    cursor = connection.cursor(prepared=True)
    cursor.execute(query,values)
    connection.commit()
    cursor.execute("SELECT LAST_INSERT_ID()")
    id = cursor.fetchone()
    connection.close()
    return id[0]

def getCookieTickets():
    tickets = request.cookies.get("tickets").split("/")
    tickets.pop()
    result = []

    for ticket in tickets:
        ticketSplit = ticket.split(".")
        result.append(ticketSplit)

    return result

def getSelectedTickets():
    tickets = getCookieTickets()
    print(tickets)
    result = []
    for ticket in tickets:
        print(ticket[0])
        result.append([executeQueryOne("SELECT vs.venueSeatName, ptt.performanceTicketTypePrice FROM performanceTicketTypes ptt INNER JOIN venueSeating vs ON vs.venueSeatingID = ptt.venueSeatingID WHERE ptt.performanceTicketTypeID = %s",(ticket[0],)),ticket[1]])
    print(result)
    return result


def getOrderTotal():
    total = 0.00;
    for ticket in getSelectedTickets():
        total += float(ticket[0][1]) * int(ticket[1])
    return "{:.2f}".format(total)

def getGuestAccountData():
    return executeQueryOne("SELECT * FROM guests WHERE guestID = %s",(session['id'],))

def getPromoterAccountData():
    return executeQueryOne("SELECT * FROM promoters WHERE promoterID = %s",(session['id'],))

def getPerformanceData(performanceID):
    return executeQuery("SELECT p.performanceID, v.venueCity, v.venueName, DATE_FORMAT(p.performanceDateTime, '%D %M %Y')AS date, v.venueSeatingImage, e.eventImage, e.eventName, e.eventPerformer, DATE_FORMAT(p.performanceDateTime, '%H:%i')AS time, p.performanceTicketLimit FROM performances p INNER JOIN venues v ON p.venueID = v.venueID INNER JOIN events e ON e.eventID = p.eventID WHERE p.performanceID = %s",(performanceID,))[0]

def isLoggedIn():
    if ('loggedin' in session):
        return True
    else:
        return False

@app.route("/upcomingEvents")
def upcomingEvents():
    if request.method =='GET':
        eventData = executeQuery("SELECT eventID, eventName, eventPerformer, eventImage FROM events")
        return render_template("upcomingEvents.html", events=eventData)

@app.route("/upcomingEvents/viewDates/<eventID>")
def viewDates(eventID):
    if request.method =='GET':
        eventID = int(eventID)
        performanceData = executeQuery("SELECT p.performanceID, v.venueCity, v.venueName, DATE_FORMAT(p.performanceDateTime, '%D %M %Y')AS date FROM performances p INNER JOIN venues v ON p.venueID = v.venueID WHERE p.eventID = %s",(eventID,))
        eventData = executeQuery("SELECT * FROM events WHERE eventID = %s",(eventID,))[0]
        return render_template("viewDates.html", performances=performanceData, event=eventData)

@app.route("/performances/<performanceID>/venueTicketOptions")
def viewVenueTicketOptions(performanceID):
    if request.method =='GET':

        venueTicketOptionsQuery = """
        SELECT ptt.performanceTicketTypeID, vs.venueSeatName, ptt.performanceTicketTypePrice,
        CASE
        	WHEN (SELECT COUNT(*) FROM tickets t INNER JOIN performances p ON p.performanceID = t.performanceID INNER JOIN venues v ON v.venueID = p.venueID WHERE p.performanceID = ptt.performanceID AND t.performanceTicketTypeID = ptt.performanceTicketTypeID) < vs.venueSeatCapacity THEN False
            ELSE True
        END AS soldOut
        FROM performanceTicketTypes ptt
        INNER JOIN venueSeating vs
        ON vs.venueSeatingID = ptt.venueSeatingID
        WHERE ptt.performanceID = %s"""

        performanceData = getPerformanceData(performanceID)
        venueTicketOptions = executeQuery(venueTicketOptionsQuery,(int(performanceID),))


        print("TICKET OPTIONS: ")
        print(venueTicketOptions)

        return render_template("venueTicketOptions.html", ticketOptions=venueTicketOptions, performanceData = performanceData)


@app.route('/checkout/payment', methods = ['GET','POST'])
def loadPayment():
    if request.method == 'GET':
        if 'loggedin' in session:
            performanceID = request.cookies.get("performanceID")
            performanceData = getPerformanceData(performanceID)
            orderTotal = getOrderTotal()
            return render_template("payment.html", performanceData = performanceData, ticketData=getSelectedTickets(), guestData=getGuestAccountData(), orderTotal = orderTotal)
        else:
            return render_template("login.html", successPage="/upcomingEvents")
    if request.method == 'POST':

        guestID = session['id']
        transactionID = executeStatement("INSERT INTO transactions (guestID, transactionDateTime) VALUES (%s,%s)",(guestID, time.strftime('%Y-%m-%d %H:%M:%S')))

        basket = getBasketData()
        for ticket in basket:
            performanceID = ticket[0][0]
            seatID = int(executeQuery("SELECT COUNT(*) FROM tickets WHERE performanceID = %s",(performanceID,))[0][0])
            print(seatID)
            executeStatement("INSERT INTO tickets (guestID, performanceID, seatID, transactionID) VALUES (%s,%s,%s,%s)",(guestID,performanceID,seatID,transactionID))
        return render_template("orderConfirmed.html", guestData=getGuestAccountData())

@app.route('/checkout/orderConfirmed', methods = ['GET'])
def loadOrderConfirmed():
    if request.method == 'GET':
        return render_template("orderConfirmed.html", basketData=getBasketData(), guestData=getGuestAccountData())

@app.route('/account/login', methods = ['GET','POST'])
def loadLogin():
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST' and 'emailAddress' in request.form and 'password' in request.form:
        # Create variables for easy access
        emailAddress = request.form['emailAddress']
        password = request.form['password']

        guestAccount = executeQueryOne("SELECT guestID FROM guests WHERE guestEmailAddress = %s AND guestPassword = %s",(emailAddress,password))
        if guestAccount:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = guestAccount[0]
            session['type'] = "guest"
            return render_template("profile.html", guestData=getGuestAccountData())

        return render_template("login.html", msg = "Login details did not match our records. Please try again.")

@app.route('/account/logout', methods = ['GET'])
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('type', None)
   # Redirect to login page
   return render_template("login.html", msg = "You have been logged out")


@app.route('/account/register', methods = ['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        emailAddress = request.form['emailAddress']
        addressLine1 = request.form['addressLine1']
        addressLine2 = request.form['addressLine2']
        postcode = request.form['postcode']
        mobileNumber = request.form['mobileNumber']
        password = request.form['password']

        executeStatement("INSERT INTO guests (guestFirstName, guestLastName, guestEmailAddress, guestAddressLine1, guestAddressLine2, guestPostcode, guestMobileNumber, guestPassword) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(firstName,lastName,emailAddress,addressLine1,addressLine2,postcode,mobileNumber,password,))
        guestID = (executeQuery("SELECT guestID FROM guests WHERE guestEmailAddress = %s",(emailAddress,)))[0][0]
        session['loggedin'] = True
        session['id'] = guestID
        session['type'] = "guest"
        return render_template("profile.html", guestData=getGuestAccountData())

@app.route('/account/profile', methods = ['GET'])
def profile():
    if isLoggedIn():
        return render_template("profile.html", guestData=getGuestAccountData())
    else:
        return render_template("login.html", msg = "Please log in to continue")



if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
