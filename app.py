from flask import Flask, redirect, render_template, request, url_for
import sys
import mysql.connector as sql

conn = sql.connect(host = "localhost", user = "root", passwd="Pavitra@01", database = "vital_nest_flask_solution")
if(conn.is_connected):
    print("Connected Successfully")
else:
    print("Connection is interrupted")
    sys.exit()
curr = conn.cursor()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    aadhar = request.form.get('aadhar')
    passwd = request.form.get('passwd')
    query = "select exists(select 1 from acl_list where aadhar = {})".format(aadhar)
    curr.execute(query)
    if(curr.fetchone()[0]==0):
        print("User not Found")
        return render_template('index.html')
    else:
        query = "select passwd, user_type from acl_list where aadhar = {}".format(aadhar)
        curr.execute(query)
        res = curr.fetchone()
        real_passwd = res[0]
        user_type = res[1]
        print(real_passwd)
        print(user_type)
        if user_type=="Hospital":
            return render_template('hospital_dashboard.html')
        elif user_type=="Supplier":
            return render_template('supplier_dashboard.html')
        elif user_type=="Industry":
            return render_template('industry_dashboard.html')
        else:
            return render_template('admin_dashboard.html')    
        return "Welcome on board"

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registerToDB', methods=["GET", "POST"])
def registerToDB():
    name = request.form.get('uname')
    aadhar = request.form.get('aadhar')
    mobile = request.form.get('mobile')
    passwd = request.form.get('passwd')
    utype = request.form.get('utype')
    query = "insert into acl_list values('{}', {}, {}, '{}', '{}')".format(name, aadhar, mobile, passwd, utype)
    curr.execute(query)
    conn.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug = True)