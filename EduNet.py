from datetime import datetime

import flask
from bson import ObjectId
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
    adhaar = req['adhaar']

    client = MongoClient()
    db = client.edunet
    users = db.User

    user = users.insert_one({
        'name': name,
        'username': adhaar,
        'password': adhaar,
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
        'adhaar': adhaar,
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
        'fromDate': today.strftime('%Y-%m-%d'),
        'toDate': today.strftime('%Y-%m-%d'),
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


@app.route('/student/enroll/pending', methods=['POST'])
def get_enroll_pending_students():
    req = flask.request.json
    university = req['university']

    client = MongoClient()
    db = client.edunet
    certificates = db.Certificate

    student_list = []

    students = db.Student
    users = db.User
    students = students.find({'university': university})
    certified_students = certificates.find({'university': university})
    certified_students = list(map(lambda x: ObjectId(x['certifiedUser']), certified_students))
    for student in students:
        if student['userId'] not in certified_students:
            user = users.find_one({'_id': student['userId']})
            student['user'] = user
            student_list.append(student)

    response = {'status': 200, 'data': student_list}

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

    university_obj = users.find_one({'_id': ObjectId(university)})
    cert_list = []
    for certificate in certificates.find({'university': university}):
        user = certificate['certifiedUser']
        student = students.find_one({'userId': ObjectId(user)})
        if student:
            student['user'] = users.find_one({'_id': ObjectId(user)})
            certificate['student'] = student
            certificate['university'] = university_obj
            cert_list.append(certificate)

    return JSONEncoder().encode(cert_list)


@app.route('/user/profile/get', methods=['POST'])
def get_user_profile():
    req = flask.request.json
    userId = req['userId']

    client = MongoClient()
    db = client.edunet
    certificates = db.Certificate
    students = db.Student
    users = db.User
    experiences = db.Experience

    certificate = certificates.find_one({'certifiedUser': userId})
    if certificate:
        user = certificate['certifiedUser']
        student = students.find_one({'userId': ObjectId(user)})
        if student:
            student['user'] = users.find_one({'_id': ObjectId(user)})
            certificate['student'] = student
            response = {'status': 200, 'data': certificate}
        else:
            response = {'status': 205, 'data': 'no student found'}

        certificate['experience'].pop(0)
        exp_ids = certificate['experience']
        for exp_id, i in zip(exp_ids, range(len(exp_ids))):
            exp = experiences.find_one({'_id': ObjectId(exp_id)})
            comp = exp['company']
            comp = users.find_one({'_id': ObjectId(comp)})
            exp['company'] = comp
            exp_ids[i] = exp
        university = users.find_one({'_id': ObjectId(certificate['university'])})
        certificate['university'] = university
    else:
        response = {'status': 205, 'data': 'no certificate found'}

    return JSONEncoder().encode(response)


@app.route('/company/hire', methods=['POST'])
def hire_employee():
    req = flask.request.json
    companyId = req['companyId']
    userId = req['userId']
    department = req['department']
    role = req['role']

    client = MongoClient()
    db = client.edunet

    employees = db.Employee
    employees.insert_one({
        'company': companyId,
        'user': userId,
        'department': department,
        'role': role,
        'doj': datetime.now(),
        'active': True
    })

    response = {'status': 200}

    return flask.jsonify(response)


@app.route('/company/employees', methods=['POST'])
def get_all_employee():
    req = flask.request.json
    company = req['company']

    client = MongoClient()
    db = client.edunet

    employees = db.Employee
    users = db.User
    empl_list = list(employees.find({'company': company, 'active': True}))
    for emp in empl_list:
        user = users.find_one({'_id': ObjectId(emp['user'])})
        emp['user'] = user
    return JSONEncoder().encode(empl_list)


@app.route('/company/employee/relieve', methods=['POST'])
def add_experience():
    req = flask.request.json
    userId = req['userId']
    id = req['id']
    client = MongoClient()
    db = client.edunet
    experiences = db.Experience
    employees = db.Employee
    certificates = db.Certificate

    employee = employees.find_one({'user': userId})
    company = employee['company']
    fromDate = employee['doj']

    exp_object = {
        'fromDate': fromDate,
        'toDate': datetime.now(),
        'company': company
    }
    experience = experiences.insert_one(exp_object)
    experience_id = experience.inserted_id
    exp_object['experienceId'] = experience_id
    exp_object['$class'] = 'com.app.edunet.Experience'

    certificates.update_one({'certifiedUser': userId},
                            {'$push': {'experience': experience_id}})

    employees.update({'_id': ObjectId(id)}, {'$set': {'active': False}})
    return JSONEncoder().encode(exp_object)


@app.route('/home/status', methods=['GET'])
def get_home_status():
    client = MongoClient()
    db = client.edunet

    users = db.User
    certificates = db.Certificate
    employees = db.Employee

    response = {
        'users': len(list(users.find({}))),
        'certificate': len(list(certificates.find({}))),
        'employee': len(list(employees.find({})))
    }

    return flask.jsonify(response)


@app.route('/user/profile/update', methods=['POST'])
def update_profile():
    client = MongoClient()
    db = client.edunet
    users = db.User

    req = flask.request.json
    userId = req['userId']
    name = req['name']
    password = req['password']

    users.update({'_id': ObjectId(userId)}, {'$set': {'name': name, 'password': password}})

    response = {'status': 200}
    return flask.jsonify(response)


if __name__ == '__main__':
    app.run()
