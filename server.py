from flask import Flask, redirect, request,render_template, jsonify, send_from_directory, make_response, url_for, session
import mysql.connector
import re

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
    connection.close()
    return None


def getBasketData():

    basket = getCookieBasket()

    for product in basket:
        eventID = product[0]
        product[0] = (executeQuery("SELECT p.performanceID, e.eventName, e.eventPerformer, v.venueName, v.venueCity, DATE_FORMAT(p.performanceDateTime, '%D %M %Y')AS date FROM performances p INNER JOIN events e ON e.eventID = p.eventID INNER JOIN venues v ON v.venueID = p.venueID WHERE e.eventID = %s",(eventID,)))[0]

    return basket

def getCookieBasket():
    basket = request.cookies.get("basket").split("/")
    basket.pop()
    result = []

    for product in basket:
        productSplit = product.split(".")
        result.append(productSplit)

    return result

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
        return render_template("basket.html", basketData=getBasketData())

@app.route('/checkout/payment', methods = ['GET'])
def loadPayment():
    if request.method == 'GET':
        return render_template("payment.html", basketData=getBasketData())

@app.route('/checkout/guestDetails', methods = ['GET','POST'])
def guestDetails():
    if request.method == 'GET':
        return render_template("guestDetails.html")
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        emailAddress = request.form['emailAddress']
        addressLine1 = request.form['addressLine1']
        addressLine2 = request.form['addressLine2']
        postcode = request.form['postcode']
        mobileNumber = request.form['mobileNumber']

        executeStatement("INSERT INTO guests (guestFirstName, guestLastName, guestEmailAddress, guestAddressLine1, guestAddressLine2, guestPostcode, guestMobileNumber) VALUES (%s,%s,%s,%s,%s,%s,%s)",(firstName,lastName,emailAddress,addressLine1,addressLine2,postcode,mobileNumber,))
        guestID = (executeQuery("SELECT guestID FROM guests WHERE guestEmailAddress = %s",(emailAddress,)))[0][0]
        return str(guestID)

@app.route('/checkout/orderConfirmed', methods = ['GET'])
def loadOrderConfirmed():
    if request.method == 'GET':
        return render_template("orderConfirmed.html", basketData=getBasketData())

@app.route('/basket/add', methods = ['POST'])
def addToBasket():
   if request.method == 'POST':
       performanceID = request.form['performanceID']
       quantity = request.form['quantity']
       exisitngItems = ""
       if 'basket' in request.cookies:
           exisitngItems = request.cookies.get('basket')

       resp = make_response(render_template('basket.html'))
       resp.set_cookie('basket', exisitngItems + performanceID+"."+quantity+"/")
       return resp

@app.route('/login', methods = ['GET','POST'])
def loadLogin():
    if request.method == 'GET':
        errorMessage = ""
    if request.method == 'POST' and 'emailAddress' in request.form and 'password' in request.form:
        # Create variables for easy access
        emailAddress = request.form['emailAddress']
        password = request.form['password']
        account = executeQueryOne("SELECT guestID FROM guests WHERE guestEmailAddress = %s AND guestPassword = %s",(emailAddress,password))
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[0]
            errorMessage = 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            errorMessage = "Login failed."
    return render_template("login.html", msg = errorMessage)

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
