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
    else:
        response['valid'] = False

    return flask.jsonify(response)


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
    else:
        response['status'] = False

    return flask.jsonify(response)


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


if __name__ == '__main__':
    app.run()
