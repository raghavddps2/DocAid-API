
from flask import Flask, redirect, url_for, request, jsonify,render_template
from firebase_admin import credentials, firestore, initialize_app
import pickle
import socket
import json
import numpy as np
import pyrebase
import pdfkit
import sklearn
app = Flask(__name__)
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()

config = {
       "apiKey": "AIzaSyAmAnf-0bRmvGjRkJJgpZkDiZ3nRIFlBhw",
    "authDomain": "docaid-api.firebaseapp.com",
    "databaseURL": "https://docaid-api.firebaseio.com",
    "projectId": "docaid-api",
    "storageBucket": "docaid-api.appspot.com",
    "messagingSenderId": "918014081942",
    "appId": "1:918014081942:web:827def8f7c8615204d7bb7"

}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()

patient_details = db.collection('patient_details')
medicines_diagonized = db.collection('medicines_diagonized')
diagnosis_keywords = db.collection('diagnosis_keywords')
reports = db.collection('reportsUrl')

# API SUMMARY

# API1: patient_details_api [POST and GET]
# API2: diagonized_medicines_api [POST GET and PUT]
# API3: diagnosis_keywords_api [POST GET and PUT]


@app.route('/rg',methods=['POST'])
def genPdf():
    if request.method == 'POST':
        data = request.json
        age = data['age']
        pid = data['pid']
        dosages = data['dosages']
        bmi = data['bmi']
        x = render_template('r.html',pid=pid,age=age,bmi=bmi,dosages=dosages)
        print(x)
        pdfkit.from_string(x,'report1.pdf')
        report = str(pid)
        storage.child('reportsPdf/{}'.format(report)).put('report1.pdf')
        pdf_url = storage.child('reportsPdf/{}'.format(report)).get_url(None)
        data = {
            'pdf_url':pdf_url
        }
        res = reports.document(pid).set(data)
        return pdf_url
    
@app.route('/sendReportToDB',methods=['POST'])
def getReport():
    requestData = request.json
    pid = requestData['pid']
    data = reports.document(pid).get()
    return jsonify(data.to_dict())

@app.route('/prediction', methods=['POST'])
def prediction():

    requestData = request.json
    data = requestData['val']

    if request.method == 'POST':
        s = ['skin_rash', 'continuous_sneezing', 'acidity', 'fatigue', 'nausea',
             'loss_of_appetite', 'chest_pain', 'fast_heart_rate', 'bladder_discomfort', 'muscle_pain',
             'prognosis']

        symptoms = [s[i] for i in range(len(s)) if i == 1]

        model = pickle.load(open('medpredMLP.pickle', 'rb'))
        dummydata = model.predict([data])

        d = str(dummydata[0])
        print(d)
        with open('Medicine.json') as json_file:
            jdata = json.load(json_file)
            data = jdata[d]
        # data = jsonify(list(dummydata))
        print("\n\n", data)
        class_probs = np.array(model.predict_proba([data]))
        probs = class_probs
        # i, max1 = np.argmax(probs), np.amax(probs)
        # ddata = np.delete(probs, i)
        # j, max2 = np.argmax(ddata), np.amax(ddata)

        # print(type(j), type())

        # dis1 = data
        # prid1 = 0

        # ndata = {str(d): data}
        # list1 = []
        # list1.append(ndata)
        # list1.append(symptoms)
        # jsondata = jsonify(list1)
        # return jsondata
        return "Hello World"


@app.route('/patient_details', methods=['POST', 'GET'])
def patient_details_api():

    requestData = request.json
    pid = requestData['pid']

    if request.method == 'POST':
        res = patient_details.document(pid).set(request.json)
        data = {

            "message": "patient_added",
            "pid": pid
        }
        return data
    elif request.method == 'GET':
        data = patient_details.document(pid).get()
        return jsonify(data.to_dict())
    else:
        return "Invalid request"


