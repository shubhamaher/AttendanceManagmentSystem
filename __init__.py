from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
from pymongo import MongoClient
import bcrypt
import simplejson as json
import time
from bson.objectid import ObjectId

app = Flask(__name__)

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'attendman'
mongo = PyMongo(app)


# @app.route('/')
# def index():
# 	if 'username' in session:
# 		username = session['username']
# 		return render_template('index.html',username=username)
	# return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
	user = None
	role =  request.form['role']
	if role == 'staff':
		newrole = request.form['classsub']
		if newrole == 'cls':
			user = mongo.db.class_teacher
		else:
			user = mongo.db.subject_teacher
	else:
		user = mongo.db.principle

	login_user = user.find_one({'name' : request.form['username']})

	if login_user:
		if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
			session['username'] = request.form['username']
			return redirect(url_for('index'))

	return 'Invalid username/password combination'
	

@app.route('/addclassteacher', methods=['POST', 'GET'])
def addclassteacher():
	if request.method == 'POST':
		if 'username' in session:
			username = session['username']
			ifprinciple = mongo.db.principle.find_one({'name' : username })
			if ifprinciple:
				staff = mongo.db.class_teacher
				existing_user = staff.find_one({'standard' : request.form['std'],'division' : request.form['div']})
				if existing_user is None:
					hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
					staff.insert({'name' : request.form['username'],'email' : request.form['email'],'phon' : request.form['phon'],'standard' : request.form['std'],'division' : request.form['div'],'password' : hashpass})
					if mongo.db.staff.find_one({'name' : request.form['username']}) is None:
						mongo.db.staff.insert({'name' : request.form['username'],'email' : request.form['email'],'phon' : request.form['phon']})
					return "Added Successfully"
				return "Class teacher for requested class already assigned."
		return "Access Denied"
	return render_template('addclassteacher.html')


@app.route('/addsubjectteacher', methods=['POST', 'GET'])
def addsubjectteacher():
	if request.method == 'POST':
		if 'username' in session:
			username = session['username']
			ifprinciple = mongo.db.principle.find_one({'name' : username })
			if ifprinciple:
				staff = mongo.db.subject_teacher
				existing_user = staff.find_one({'name' : request.form['username']})
				if existing_user is None:
					hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
					staff.insert({'name' : request.form['username'],'email' : request.form['email'],'phon' : request.form['phon'],'standard' : request.form['std'],'division' : request.form['div'],'subject': request.form['sub'],'password' : hashpass})
					if mongo.db.staff.find_one({'name' : request.form['username']}) is None:
						mongo.db.staff.insert({'name' : request.form['username'],'email' : request.form['email'],'phon' : request.form['phon']})
					return "Added Successfully"
				else:
					if existing_user['subject'] == request.form['sub'] and existing_user['standard'] == request.form['std'] and existing_user['division'] == request.form['div']:
						return "Subject teacher for requested class,division and subject already assigned."
					else:
						staff.insert({'name' : request.form['username'],'email' : request.form['email'],'phon' : request.form['phon'],'standard' : request.form['std'],'division' : request.form['div'],'subject': request.form['sub'],'password' : existing_user['password']})
						return "Subject teacher added with new standard,division and subject...password carry forwarded.."
			return "Access Denied"
	return render_template('addsubjectteacher.html')




@app.route('/addstudent', methods=['POST', 'GET'])
def addstudent():
	if request.method == 'POST':
		if 'username' in session:
			username = session['username']
			stud = mongo.db.class_teacher.find_one({'name' : username })
			if stud:
				stdd = stud['standard']
				divi = stud['division']
				stud = mongo.db.students
				if stud.find_one({'standard' : stdd, 'division' : divi, 'rollno' : request.form['roll']}):
					return "Student already exist with same details..."
				else:
					stud.insert({'name' : request.form['name'],'standard' : stdd, 'division' : divi, 'rollno' : request.form['roll'],'email' : request.form['email'],'phon' : request.form['phon']})
					return 'Student Added...'
		return  'Access Denied...'
	return render_template('addstudent.html')
multi = []

@app.route('/attendance')
def attendance():
	if 'username' in session:
				username = session['username']
				ifsubject = mongo.db.subject_teacher.find({'name' : username})
				if ifsubject:
					multi = []
					for i in ifsubject:
						multi.append(i)
	return render_template('studentattendance.html',multii=multi)
studentfill = []

@app.route('/studentattendance',methods=['POST','GET'])
def studentattendance():
	if request.method == 'POST':
		field = request.form['field']
		std = field[ field.find('standard')+13 : field.find('u',field.find('standard')+8)+3 ]
		div = field[ field.find('division')+13 : field.find('u',field.find('division')+8)+3 ]
		sub = field[ field.find('subject')+12 : -2]
		collect = mongo.db.students.find({"standard" : std,"division" : div})
		studentfill = []
		for i in collect:
			studentfill.append(i)
		return render_template('fillstudentattendance.html',records=studentfill)

@app.route('/fillstudentattendance',methods=['POST','GET'])
def fillstudentattendance():
	ppresennt = ''
	present = None
	username = session['username']
	match = mongo.db.subject_teacher.find_one({'name' : username})
	presents = request.form.getlist('field')
	for i in presents:
		present = mongo.db.students.find_one( {'_id' :  ObjectId(i)  })
		if present:
			ppresennt = '112'
			if mongo.db.student_attendance.find_one({'rollno': present['rollno'] ,'standard' :present['standard'] ,'division' :present['division'] ,'subject' : match['subject'],'date' : time.strftime('%d:%m:%Y') , 'time' : time.strftime('%H:00') }) is None:
				mongo.db.student_attendance.insert({'rollno': present['rollno'] ,'standard' :present['standard'] ,'division' :present['division'] ,'subject' : match['subject'],'date' : time.strftime('%d:%m:%Y') , 'time' : time.strftime('%H:00') , 'attendace': 'present' })
				return 'Updated'
			else:
				return "Not Allowed..."
	return str(ppresennt)

@app.route('/logout/')
def logout():

	session.pop('username',None)
	return render_template('login.html')

if __name__ == '__main__':
	app.secret_key = 'mySecret'
	app.run(debug=True)
