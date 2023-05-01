from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from datetime import timedelta
from .helpRoutes import *   # this is used to import all functions from 'helpRoutes.py' 
from .accept import *


app = Flask(__name__)
auth = HTTPBasicAuth()

db_name = "users_libraries_books" 

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",                       # that's because I do not use a password... you may change it for your DBMS
    database=db_name   # a database I created to play with...
)

    

def get_admin():
    cursor = db.cursor()
    sql = "select username, password from User where type='admin';"
    cursor.execute(sql)
    p = cursor.fetchall()[0]
    #print(p)
    return p
# Set the username and password for authentication
# Use @auth.login_required to make a route private...
users = {
    "dev": "chatgpt"
}



# Verify the username and password for each request
@auth.verify_password
def verify_password(username, password):
    if username in users and password == users[username] or username==get_admin()[0] and password==get_admin()[1]:
        return username

# Add the authentication decorator to the route
@app.route('/page')
@auth.login_required
def private_page():
    # Your private route code here
    return jsonify({"message": "This is a private page"})

## in order to use the db "users_and_libraries" 
##  Apache and MySQL should be running...
## run the page '/create' which creates db and schema

## and then '/insert-user' which inserts data into table User
## and then '/insert-lib' which inserts data into table School-Library
## and then '/insert-signup-approval' which inserts data into table SignUp_Approval
## and then '/insert-book' which inserts books in db and their characteristics
## and then '/insert-available' which inserts books into several schools

## All these can be done with '/insert'

## sign in operates according to the database (or not if you use the JS comments in "sign-in.html" 
## and the appropriate code in python)
## Attention!! when you run '/create' database drops and a new is created 
## So all data are lost !

###### Example using sakila database ####### (change above database="sakila")
'''
@app.route("/categories")
def category():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM category")
    categories = cursor.fetchall()
    out = ''
    for tup in categories:
        out = out + tup[1] + '<br>'
    return out #str(categories)
'''

# run '/' to see the home page
@app.route("/")
def home():
    return render_template('home.html')

# This is a simple routing example 
# If you want to make an html page, you should put it into directory 'templates'
@app.route("/sample")
def sample_route():
    return sample()


# create schema ...
@app.route("/create")
@auth.login_required
def create_route():
    return create(db)

# insert all
@app.route("/insert")
@auth.login_required
def insert_route():
    return insert(db)

# insert data into User 
@app.route('/insert-user')
@auth.login_required
def insert_user_route():
    return insert_user(db)

# insert data into School_Library 
@app.route('/insert-lib')
@auth.login_required
def insert_lib_route():
    return insert_lib(db)

# insert data into Book
@app.route('/insert-book')
@auth.login_required
def insert_book_route():
    return insert_book(db)

# inserts all the existing books in several schools ..
@app.route('/insert-available')
@auth.login_required
def insert_available_route():
    return insert_available(db)

# inserts all existing in the DB Users to the table Signup_Approval
# correlated by a random school
# should be done only when Signup_Approval is empty set ! 
# so that there will be no duplicate entry errors
@app.route('/insert-signup-approval')
@auth.login_required
def insert_signup_approval_route():
    return insert_signup_approval(db)

@app.route("/signup", methods=['GET', 'POST'])
def signup_form_redirect():
    if request.method == 'POST':
        username = request.form.get('username')    
        password = request.form.get('pass1')     ### pass1 is the name! of the input field
        type = request.form.get('userType')
        school = request.form.get('school')
        birth_date = request.form.get('birth_date')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        print(school)
        address = school.split(',')[1]
        print(address)
        cursor = db.cursor()
                 
        query = "select * from School_Library where address='{}'".format(address)
        cursor.execute(query)
        schoolExists = cursor.fetchall()

        if schoolExists:
            # insert into User
            try:
                sql_query = """insert into User values('{u}', '{p}', '{t}','0','{d}','{f}','{l}')"""
                cursor.execute(sql_query.format(u=username, p=password, t=type, d=birth_date, f=first_name, l=last_name))
                db.commit()
                # insert into Signup_Approval
                sql_query = """insert into Signup_Approval values('{}','{}')""".format(username, address)
                cursor.execute(sql_query)
                db.commit()
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
                return 'Insertion Error: <br> maybe username is already used!'
        else:
            return 'school selected does not exist in database'
        return redirect('not-approved-user/{}'.format(username))
    else:
        return render_template('sign-up.html')

# returns json object with schools from the database 
# in order to be used in JS - Sign-up page
@app.route('/schools-list')
def schools_list_route():
    return get_schools_list(db)

