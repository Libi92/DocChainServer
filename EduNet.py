from datetime import datetime

import flask
from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

from JSONEncoder import JSONEncoder

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login', methods=['POST'])
def login():
    req = flask.request.json
    username = req['username']
    password = req['password']

    client = MongoClient()
    db = client.edunet
    users = db.User
    user = users.find_one({'username': username, 'password': password})
    response = {'status': 200}
    if user:
        response['valid'] = True
        response['userType'] = user['userType']
        response['user'] = user
    else:
        response['valid'] = False

    return JSONEncoder().encode(response)


@app.route('/register', methods=['POST'])
def register():
    req = flask.request.json
    name = req['name']
    username = req['username']
    password = req['password']
    userType = req['userType']

    client = MongoClient()
    db = client.edunet
    users = db.User
    user = users.insert_one({
        'name': name,
        'username': username,
        'password': password,
        'userType': userType
    })
    response = {'status': 200}
    if user:
        response['valid'] = True
        response['user'] = user.inserted_id
    else:
        response['valid'] = False

    return JSONEncoder().encode(response)


@app.route('/student/create', methods=['POST'])
def create_student():
    req = flask.request.json
    name = req['name']
    registerNo = req['registerNo']
    department = req['department']
    degree = req['degree']
    college = req['college']
    year = req['year']
    university = req['university']

    client = MongoClient()
    db = client.edunet
    users = db.User

    user = users.insert_one({
        'name': name,
        'username': registerNo,
        'password': registerNo,
        'userType': 'student'
    })

    students = db.Student

    student = students.insert_one({
        'userId': user.inserted_id,
        'registerNo': registerNo,
        'department': department,
        'degree': degree,
        'college': college,
        'year': year,
        'university': university
    })

    response = {'status': 200}

    if student:
        response['status'] = True
        response['student'] = user.inserted_id
    else:
        response['status'] = False

    return JSONEncoder().encode(response)


@app.route('/student/get', methods=['POST'])
def get_student():
    req = flask.request.json
    university = req['university']

    client = MongoClient()
    db = client.edunet
    students = db.Student
    students_data = list(students.find({'university': university}))
    users = db.User
    for student in students_data:
        user = users.find_one({'_id': student['userId']})
        student['user'] = user
    response = {'status': 200, 'data': students_data}

    return JSONEncoder().encode(response)


@app.route('/student/enroll', methods=['POST'])
def enroll_student():
    today = datetime.today()
    current_year = today.year

    req = flask.request.json
    user = req['user']
    degree = req['degree']
    university = req['university']
    marks = req['marks']

    client = MongoClient()
    db = client.edunet
    experiences = db.Experience
    exp_object = {
        'fromYear': current_year,
        'toYear': current_year,
        'company': university
    }
    experience = experiences.insert_one(exp_object)
    experience_id = experience.inserted_id
    exp_object['experienceId'] = experience_id
    exp_object['$class'] = 'com.app.edunet.Experience'

    cert_object = {
        "degree": degree,
        "year": current_year,
        "active": True,
        "marks": marks,
        "certifiedUser": user,
        "university": university,
        "experience": [
            experience_id
        ]
    }

    certificates = db.Certificate
    certificate = certificates.insert_one(cert_object)
    certificate_id = certificate.inserted_id
    cert_object['$class'] = 'com.app.edunet.Certificate'
    cert_object['certificateId'] = certificate_id

    del exp_object['_id']
    del cert_object['_id']
    response = {'status': 200, 'experience': exp_object, 'certificate': cert_object}
    return JSONEncoder().encode(response)


@app.route('/student/enroll/get', methods=['POST'])
def get_enrolled_students():
    req = flask.request.json
    university = req['university']

    client = MongoClient()
    db = client.edunet
    certificates = db.Certificate
    students = db.Student
    users = db.User

    student_list = []
    for certificate in certificates.find({'university': university}):
        user = certificate['certifiedUser']
        student = students.find_one({'userId': user})
        if student:
            student['user'] = users.find_one({'_id': user})
            student_list.append(student)

    return JSONEncoder().encode(student_list)


if __name__ == '__main__':
    app.run()
