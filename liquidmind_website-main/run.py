from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from datetime import datetime, timedelta
import hashlib
import mysql.connector
from mysql.connector import Error
from decimal import Decimal
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Liquidmind.AI!@#$%^&*'
bcrypt = Bcrypt(app)

config = {
    'host': 'mysql-53ffb30-pradeepmajji42-ae7a.e.aivencloud.com',      
    'port': 22015,                  
    'user': 'avnadmin',       
    'password': 'AVNS_j7LEzLWZO2EscHzvNdr',  
    'database': 'liquidmind'     
}

connection = mysql.connector.connect(**config)

def generate_msme_id(email):
    now = datetime.now()
    datetime_str = now.strftime('%Y%m%d%H%M%S%f')
    unique_str = email + datetime_str
    user_id = hashlib.sha256(unique_str.encode()).hexdigest()
    return user_id

def generate_vendor_id(name):
    now = datetime.now()
    datetime_str = now.strftime('%Y%m%d%H%M%S%f')
    unique_str = name + datetime_str
    user_id = hashlib.sha256(unique_str.encode()).hexdigest()
    return user_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():

    name = request.form['name']
    phone_number = request.form['phone_number']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    erp = request.form['erp']
    erp_id = request.form['erp_id']
    msme_industry = request.form['industry']


    if password != confirm_password:
        flash('Passwords do not match!', 'warning')
        return redirect(url_for('index'))

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM MSME WHERE MSME_EMAIL = %s", (email,))
        existing_msme = cursor.fetchone()

        if existing_msme:
            flash('Email already exists!', 'warning')
            return redirect(url_for('index'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        msme_id = generate_msme_id(email)

        insert_query = """
        INSERT INTO MSME (MSME_ID, MSME_NAME, MSME_PHONE, MSME_EMAIL, MSME_PASSWORD, MSME_ERP, MSME_ERP_ID, MSME_INDUSTRY)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (msme_id, name, phone_number, email, hashed_password, erp, erp_id, msme_industry))
        connection.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('index'))

    except Error as e:
        print(f"Error in registration: {e}")
        flash('Registration failed. Please try again later.', 'error')
        return redirect(url_for('index'))

    finally:
        cursor.close()

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM MSME WHERE MSME_EMAIL = %s", (email,))
        msme = cursor.fetchone()

        if not msme or not bcrypt.check_password_hash(msme[4], password):
            flash('Login Unsuccessful. Please check email and password.', 'error')
            return redirect(url_for('index'))

        session['MSME_ID'] = msme[0]
        return redirect(url_for('dashboard'))

    except Error as e:
        print(f"Error in login: {e}")
        flash('Login failed. Please try again later.', 'error')
        return redirect(url_for('index'))

    finally:
        cursor.close()

@app.route('/dashboard')
def dashboard():
    print(session)
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/google_login')
def google_login():
    pass

@app.route('/vendor_register', methods=['GET', 'POST'])
def vendor_register():
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    msme_id = session['MSME_ID']
    if request.method == 'POST':
        vendor_name = request.form['vendor_name']
        payment_gateway = request.form['payment_gateway']
        payment_link = request.form['payment_link']
        vendor_industry = request.form['vendor_industry']
        vendor_phone = request.form['vendor_phone']
        vendor_email = request.form['vendor_email']
        vendor_id = generate_vendor_id(vendor_name)
        try:
            cursor = connection.cursor()
            insert_query = """
            INSERT INTO VENDOR (VENDOR_ID, MSME_ID, VENDOR_NAME, VENDOR_PHONE_NUMBER, VENDOR_EMAIL, VENDER_PAYMENT_GATEWAY, VENDOR_PAYMENT_GATEWAY_LINK, VENDOR_INDUSTRY)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (vendor_id, msme_id, vendor_name, vendor_phone, vendor_email, payment_gateway, payment_link, vendor_industry))
            connection.commit()
            flash('Vendor registration successful!', 'success')
            return redirect(url_for('vendor_register'))
        except Error as e:
            print(f"Error in vendor registration: {e}")
            flash('Vendor registration failed. Please try again later.', 'error')
            return redirect(url_for('vendor_register'))
        finally:
            cursor.close()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT VENDOR_ID, VENDOR_NAME, VENDOR_PHONE_NUMBER, VENDOR_EMAIL, VENDER_PAYMENT_GATEWAY, VENDOR_PAYMENT_GATEWAY_LINK, VENDOR_INDUSTRY FROM VENDOR WHERE MSME_ID = %s", (msme_id,))
        vendors = cursor.fetchall()
    except Error as e:
        print(f"Error in fetching vendors: {e}")
        vendors = []
    finally:
        cursor.close()
    return render_template('vendor_register.html', vendors=vendors)

@app.route('/edit_vendor/<vendor_id>', methods=['GET', 'POST'])
def edit_vendor(vendor_id):
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        vendor_name = request.form['vendor_name']
        vendor_phone = request.form['vendor_phone']
        vendor_email = request.form['vendor_email']
        payment_gateway = request.form['payment_gateway']
        payment_link = request.form['payment_link']
        vendor_industry = request.form['vendor_industry']
        try:
            cursor = connection.cursor()
            update_query = """
            UPDATE VENDOR
            SET VENDOR_NAME = %s, VENDOR_PHONE_NUMBER = %s, VENDOR_EMAIL = %s, VENDER_PAYMENT_GATEWAY = %s, VENDOR_PAYMENT_GATEWAY_LINK = %s, VENDOR_INDUSTRY = %s
            WHERE VENDOR_ID = %s
            """
            cursor.execute(update_query, (vendor_name, vendor_phone, vendor_email, payment_gateway, payment_link, vendor_industry, vendor_id))
            connection.commit()
            flash('Vendor details updated successfully!', 'success')
            return redirect(url_for('vendor_register'))
        except Error as e:
            print(f"Error in updating vendor: {e}")
            flash('Failed to update vendor details. Please try again later.', 'error')
        finally:
            cursor.close()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM VENDOR WHERE VENDOR_ID = %s", (vendor_id,))
        vendor = cursor.fetchone()
    except Error as e:
        print(f"Error in fetching vendor details: {e}")
        vendor = None
    finally:
        cursor.close()
    if not vendor:
        flash('Vendor not found.', 'error')
        return redirect(url_for('vendor_register'))
    return render_template('edit_vendor.html', vendor=vendor)

@app.route('/delete_vendor/<vendor_id>', methods=['POST'])
def delete_vendor(vendor_id):
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    try:
        cursor = connection.cursor()
        delete_query = "DELETE FROM VENDOR WHERE VENDOR_ID = %s"
        cursor.execute(delete_query, (vendor_id,))
        connection.commit()
        flash('Vendor removed successfully!', 'success')
    except Error as e:
        print(f"Error in removing vendor: {e}")
        flash('Failed to remove vendor. Please try again later.', 'error')
    finally:
        cursor.close()
    return redirect(url_for('vendor_register'))

@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    
    MSME_ID = session.get('MSME_ID')
    
    if request.method == 'POST':
        data = request.get_json()
        selected_date = data.get('selected_date')
        
        try:
            cursor = connection.cursor()
            query = """
                SELECT inst.*, v.VENDOR_NAME
                FROM INSTALLMENT inst
                JOIN INVOICE inv ON inst.INVOICE_ID = inv.INVOICE_ID
                JOIN VENDOR v ON inv.VENDOR_ID = v.VENDOR_ID
                WHERE inv.MSME_ID = %s
                    AND inst.SELECTED_DATE = %s
                    AND inst.STATUS = 'PENDING';
            """
            cursor.execute(query, (MSME_ID, selected_date))
            installments = cursor.fetchall()
        except Exception as e:
            print(f'Exception Raised: {e}')
            installments = []
        finally:
            cursor.close()

        return jsonify(installments=installments)
    
    else:
        current_date = datetime.now().date()
        selected_date = current_date.strftime('%Y-%m-%d')
        
        try:
            cursor = connection.cursor()
            query = """
                SELECT inst.*, v.VENDOR_NAME
                FROM INSTALLMENT inst
                JOIN INVOICE inv ON inst.INVOICE_ID = inv.INVOICE_ID
                JOIN VENDOR v ON inv.VENDOR_ID = v.VENDOR_ID
                WHERE inv.MSME_ID = %s
                    AND inst.SELECTED_DATE = %s
                    AND inst.STATUS = 'PENDING';
            """
            cursor.execute(query, (MSME_ID, selected_date))
            installments = cursor.fetchall()
        except Exception as e:
            print(f'Exception Raised: {e}')
            installments = []
        finally:
            cursor.close()

        return render_template('n_calendar.html', installments=installments)

@app.route('/get_selected_dates', methods=['GET'])
def get_selected_dates():
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    selected_dates = []
    try:
        cursor = connection.cursor()
        MSME_ID = session.get('MSME_ID')
        query = """
            SELECT DISTINCT SELECTED_DATE
            FROM INSTALLMENT inst
            JOIN INVOICE inv ON inst.INVOICE_ID = inv.INVOICE_ID
            WHERE inv.MSME_ID = %s
                AND inst.STATUS = 'PENDING';
        """
        cursor.execute(query, (MSME_ID,))
        result = cursor.fetchall()
        selected_dates = [row[0].strftime('%Y-%m-%d') for row in result]
    except Exception as e:
        print(f'Exception Raised: {e}')
    finally:
        cursor.close()
    return jsonify(selected_dates)


@app.route('/user_installments',methods=['GET', 'POST'])
def user_installments():
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    msme_id=session.get('MSME_ID')
    cursor=connection.cursor()
    query = """
    SELECT 
        i.INSTALLMENT_ID, 
        v.VENDOR_NAME, 
        v.VENDOR_INDUSTRY, 
        inv.INVOICE_NUMBER, 
        i.SELECTED_DATE,
        inv.DUE_DATE,
        i.AMOUNT
    FROM 
        INSTALLMENT i
    JOIN 
        INVOICE inv ON i.INVOICE_ID = inv.INVOICE_ID
    JOIN 
        VENDOR v ON inv.VENDOR_ID = v.VENDOR_ID
    WHERE 
        inv.MSME_ID = %s
        AND i.STATUS = 'PENDING'
    """

    cursor.execute(query, (msme_id,))
    results = cursor.fetchall()
    cursor.close()

    data = []
    for row in results:
        data.append({
            'installment_id': row[0],
            'vendor_name': row[1],
            'vendor_industry': row[2],
            'invoice_number': row[3],
            'selected_date' : row[4],
            'due_date' : row[5],
            'amount': row[6]
        })

    return render_template('pending_installments.html', data=data)

@app.route('/get_dashboard',methods=['GET'])
def get_dashboard():
    print(session)
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    msme_id = session['MSME_ID']
    cursor=connection.cursor()
    try:

        # Total Invoices Amount
        cursor.execute("SELECT SUM(INVOICE_TOTAL_AMOUNT) FROM INVOICE WHERE MSME_ID = %s", (msme_id,))
        total_invoices_amount = cursor.fetchone()[0] or Decimal('0.00')

        print(f'total_invoices_amount {total_invoices_amount}')

        # Total Amount Paid Still Now (including PAY_NOW and successful INSTALLMENTS)
        cursor.execute("""
        SELECT 
            COALESCE(SUM(PN.TOTAL_AMOUNT_PAID), 0) + COALESCE((SELECT SUM(AMOUNT) FROM INSTALLMENT WHERE INVOICE_ID IN (SELECT INVOICE_ID FROM INVOICE WHERE MSME_ID = %s) AND STATUS = 'PAID'), 0) AS total_paid
        FROM 
            PAY_NOW PN 
        JOIN 
            INVOICE I ON PN.INVOICE_ID = I.INVOICE_ID 
        WHERE 
            I.MSME_ID = %s
         """, (msme_id, msme_id))
        total_amount_paid = cursor.fetchone()[0] or Decimal('0.00')

        print(f'total_amount_paid {total_amount_paid}')

        #Due Amount To Paid
        cursor.execute(""" 
        SELECT 
            COALESCE((SELECT SUM(AMOUNT) FROM INSTALLMENT WHERE INVOICE_ID IN (SELECT INVOICE_ID FROM INVOICE WHERE MSME_ID = %s) AND STATUS = 'PENDING'), 0) AS total_paid
        """,(msme_id,))
        total_amount_due = cursor.fetchone()[0] or Decimal('0.00')
        print(f'Total Amount Due: {total_amount_due}')

        # Number of Invoice
        cursor.execute("SELECT COUNT(*) FROM INVOICE WHERE MSME_ID = %s", (msme_id,))
        number_of_invoices = cursor.fetchone()[0]

        print(f'number_of_invoices {number_of_invoices}')

        # Number of Invoice They Paid
        cursor.execute("SELECT COUNT(*) FROM INVOICE WHERE MSME_ID = %s AND INVOICE_STATUS = 'PAID'", (msme_id,))
        number_of_invoices_paid = cursor.fetchone()[0]

        print(f'number_of_invoices_paid {number_of_invoices_paid}')


        # Number of invoices in Due
        cursor.execute("SELECT COUNT(*) FROM INVOICE WHERE MSME_ID = %s AND INVOICE_STATUS = 'PENDING'", (msme_id,))
        number_of_invoices_due = cursor.fetchone()[0]

        print(f'number_of_invoices_due {number_of_invoices_due}')


        # Number of Invoice in Over Due
        cursor.execute("SELECT COUNT(*) FROM INVOICE WHERE MSME_ID = %s AND INVOICE_STATUS = 'Over Due'", (msme_id,))
        number_of_invoices_overdue = cursor.fetchone()[0]

        print(f'number_of_invoices_overdue {number_of_invoices_overdue}')


        # Invoices Due Today (count and sum amount)
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*), SUM(AMOUNT) FROM INSTALLMENT I JOIN INVOICE INV ON I.INVOICE_ID = INV.INVOICE_ID WHERE INV.MSME_ID = %s AND I.SELECTED_DATE = %s AND I.STATUS = 'PENDING'", (msme_id, today))
        invoices_due_today_count, amount_due_today = cursor.fetchone()
        amount_due_today = amount_due_today or Decimal('0.00')

        print(f'invoices_due_today_count {invoices_due_today_count}')
        print(f'amount_due_today {amount_due_today}')


        # Total Vendors
        cursor.execute("SELECT COUNT(DISTINCT VENDOR_NAME) FROM VENDOR WHERE MSME_ID = %s", (msme_id,))
        total_vendors = cursor.fetchone()[0]

        print(f'total_vendors {total_vendors}')


        # Next 7 Days Due Payments
        next_week = today + timedelta(days=7)
        cursor.execute("SELECT V.VENDOR_NAME, I.SELECTED_DATE, I.AMOUNT FROM INSTALLMENT I JOIN INVOICE INV ON I.INVOICE_ID = INV.INVOICE_ID JOIN VENDOR V ON INV.VENDOR_ID = V.VENDOR_ID WHERE INV.MSME_ID = %s AND I.SELECTED_DATE BETWEEN %s AND %s AND I.STATUS = 'PENDING'", (msme_id, today, next_week))        
        next_7_days_due_payments = cursor.fetchall()
        print(next_7_days_due_payments)

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
    finally:
        cursor.close()

    return render_template('dashboard_page.html', 
                        total_invoices_amount=total_invoices_amount,
                        total_amount_paid=total_amount_paid,
                        total_amount_due=total_amount_due,
                        number_of_invoices=number_of_invoices,
                        number_of_invoices_paid=number_of_invoices_paid,
                        number_of_invoices_due=number_of_invoices_due,
                        number_of_invoices_overdue=number_of_invoices_overdue,
                        invoices_due_today_count=invoices_due_today_count,
                        amount_due_today=amount_due_today,
                        total_vendors=total_vendors,
                        next_7_days_due_payments=next_7_days_due_payments)
@app.route('/logout')
def logout():
    if 'MSME_ID' not in session:
        return redirect(url_for('index'))
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