@app.route("/signin", methods=['GET', 'POST'])
def handle_signin():
    if request.method == 'POST':     # here I handle post request by submitting the sign in form
        
        username = request.form.get('username')    
        password = request.form.get('pass')     ### pass is the name! of the input field
        
        # the below are written using the database

        cursor = db.cursor()
        sql_query = """select * from User where username='{u}'"""
        cursor.execute(sql_query.format(u=username))
        user = cursor.fetchall()
        if not user: return 'User not found'
        correct_password = user[0][1] 
        if password != correct_password: return 'Incorrect Password!'
        else: 
            valid = user[0][3]
            if valid: 
                type = user[0][2]
                if type=='librarian':
                    return redirect('/librarian/{}'.format(username))
                elif type == 'admin':
                    return redirect('/{}/admin'.format(username))
                else:
                    return redirect('/simple-user/{}/{}'.format(type,username))
                    #return 'Succesfull login!  <br><br> valid user &emsp;' + username
            else: return redirect('/not-approved-user/{}'.format(username))
        
        ##### the below handles post request if you do not use a database
        '''
        if username == 'nikospapa':
            return redirect(url_for('student'))
        else:
            return redirect(url_for('notApprovedUser'))
        '''
    else:
        return render_template('sign-in.html')

@app.route("/not-approved-user/<username>")
def notApprovedUser(username):
    cursor = db.cursor()
    sql = "select type from User where username='{}'".format(username)
    cursor.execute(sql)
    type = cursor.fetchall()[0][0]
    out = ''
    if type=='librarian': out += 'Wait for the admin to validate you <br>'
    else:
        sql = '''select L.username, A.address, L.type
                from User L, Signup_Approval S, Signup_Approval A
                where S.username="{}" and  S.address=A.address and A.username=L.username and L.type="librarian" and L.valid=1;'''.format(username)
        cursor.execute(sql)
        librarians = cursor.fetchall()
        
        if not librarians: out += 'There are no valid librarians in this school. You will wait for your validation until there is a valid librarian for your school'
        else:
            out += 'One of those librarians may validate you: <br>'
            for lib in librarians:
                out += lib[0] + '<br>'
    return render_template('not-approved-user.html', username=username) + out

@app.route('/notValidLibrarians')
@auth.login_required
def notValidLibrarians():
    cursor = db.cursor()
    # find librarians that are not approved yet
    cursor.execute("SELECT * FROM User join Signup_Approval on User.username = Signup_Approval.username where valid=0 and type='librarian';")
    notValidLibrarians = cursor.fetchall()
    # 
    out = 'Not valid librarians (username, password) <br>'
    for tup in notValidLibrarians:
        out = out + tup[0] + ' ' + tup[1] + ' ' + tup[2] + ' ' + str(tup[3]) + ' ' + tup[4] + ' ' + tup[5] +  '<br>'
    
    return jsonify(notValidLibrarians=notValidLibrarians) 

@app.route('/accept-librarians', methods=['GET', 'POST'])
@auth.login_required
def accept_libs_route():
    return accept_librarians(db)

@app.route('/<username>/admin')
@auth.login_required
def admin(username):
    return render_template('admin.html', username=username)

@app.route("/simple-user/<type>/<username>")
def simple_user(type, username):
    if not is_internal_request(): abort(401)
    return render_template('simple-user.html', type=type, username=username)

@app.route("/simple-user/<type>/<username>/card")
def simple_user_card(type, username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = "select birth_date, first_name, last_name from User where username='{}'".format(username)
    cursor.execute(sql)
    birth_date, first_name, last_name = cursor.fetchall()[0]
    return '''Card of the valid member of School Library Network <br> {} ({}) <br>
               Birth Date = {} <br>
                First Name = {} <br>
                 Last Name = {} <br> '''.format(username, type, birth_date, first_name, last_name)

@app.route("/librarian/<username>")
def librarian(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    q = "select address from Signup_Approval where username='{}'".format(username)
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address:
        return render_template("librarian.html", username=username, address=address)
    else:
        return 'An error occured!'

@app.route("/librarian/<lib_username>/accept-users", methods=['GET', 'POST'])
def accept_users_route(lib_username):
    return accept_users(db, lib_username)

@app.route("/librarian/<lib_username>/disable-users", methods=['GET', 'POST'])
def disable_users_route(lib_username):
    return disable_users(db, lib_username)

@app.route('/librarian/<lib_username>/notValidUsers')
def notValidUsers_route(lib_username):
    return ValidUsers(db, lib_username, 0)      # valid=0

@app.route('/librarian/<lib_username>/ValidUsers')
def ValidUsers_route(lib_username):
    return ValidUsers(db, lib_username, 1)     # valid=1

@app.route('/librarian/<username>/insert-book', methods = ['GET', 'POST'])
def insert_book_by_lib(username):
    return insert_book_by_librarian(db, username)


@app.route('/insert-school', methods=['GET', 'POST'])
def insert_school_route():
    return insert_school(db)

@app.route('/<username>/change-password', methods=['GET', 'POST'])
def change_password_route(username):
    return change_password(db, username)

@app.route('/backup', methods = ['GET', 'POST'])
@auth.login_required
def backup_route():
    return backup(db, db_name)

@app.route('/restore', methods = ['GET', 'POST'])
@auth.login_required
def restore_route():
    return restore(db, db_name)

if __name__ == '__main__':
    app.run(debug=True)