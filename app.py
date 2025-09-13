from flask import Flask, redirect, render_template, request, url_for
import sys
import mysql.connector as sql

conn = sql.connect(
    host='127.0.0.1',
    user='root',
    password='Sakshi@1922',
    database='vital_nest_flask_solution',
    port=3306,
    auth_plugin='mysql_native_password',
    use_pure=True
    )
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
        if real_passwd == passwd:
            query = "insert into log_table (aadhar) values({})".format(aadhar)
            curr.execute(query)
            conn.commit()
            user_type = res[1]
            if user_type=="hospital":
                query = "select hsp_id from hsp_identity where manager_id = {}".format(aadhar)
                res = curr.execute(query)
                hsp_id = curr.fetchone()[0] 
                print(hsp_id)
                return render_template('hospital_dashboard.html', hsp_id = hsp_id)
            elif user_type=="distributor":
                return render_template('supplier_dashboard.html')
            elif user_type=="industry":
                query = "select ind_id from ind_identity where manager_id = {}".format(aadhar)
                res = curr.execute(query)
                ind_id = curr.fetchone()[0]
                print(ind_id) 
                query = "select * from medicine_data where ind_id = '{}'".format(ind_id)
                medicines = curr.fetchall()
                print(medicines)
                return render_template('industry_dashboard.html', ind_id = ind_id, medicines = medicines)
            elif user_type=="Rep":
                return render_template("representative_dashboard.html")
            else:
                sql = "select name, aadhar, mobile, user_type  from acl_list where user_type<>'admin'"
                curr.execute(sql)
                Users_data = curr.fetchall()
                sql = "select aadhar, log_timestamp from log_table order by log_timestamp desc"
                curr.execute(sql)
                Log_data = curr.fetchall()
                sql = "select * from inventory_data order by hsp_id, supplier_id , supplied_timestamp desc"
                curr.execute(sql)
                supply_data = curr.fetchall()
                sql = "select hsp_identity.hsp_id, hsp_identity.manager_id, acl_list.mobile from hsp_identity join acl_list on acl_list.aadhar = hsp_identity.manager_id"
                curr.execute(sql)
                hsp_data = curr.fetchall()
                return render_template('admin_dashboard.html', admin_id = aadhar, users = Users_data, logs = Log_data, supply = supply_data, hsp_data = hsp_data)
        else:
            print("Passwd Not Matching try again....")
            return render_template('index.html')    

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

@app.route('/newMedicine', methods=["GET", "POST"])
def addNewMedicine():
    med_name = request.form.get('med_name')
    uses = request.form.get('uses')
    side_effects = request.form.get('side_effects')
    ind_id = request.form.get('ind_id')
    query = "insert into medicine_data values('{}', '{}', '{}', '{}')".format(ind_id, med_name, uses, side_effects)
    curr.execute(query)
    conn.commit()
    print("new medicine's data has been sent successfully")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug = True)