@app.route('/diagonized_medicines_1', methods=['POST'])
def diagonized_medicines_1():
    requestData = request.json
    pid = requestData['pid']

    if(request.method == 'POST'):
        data = medicines_diagonized.document(pid).get()
        d = data.to_dict()
        l = []
        for key in d:
            l.append(d[key])
        return jsonify(data.to_dict())
    else:
        return "Invalid request"


@app.route('/diagonized_medicines', methods=['POST', 'GET', 'PUT'])
def diagonized_medicines():
    requestData = request.json
    pid = requestData['pid']
    if(request.method == 'POST'):

        timestamp = requestData['timestamp']
        sendData = {}
        sendData[timestamp] = requestData
        medicines_diagonized.document(pid).set(sendData)
        data = {
            "message": "Medicines stored for first time",
            "pid": pid,
            "timestamp": timestamp
        }
        return data

    elif request.method == 'PUT':
        '''
            #Now this is interesting, please note carefully. 
            When the doctor is gonna update it when the user visits second time, 
            Here, the previous json object will be called using get and then the current one will be appended,
            so that it becomes an array of objects according to timestamp. 

            #Thats just json, manipulation, in the api, we will just update the value, whenever a put request is received.
        '''
        # The requestData will obviously change as is sent in the request.

        timestamp = requestData['timestamp']
        data = medicines_diagonized.document(pid).get()
        data = data.to_dict()
        json_data = {}
        for key in data.keys():
            json_data[key] = data[key]
        json_data[timestamp] = requestData
        print(json_data)
        medicines_diagonized.document(pid).update(json_data)
        data = {
            "message": "Medicines updated",
            "pid": pid,
        }
        return data

    # This will be used while generating the prescription.
    elif(request.method == 'GET'):
        data = medicines_diagonized.document(pid).get()
        return jsonify(data.to_dict())

    else:
        return "Invalid request"


@app.route('/keywords', methods=['GET', 'PUT', 'POST'])
def keywords():

    requestData = request.json
    pid = requestData['pid']

    if(request.method == 'POST'):
        timestamp = requestData['timestamp']
        sendData = {}
        sendData[timestamp] = requestData
        diagnosis_keywords.document(pid).set(sendData)
        data = {
            "message": "Keywords stored!!!",
            "pid": pid,
            "timestamp": timestamp
        }
        return data

    elif request.method == 'PUT':
        '''
            #This is exactly same as the previous API.

            #Now this is interesting, please note carefully. 
            When the doctor is gonna update it when the user visits second time, 
            Here, the previous json object will be called using get and then the current one will be appended,
            so that it becomes an array of objects according to timestamp. 

            #Thats just json, manipulation, in the api, we will just update the value, whenever a put request is received.
        '''
        # The requestData will obviously change as is sent in the request.

        timestamp = requestData['timestamp']
        data = diagnosis_keywords.document(pid).get()
        print(data)
        data = data.to_dict()
        json_data = {}
        print(data)
        for key in data.keys():
            json_data[key] = data[key]
        print(json_data)
        json_data[timestamp] = requestData
        diagnosis_keywords.document(pid).update(json_data)
        data = {
            "message": "Keywords updated",
            "pid": pid,
        }
        return data

    # This will be used while generating the prescription.
    elif(request.method == 'GET'):
        data = diagnosis_keywords.document(pid).get()
        return jsonify(data.to_dict())

    else:
        return "Invalid request"


@app.route('/')
def index():
    return "Welcome to DocAid-API"


@app.route('/socket_conn', methods=['POST'])
def socket_server():

    # Work for raghav: pull user data from firebase and put it in data
    # if data not in firebase, return unsuccessful

    data = request.json
    pid = data['pid']
    data = patient_details.document(pid).get()
    data = pickle.dumps(data.to_dict())
    client.send(data)
    return "Hello World"

           


if __name__ == '__main__':
    host = "34.93.231.96"
    # host = socket.gethostname()
    # port = 5500

    # client = socket.socket()
    # client.connect((host, port))
    app.run(debug=True)
