from flask import Flask, redirect, render_template, request, url_for
import sys
import mysql.connector as sql
from werkzeug.security import generate_password_hash, check_password_hash

conn = sql.connect(
    host='127.0.0.1',
    user='root',
    password='Pavitra@01',
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
        if check_password_hash(real_passwd, passwd):
            query = "insert into log_table (aadhar) values({})".format(aadhar)
            curr.execute(query)
            conn.commit()
            user_type = res[1]
            if user_type=="Hospital":
                query = "select hsp_id from hsp_identity where manager_id = {}".format(aadhar)
                res = curr.execute(query)
                hsp_id = curr.fetchone()[0]
                query = "select supplier_id, medicine_name, quantity, ind_id from medicine_data_replica_for_hospitals where quantity<>0 order by supplier_id, ind_id"
                curr.execute(query)
                inven_data = curr.fetchall()
                query = "select med_name, quantity from medicine_data_for_patients where hsp_id = '{}' and quantity > 0".format(hsp_id)
                curr.execute(query)
                patient_meds = curr.fetchall()
                return render_template('hospital_dashboard.html', hsp_id = hsp_id, data = inven_data, patient_meds = patient_meds)
            elif user_type=="distributor":
                query = "select * from medicine_data"
                curr.execute(query)
                data = curr.fetchall()
                query = "select * from inventory_data_industry_to_supplier where supplier_id = {}".format(aadhar)
                curr.execute(query)
                inventory_data = curr.fetchall()
                query = "select * from inventory_request_to_supplier_by_hospital where supplier_id = '{}'".format(aadhar)
                curr.execute(query)
                request_data = curr.fetchall()
                return render_template('supplier_dashboard.html', data = data, manager_id = aadhar, inventory_data = inventory_data, request_data = request_data)
            elif user_type=="industry":
                query = "select ind_id from ind_identity where manager_id = {}".format(aadhar)
                res = curr.execute(query)
                ind_id = curr.fetchone()[0]
                query = "select * from medicine_data where ind_id = '{}'".format(ind_id)
                curr.execute(query)
                medicines = curr.fetchall()
                query = "select * from inventory_request_to_industry_by_supplier where ind_id = '{}'".format(ind_id)
                curr.execute(query)
                request_data = curr.fetchall()
                return render_template('industry_dashboard.html', ind_id = ind_id, medicines = medicines, request_data = request_data)
            elif user_type=="Rep":
                return render_template("representative_dashboard.html")
            elif user_type=="payer":
                return render_template("payer_dashboard.html", aadhar=aadhar)
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
                sql = "select name, aadhar, mobile, user_type, request_timestamp, passwd from registration_approval_data where approval_status = 'not approved'"
                curr.execute(sql)
                approval_data = curr.fetchall()
                return render_template('admin_dashboard.html', admin_id = aadhar, users = Users_data, logs = Log_data, supply = supply_data, hsp_data = hsp_data, approval_data = approval_data)
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
    hashed_passwd = generate_password_hash(passwd)
    print(len(hashed_passwd))
    if utype == 'payer':
        query = "insert into acl_list (name, aadhar, mobile, passwd, user_type) values('{}', {}, {}, '{}', '{}')".format(name, aadhar, mobile, hashed_passwd, utype)
        curr.execute(query)
        conn.commit()
        return redirect(url_for('home'))
    else:
        query = "insert into registration_approval_data (name, aadhar, mobile, passwd, user_type) values('{}', {}, {}, '{}', '{}')".format(name, aadhar, mobile, hashed_passwd, utype)
        curr.execute(query)
        conn.commit()
        return redirect(url_for('home'))

@app.route('/newMedicine', methods=["GET", "POST"])
def addNewMedicine():
    med_name = request.form.get('med_name')
    uses = request.form.get('uses')
    side_effects = request.form.get('side_effects')
    ind_id = request.form.get('ind_id')
    query = "insert into medicine_data (ind_id, medicine_name, uses, side_effects) values('{}', '{}', '{}', '{}')".format(ind_id, med_name, uses, side_effects)
    curr.execute(query)
    conn.commit()
    query = "select aadhar from acl_list where user_type = 'distributor'"
    curr.execute(query)
    sup_ids = curr.fetchall()
    for i in sup_ids:
        query = "insert into medicine_data_replica_for_hospitals (ind_id, medicine_name, supplier_id) values('{}','{}','{}')".format(ind_id, med_name, i[0])
        curr.execute(query)
        conn.commit()
    return redirect(url_for('home'))

@app.route('/billPatient', methods=["GET", "POST"])
def billPatient():
    hsp_id = request.form.get('hsp_id')
    aadhar = request.form.get('aadhar')
    item = request.form.get('item')
    quantity = request.form.get('quantity')
    query = "insert into patient_data (p_id, item, quantity, hsp_id) VALUES (%s, %s, %s, %s)"
    curr.execute(query, (aadhar, item, int(quantity), hsp_id))
    update_query = "update medicine_data_for_patients set quantity = quantity - {} where hsp_id = '{}' and med_name = '{}'".format(int(quantity), hsp_id, item)
    curr.execute(update_query)
    conn.commit()
    query = "select supplier_id, medicine_name, quantity, ind_id from medicine_data_replica_for_hospitals where quantity<>0 order by supplier_id, ind_id"
    curr.execute(query)
    inven_data = curr.fetchall()
    query = "select med_name, quantity from medicine_data_for_patients where hsp_id = '{}' and quantity > 0".format(hsp_id)
    curr.execute(query)
    patient_meds = curr.fetchall()
    return render_template('hospital_dashboard.html', hsp_id = hsp_id, data = inven_data, patient_meds = patient_meds)

@app.route('/addTreatmentRecord', methods=["GET", "POST"])
def addTreatmentRecord():
    hsp_id = request.form.get('hsp_id')
    aadhar = request.form.get('p_id')
    disease_remark = request.form.get('disease_remark')
    treatment_remark = request.form.get('treatment_remark')
    query = "insert into treatment_record (p_id, disease_remark, treatment_remark, hsp_id) values('{}','{}','{}','{}')".format(aadhar, disease_remark, treatment_remark, hsp_id)
    curr.execute(query)
    conn.commit()
    query = "select supplier_id, medicine_name, quantity, ind_id from medicine_data_replica_for_hospitals where quantity<>0 order by supplier_id, ind_id"
    curr.execute(query)
    inven_data = curr.fetchall()
    query = "select med_name, quantity from medicine_data_for_patients where hsp_id = '{}' and quantity > 0".format(hsp_id)
    curr.execute(query)
    patient_meds = curr.fetchall()
    return render_template('hospital_dashboard.html', hsp_id = hsp_id, data = inven_data, patient_meds = patient_meds)

@app.route('/patientRecords', methods=["GET", "POST"])
def patientRecords():
    aadhar = request.form.get('aadhar')
    hsp_id = request.form.get('hsp_id')
    query = "select * from treatment_record where p_id = '{}'".format(aadhar)
    curr.execute(query)
    records = curr.fetchall()
    query = "insert into patient_records_accessed_log_data (hsp_id, p_id) values('{}', '{}')".format(hsp_id, aadhar)
    curr.execute(query)
    conn.commit()
    return render_template('patient_records.html', hsp_id = hsp_id, records = records)

@app.route("/patientRecordsLogData", methods=["GET", "POST"])
def patientRecordsLogData():
    p_id = request.form.get('aadhar')
    query = "select * from patient_records_accessed_log_data where p_id = '{}'".format(p_id)
    curr.execute(query)
    records = curr.fetchall()
    return render_template('patient_records_logs.html', records = records)

@app.route('/approveUser', methods=["GET", "POST"])
def approveUser():
    name = request.form.get('name')
    aadhar = request.form.get('aadhar')
    mobile = request.form.get('mobile')
    type = request.form.get('type')
    passwd = request.form.get('passwd')
    action = request.form.get('action')
    query = "select name, aadhar, mobile, user_type from acl_list where aadhar = {}".format(aadhar)
    curr.execute(query)
    details = curr.fetchall()
    if len(details)>0 and action == 'approve':
        return "User already exists with the details like this: " + ", ".join([str(row) for row in details])
    elif action == 'reject':
        query = "delete from registration_approval_data where aadhar = {}".format(aadhar)
        curr.execute(query)
        conn.commit()
        print("Rejection of this user is successful")
        return "Rejected Successfully"
    else:
        hashed_passwd = generate_password_hash(passwd)
        query = "insert into acl_list values('{}', {}, {}, '{}', '{}')".format(name, aadhar, mobile, hashed_passwd, type)
        curr.execute(query)
        conn.commit()
        query = "delete from registration_approval_data where aadhar = '{}'".format(aadhar)
        curr.execute(query)
        conn.commit()
        return "Approved Successfully"

@app.route('/updateMedicineQuantity', methods=["GET", "POST"])
def updateQuantity():
    updated_quantity = int(request.form.get('quant')) + int(request.form.get('quant_update'))
    med_name = request.form.get('name')
    query = "update medicine_data set quantity = {} where medicine_name = '{}'".format(updated_quantity, med_name)
    curr.execute(query)
    conn.commit()
    return "Update Successfull"

@app.route('/removeMedicine', methods=["GET", "POST"])
def removeMedicine():
    med_name = request.form.get('name')
    query = "select * from medicine_data where medicine_name = '{}'".format(med_name)
    curr.execute(query)
    data = curr.fetchall()
    ind_id = data[0][0]
    med_name = data[0][1]
    uses = data[0][2]
    side_effects = data[0][3]
    query = "insert into unregistered_medicine_data(ind_id, medicine_name, uses, side_effects) values('{}','{}','{}','{}')".format(ind_id, med_name, uses, side_effects)
    curr.execute(query)
    conn.commit()
    query = "delete from medicine_data where medicine_name = '{}'".format(med_name)
    curr.execute(query)
    conn.commit()
    return "Medicine Unregistering Successful"

@app.route('/requestInventory', methods=["GET", "POST"])
def requestInventory():
    supplier_id = request.form.get('supplier_id')
    quantity = request.form.get('quantity')
    ind_id = request.form.get('ind_id')
    med_name = request.form.get('med_name')
    query = "insert into inventory_request_to_industry_by_supplier(supplier_id, quantity, ind_id, med_name) values('{}', {}, '{}', '{}')".format(supplier_id, quantity, ind_id, med_name)
    curr.execute(query)
    conn.commit()
    return "Inventory Request fetch is successful"

@app.route('/sendInventory', methods=["GET", "POST"])
def sendInventory():
    supplier_id = request.form.get('supplier_id')
    ind_id = request.form.get('ind_id')
    med_name = request.form.get('med_name')
    quantity = request.form.get('quantity')
    action = request.form.get('action')
    if(action == 'approve'):
        query = "update medicine_data set quantity = quantity - {} where ind_id = '{}' and medicine_name = '{}'".format(quantity, ind_id, med_name)
        curr.execute(query)
        conn.commit()
        query = "insert into inventory_data_industry_to_supplier (supplier_id, quantity, ind_id, med_name) values({}, {}, '{}', '{}')".format(supplier_id, quantity, ind_id, med_name)
        curr.execute(query)
        conn.commit()
        query = "update medicine_data_replica_for_hospitals set quantity = quantity + {} where supplier_id = '{}'".format(quantity, supplier_id)
        curr.execute(query)
        conn.commit()
        query = "delete from inventory_request_to_industry_by_supplier where supplier_id = '{}' and med_name = '{}'".format(supplier_id, med_name)
        curr.execute(query)
        conn.commit()
    else:
        query = "delete from inventory_request_to_industry_by_supplier where supplier_id = '{}' and med_name = '{}'".format(supplier_id, med_name)
        curr.execute(query)
        conn.commit()
    return "Send Inventory data is Successful"

@app.route('/requestInventoryByHospital', methods=["GET", "POST"])
def requestInventoryByHospital():
    print("Entered Bhai")
    supplier_id = request.form.get('supplier_id')
    quantity = request.form.get('quant')
    ind_id = request.form.get('ind_id')
    med_name = request.form.get('med_name')
    hsp_id = request.form.get('hsp_id')
    query = "insert into inventory_request_to_supplier_by_hospital(supplier_id, quantity, ind_id, med_name, hsp_id) values('{}', {}, '{}', '{}', '{}')".format(supplier_id, quantity, ind_id, med_name, hsp_id)
    curr.execute(query)
    conn.commit()
    return "Inventory Request fetch from hospital is successful"

@app.route('/sendInventoryToHospital', methods=["GET", "POST"])
def sendInventoryToHospital():
    supplier_id = request.form.get('supplier_id')
    hsp_id = request.form.get('hsp_id')
    med_name = request.form.get('med_name')
    quantity = request.form.get('quantity')
    action = request.form.get('action')
    if(action == 'approve'):
        query = "update medicine_data_replica_for_hospitals set quantity = quantity - {} where supplier_id = '{}' and medicine_name = '{}'".format(quantity, supplier_id, med_name)
        curr.execute(query)
        conn.commit()
        query = "insert into inventory_data_supplier_to_hospital (supplier_id, quantity, hsp_id, med_name) values({}, {}, '{}', '{}')".format(supplier_id, quantity, hsp_id, med_name)
        curr.execute(query)
        conn.commit()
        check_query = "select quantity from medicine_data_for_patients where hsp_id = '{}' and med_name = '{}'".format(hsp_id, med_name)
        curr.execute(check_query)
        result = curr.fetchone()
        if result:
            new_quantity = result[0] + int(quantity)
            update_query = "update medicine_data_for_patients set quantity = {} where hsp_id = '{}' and med_name = '{}'".format(new_quantity, hsp_id, med_name)
            curr.execute(update_query)
        else:
            insert_query = "insert into medicine_data_for_patients (quantity, hsp_id, med_name) values({}, '{}', '{}')".format(quantity, hsp_id, med_name)
            curr.execute(insert_query)
        conn.commit()
        query = "delete from inventory_request_to_supplier_by_hospital where hsp_id = '{}' and med_name = '{}'".format(hsp_id, med_name)
        curr.execute(query)
        conn.commit()
    else:
        print("HSP ID", hsp_id)
        print("Medicine Name", med_name)
        query = "delete from inventory_request_to_supplier_by_hospital where hsp_id = '{}' and med_name = '{}'".format(hsp_id, med_name)
        curr.execute(query)
        conn.commit()
    return "Send Inventory data by Hospital is Successful"

@app.route('/viewPatientBills', methods=["GET", "POST"])
def viewPatientBills():
    p_id = request.form.get('p_id')
    hsp_id = request.form.get('hsp_id')
    query = "select * from patient_data where p_id = '{}' and hsp_id = '{}'".format(p_id, hsp_id)
    curr.execute(query)
    bills = curr.fetchall()
    return render_template('patient_bills.html', bills=bills, hsp_id=hsp_id)

@app.route('/createCrowdfundingDemand', methods=["GET", "POST"])
def createCrowdfundingDemand():
    p_id = request.form.get('p_id')
    total_demand = request.form.get('total_demand')
    required_donation = request.form.get('required_donation')
    query = "insert into patient_crowd_funding_demand (p_id, total_demand, required_donation) values('{}', {}, {})".format(p_id, total_demand, required_donation)
    curr.execute(query)
    conn.commit()
    return "Crowdfunding demand created successfully"

@app.route('/viewCrowdfundingDemands', methods=["GET", "POST"])
def viewCrowdfundingDemands():
    query = "select p_id, total_demand, required_donation, date_of_register from patient_crowd_funding_demand"
    curr.execute(query)
    demands_raw = curr.fetchall()
    demands = []
    for demand in demands_raw:
        p_id = demand[0]
        query_sum = "select sum(amount) from payers_crowd_funding_data where p_id = '{}'".format(p_id)
        curr.execute(query_sum)
        received = curr.fetchone()[0]
        if received is None:
            received = 0
        demands.append(demand + (received,))
    return render_template('crowdfunding_demands.html', demands=demands)

@app.route('/payCrowdfunding', methods=["GET", "POST"])
def payCrowdfunding():
    p_id = request.form.get('p_id')
    payer_id = request.form.get('payer_id')
    amount = int(request.form.get('amount'))
    gateway = request.form.get('gateway')
    query = "select required_donation from patient_crowd_funding_demand where p_id = '{}'".format(p_id)
    curr.execute(query)
    result = curr.fetchone()
    if not result:
        return "No crowdfunding demand found for this patient."
    required_donation = result[0]
    query = "select sum(amount) from payers_crowd_funding_data where p_id = '{}'".format(p_id)
    curr.execute(query)
    received_result = curr.fetchone()
    received = received_result[0] if received_result[0] else 0
    remaining = required_donation - received
    if amount > remaining:
        return "Payment amount exceeds the remaining demand. Remaining amount needed: {}".format(remaining)
    query = "insert into payers_crowd_funding_data (p_id, payer_id, amount, gateway) values('{}', '{}', {}, '{}')".format(p_id, payer_id, amount, gateway)
    curr.execute(query)
    conn.commit()
    return "Payment successful"

if __name__ == "__main__":
    app.run(debug = True)
