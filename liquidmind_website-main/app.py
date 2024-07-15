from flask import Flask, request, jsonify,render_template,url_for,redirect,session
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os
import veryfi
import uuid
import hmac
import hashlib
import mysql.connector
import datetime
import time
import base64
import secrets
from gupshupapi import GupshupAPI
from flask_cors import CORS
from flask_bcrypt import Bcrypt


config = {
    'host': 'mysql-53ffb30-pradeepmajji42-ae7a.e.aivencloud.com',      
    'port': 22015,                  
    'user': 'avnadmin',       
    'password': 'AVNS_j7LEzLWZO2EscHzvNdr',  
    'database': 'liquidmind'     
}

connection = mysql.connector.connect(**config)


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.secret_key = '@A*Laxman!@$#12!^&77HG'
CORS(app)
bcrypt = Bcrypt(app)


gupshup_api = GupshupAPI(os.environ['GUPSHUP_API_KEY'], '917834811114',0,0,'',{},{},0,'','','','','','',{},0,'','',0,[])

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    message_type = data['payload']['type']
    try:
        if message_type == 'text' or message_type == 'button_reply':
            message = data['payload']['payload'].get('text') if message_type == 'text' else data['payload']['payload'].get('postbackText')
            gupshup_api.SENDER = data['payload']['source']
            if message.lower() == "quit_liquidmind":
                gupshup_api.CONSERVATION_STEP = -1
                gupshup_api.send_message(gupshup_api.SENDER, "Bye!")
            elif message.lower() in ["start_liquidmind", "installment_pay"]:
                if gupshup_api.CONSERVATION_STEP == 0 and message.lower() == "start_liquidmind":
                    gupshup_api.CONSERVATION_STEP = 1
                    gupshup_api.send_message(gupshup_api.SENDER, "Please Write Your Password!")
                elif gupshup_api.CONSERVATION_STEP == 0 and message.lower() == "installment_pay":
                    gupshup_api.CONSERVATION_STEP = 500
                    gupshup_api.send_message(gupshup_api.SENDER, "Please Write Your Password!")

            elif gupshup_api.CONSERVATION_STEP == 1:
                handle_login_process(message)
            elif gupshup_api.CONSERVATION_STEP == 500:
                handle_installment_payment_process(message)
            elif gupshup_api.CONSERVATION_STEP == 501:
                send_installment_payment_link(message)
            elif gupshup_api.CONSERVATION_STEP == 2:
                handle_edit_or_confirm_process(message)
            elif gupshup_api.CONSERVATION_STEP == 3:
                handle_payment_options(message)
            elif gupshup_api.CONSERVATION_STEP == 4:
                handle_discount_options(message)
            elif gupshup_api.CONSERVATION_STEP == 41:
                handle_partial_payment_amount(message)
            elif gupshup_api.CONSERVATION_STEP == 5:
                handle_discount_amount(message)
            elif gupshup_api.CONSERVATION_STEP == 201:
                handle_partial_payment_process(message)
            else:
                if gupshup_api.CONSERVATION_STEP == 1:
                    gupshup_api.send_message_restrict(gupshup_api.SENDER, "You are in Restrict Mode. Please upload the Invoice or select the Stop Option.")
                elif gupshup_api.CONSERVATION_STEP == 2:
                    gupshup_api.send_message_restrict(gupshup_api.SENDER, "You are in Restrict Mode. Please select Edit or Confirm or select the Stop Option.")
                else:
                    gupshup_api.CONSERVATION_STEP = 0
                    gupshup_api.send_start_conservation(gupshup_api.SENDER, "Please start the process by clicking on 'Start' or click 'Stop'.")

        elif message_type == 'image' and gupshup_api.CONSERVATION_STEP == 1:
            gupshup_api.SENDER = data['payload']['source']
            gupshup_api.MEDIA_URL = data['payload']['payload']['url']
            extracted_data = gupshup_api.extract_data_through_veryfi_api(gupshup_api.MEDIA_URL)
            gupshup_api.send_edit_confirm_template(gupshup_api.SENDER, extracted_data)
            gupshup_api.CONSERVATION_STEP = 2

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(gupshup_api.CONSERVATION_STEP)
        print(f'Error in webhook processing: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

def handle_login_process(message):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM MSME WHERE MSME_PHONE=%s", (gupshup_api.SENDER,))
        data = cursor.fetchone()
        print(data)
        if data and bcrypt.check_password_hash(data[4], message):
            gupshup_api.MSME_ID = data[0]
            gupshup_api.send_message(gupshup_api.SENDER, "Please Upload Invoice!")
            gupshup_api.CONSERVATION_STEP = 1
        else:
            gupshup_api.send_message(gupshup_api.SENDER, "Your Password Is wrong or You Haven't Registered!")
    except Exception as e:
        print(f'MSME IS NOT VERIFIED {e}')
    finally:
        cursor.close()

def handle_installment_payment_process(message):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM MSME WHERE MSME_PHONE=%s", (gupshup_api.SENDER,))
        data = cursor.fetchone()
        if data and bcrypt.check_password_hash(data[4], message):
            gupshup_api.MSME_ID = data[0]
            gupshup_api.send_message(gupshup_api.SENDER, "Please enter the Installment ID you want to pay!")
            gupshup_api.CONSERVATION_STEP = 501
        else:
            gupshup_api.send_message(gupshup_api.SENDER, "Your Password Is wrong or You Haven't Registered!")
    except Exception as e:
        print(f'MSME IS NOT VERIFIED {e}')
    finally:
        cursor.close()

def send_installment_payment_link(message):
    try:
        gupshup_api.INSTALLMENT_ID=message.lower()
        cursor=connection.cursor()
        cursor.execute("SELECT inst.*,i.MSME_ID FROM INSTALLMENT inst JOIN INVOICE i ON inst.INVOICE_ID=i.INVOICE_ID WHERE inst.INSTALLMENT_ID=%s",(gupshup_api.INSTALLMENT_ID,))
        Data=cursor.fetchone()
        print(f'Installment Data is: {Data}')
        if Data is None:
            gupshup_api.CONSERVATION_STEP=0
            gupshup_api.send_message(gupshup_api.SENDER,"Wrong Installment ID!")
        elif Data[-1]==gupshup_api.MSME_ID:
            if Data[9] == 'PENDING':
                gupshup_api.INVOICE_ID=Data[1]
                AMOUNT=Data[3]
                url=gupshup_api.phonepe_partial(gupshup_api.SENDER,AMOUNT)
                gupshup_api.send_message(gupshup_api.SENDER,"Please Pay the amount Using the following Link!")
                gupshup_api.send_message(gupshup_api.SENDER,url)
            else:
                gupshup_api.CONSERVATION_STEP=0
                gupshup_api.send_message(gupshup_api.SENDER,f"The Payment Has been Done for this Installment! Transcation ID : {Data[8]}")
        else:
            gupshup_api.CONSERVATION_STEP=0
            gupshup_api.send_message(gupshup_api.SENDER,"Wrong Installment ID!")
    except Exception as e:
        print(f'Installment Exception {e}')
    finally:
        cursor.close()

def handle_edit_or_confirm_process(message):
    if message.lower() == "edit":
        token = str(uuid.uuid4())
        gupshup_api.TOKENS[token] = gupshup_api.SENDER
        edit_url = url_for('edit', token=token, _external=True)
        gupshup_api.send_message(gupshup_api.SENDER, "Please Edit the Details Using Following link!")
        gupshup_api.send_message(gupshup_api.SENDER, edit_url)
        gupshup_api.CONSERVATION_STEP = 101
    elif message.lower() == "confirm":
        handle_confirm_process()

def handle_confirm_process():
    try:
        cursor = connection.cursor()
        name = gupshup_api.REQURIED_FIELDS['Company_Name']
        cursor.execute("SELECT VENDOR_ID FROM VENDOR WHERE VENDOR_INDUSTRY=%s AND MSME_ID=%s", (name, gupshup_api.MSME_ID))
        data = cursor.fetchone()
        gupshup_api.VENDOR_ID = data[0]
        try:
            cursor.execute("SELECT COUNT(*) FROM INVOICE WHERE INVOICE_NUMBER=%s", (gupshup_api.REQURIED_FIELDS['invoice_number'],))
            value = cursor.fetchone()
            if value[0] == 0:
                gupshup_api.send_confirmed_message(gupshup_api.SENDER, "Your Confirmed Data")
                gupshup_api.CONSERVATION_STEP = 3
                gupshup_api.send_interactive_template(
                    gupshup_api.SENDER,
                    "Please Select Any of the Given Option Below!",
                    "pay now",
                    "pay partial",
                    "pay later"
                )
            else:
                gupshup_api.send_message(gupshup_api.SENDER, "Sry! This Invoice Is already Exists in Our Database!")
                gupshup_api.CONSERVATION_STEP = 0
        except Exception as e:
            print(f'Exception in Invoice_Number Checking! {e}')
            gupshup_api.send_message(gupshup_api.SENDER, "Sry! Something Went Wrong Please Try again!")
            gupshup_api.CONSERVATION_STEP = 0
        finally:
            cursor.close()
    except Exception as e:
        print(f'Vendor Id Not Retrieved {e}')
        gupshup_api.send_message(gupshup_api.SENDER, "Please Register Your Vendor First! Or Something Error at Backend Please try again")
        gupshup_api.CONSERVATION_STEP = 0

def handle_payment_options(message):
    if message.lower() in ['pay now', 'pay later', 'pay partial']:
        if message.lower() == "pay now":
            gupshup_api.CONSERVATION_STEP = 4
            gupshup_api.send_discount_request(
                gupshup_api.SENDER,
                "Are You Have Dynamic Discount?",
                "percentage discount",
                "amount discount",
                "no discount"
            )
        elif message.lower() == "pay later":
            gupshup_api.CONSERVATION_STEP = 4
            if len(gupshup_api.INVOICE_ID)==0:
                try:
                    invoice_id = generate_hash()
                    gupshup_api.INVOICE_ID = invoice_id
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO INVOICE(INVOICE_ID,INVOICE_NUMBER,MSME_ID,VENDOR_ID,INVOICE_DATE,DUE_DATE,SUBTOTAL,TAX,INVOICE_ADVANCE,INVOICE_DISCOUNT,INVOICE_TOTAL_AMOUNT,INVOICE_STATUS) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(invoice_id,gupshup_api.REQURIED_FIELDS['invoice_number'],gupshup_api.MSME_ID,gupshup_api.VENDOR_ID,gupshup_api.REQURIED_FIELDS['invoice_date'],gupshup_api.REQURIED_FIELDS['due_date'],gupshup_api.REQURIED_FIELDS['subtotal'],gupshup_api.REQURIED_FIELDS['tax'],gupshup_api.REQURIED_FIELDS['advance'],gupshup_api.REQURIED_FIELDS['discount'],gupshup_api.REQURIED_FIELDS['total'],'PENDING'))
                    connection.commit()
                    for item in gupshup_api.ITEM_LIST:
                        cursor.execute(
                            "INSERT INTO ITEM (INVOICE_ID, ITEM, QUANTITY, UNIT_PRICE, DISCOUNT, TAX, ITEM_TOTAL_AMOUNT) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (invoice_id, item[0], item[1], item[2], item[3], item[4], item[5])
                        )
                    connection.commit()
                    gupshup_api.INVOICE_ID = invoice_id
                except Exception as e:
                    print(f'DATA IS NOT INSERTED IN INVOICE TABLE or ITEM TABLE Pay Later {e}')
                finally:
                    cursor.close()
            token = str(uuid.uuid4())
            gupshup_api.TOKENS[token] = gupshup_api.SENDER
            installment_url = url_for('installment', token=token, _external=True)
            gupshup_api.send_message(gupshup_api.SENDER, "Please Fill the Details Using Following link!")
            gupshup_api.send_message(gupshup_api.SENDER, installment_url)
        else:
            try:
                invoice_id = generate_hash()
                gupshup_api.INVOICE_ID = invoice_id
                cursor = connection.cursor()
                cursor.execute("INSERT INTO INVOICE(INVOICE_ID,INVOICE_NUMBER,MSME_ID,VENDOR_ID,INVOICE_DATE,DUE_DATE,SUBTOTAL,TAX,INVOICE_ADVANCE,INVOICE_DISCOUNT,INVOICE_TOTAL_AMOUNT,INVOICE_STATUS) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(invoice_id,gupshup_api.REQURIED_FIELDS['invoice_number'],gupshup_api.MSME_ID,gupshup_api.VENDOR_ID,gupshup_api.REQURIED_FIELDS['invoice_date'],gupshup_api.REQURIED_FIELDS['due_date'],gupshup_api.REQURIED_FIELDS['subtotal'],gupshup_api.REQURIED_FIELDS['tax'],gupshup_api.REQURIED_FIELDS['advance'],gupshup_api.REQURIED_FIELDS['discount'],gupshup_api.REQURIED_FIELDS['total'],'PENDING'))
                connection.commit()
                for item in gupshup_api.ITEM_LIST:
                    cursor.execute(
                        "INSERT INTO ITEM (INVOICE_ID, ITEM, QUANTITY, UNIT_PRICE, DISCOUNT, TAX, ITEM_TOTAL_AMOUNT) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (invoice_id, item[0], item[1], item[2], item[3], item[4], item[5])
                    )
                connection.commit()
                gupshup_api.INVOICE_ID = invoice_id
                gupshup_api.send_message(gupshup_api.SENDER, "How Much Amount Do you want To Pay?")
                gupshup_api.CONSERVATION_STEP = 41
            except Exception as e:
                print(f'DATA IS NOT INSERTED IN INVOICE TABLE Related to Pay Partial {e}')
            finally:
                cursor.close()

def handle_discount_options(message):
    if message.lower() == "percentage discount":
        gupshup_api.TYPE_DISCOUNT = "percentage discount"
        gupshup_api.send_message(gupshup_api.SENDER, f"Please write How much {gupshup_api.TYPE_DISCOUNT} do you have")
        gupshup_api.CONSERVATION_STEP = 5
    elif message.lower() == "amount discount":
        gupshup_api.TYPE_DISCOUNT = "amount discount"
        gupshup_api.send_message(gupshup_api.SENDER, f"Please write How much {gupshup_api.TYPE_DISCOUNT} do you have")
        gupshup_api.CONSERVATION_STEP = 5
    else:
        gupshup_api.TYPE_DISCOUNT = "no discount"
        gupshup_api.CONSERVATION_STEP = 6
        DISCOUNT = 0
        gupshup_api.DISCOUNT = DISCOUNT
        try:
            invoice_id = generate_hash()
            gupshup_api.INVOICE_ID = invoice_id
            cursor = connection.cursor()
            cursor.execute("INSERT INTO INVOICE(INVOICE_ID,INVOICE_NUMBER,MSME_ID,VENDOR_ID,INVOICE_DATE,DUE_DATE,SUBTOTAL,TAX,INVOICE_ADVANCE,INVOICE_DISCOUNT,INVOICE_TOTAL_AMOUNT,INVOICE_STATUS) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(invoice_id,gupshup_api.REQURIED_FIELDS['invoice_number'],gupshup_api.MSME_ID,gupshup_api.VENDOR_ID,gupshup_api.REQURIED_FIELDS['invoice_date'],gupshup_api.REQURIED_FIELDS['due_date'],gupshup_api.REQURIED_FIELDS['subtotal'],gupshup_api.REQURIED_FIELDS['tax'],gupshup_api.REQURIED_FIELDS['advance'],gupshup_api.REQURIED_FIELDS['discount'],gupshup_api.REQURIED_FIELDS['total'],'PENDING'))
            connection.commit()
            for item in gupshup_api.ITEM_LIST:
                cursor.execute(
                    "INSERT INTO ITEM (INVOICE_ID, ITEM, QUANTITY, UNIT_PRICE, DISCOUNT, TAX, ITEM_TOTAL_AMOUNT) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (invoice_id, item[0], item[1], item[2], item[3], item[4], item[5])
                )
            connection.commit()
            url = gupshup_api.phonepe(gupshup_api.SENDER, DISCOUNT)
            gupshup_api.send_message(gupshup_api.SENDER, "Please Pay the amount Using the following Link!")
            gupshup_api.send_message(gupshup_api.SENDER, url)
        except Exception as e:
            print(f'Exception In pay now Insert Invoice {e}')
        finally:
            cursor.close()

def handle_partial_payment_amount(message):
    try:
        if float(message) >= gupshup_api.REQURIED_FIELDS["total"]:
            gupshup_api.send_message(gupshup_api.SENDER, "Enter Correct Amount!")
            return
        gupshup_api.CONSERVATION_STEP = 201
        gupshup_api.PARTIAL_AMOUNT = float(message)
        url = gupshup_api.phonepe_partial(gupshup_api.SENDER, gupshup_api.PARTIAL_AMOUNT)
        gupshup_api.send_message(gupshup_api.SENDER, "Please Pay the amount Using the following Link!")
        gupshup_api.send_message(gupshup_api.SENDER, url)
    except ValueError:
        gupshup_api.send_message(gupshup_api.SENDER, "Please enter a valid number for partial payment amount")

def handle_discount_amount(message):
    try:
        if gupshup_api.TYPE_DISCOUNT == "percentage discount":
            if float(message) >= 100 or float(message) <= 0:
                gupshup_api.send_message_restrict(gupshup_api.SENDER, "Please enter valid percentage or click on 'Stop' ")
            else:
                DISCOUNT = message.lower()
                gupshup_api.DISCOUNT = DISCOUNT
                gupshup_api.CONSERVATION_STEP = 6
                try:
                    invoice_id = generate_hash()
                    gupshup_api.INVOICE_ID = invoice_id
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO INVOICE(INVOICE_ID,INVOICE_NUMBER,MSME_ID,VENDOR_ID,INVOICE_DATE,DUE_DATE,SUBTOTAL,TAX,INVOICE_ADVANCE,INVOICE_DISCOUNT,INVOICE_TOTAL_AMOUNT,INVOICE_STATUS) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(invoice_id,gupshup_api.REQURIED_FIELDS['invoice_number'],gupshup_api.MSME_ID,gupshup_api.VENDOR_ID,gupshup_api.REQURIED_FIELDS['invoice_date'],gupshup_api.REQURIED_FIELDS['due_date'],gupshup_api.REQURIED_FIELDS['subtotal'],gupshup_api.REQURIED_FIELDS['tax'],gupshup_api.REQURIED_FIELDS['advance'],gupshup_api.REQURIED_FIELDS['discount'],gupshup_api.REQURIED_FIELDS['total'],'PENDING'))
                    connection.commit()
                    for item in gupshup_api.ITEM_LIST:
                        cursor.execute(
                            "INSERT INTO ITEM (INVOICE_ID, ITEM, QUANTITY, UNIT_PRICE, DISCOUNT, TAX, ITEM_TOTAL_AMOUNT) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (invoice_id, item[0], item[1], item[2], item[3], item[4], item[5])
                        )
                    connection.commit()
                    url = gupshup_api.phonepe(gupshup_api.SENDER, DISCOUNT)
                    gupshup_api.send_message(gupshup_api.SENDER, "Please Pay the amount Using the following Link!")
                    gupshup_api.send_message(gupshup_api.SENDER, url)
                except Exception as e:
                    print(f'Exception In pay now Insert Invoice {e}')
                finally:
                    cursor.close()
    except Exception as e:
        print(f'Give Discount Wrong Formate {e}')

def handle_partial_payment_process(message):
    try:
        if float(message) >= gupshup_api.REQURIED_FIELDS["total"]:
            gupshup_api.send_message(gupshup_api.SENDER, "Enter Correct Amount!")
            return
        gupshup_api.CONSERVATION_STEP = 201
        gupshup_api.PARTIAL_AMOUNT = float(message)
        url = gupshup_api.phonepe_partial(gupshup_api.SENDER, gupshup_api.PARTIAL_AMOUNT)
        gupshup_api.send_message(gupshup_api.SENDER, "Please Pay the amount Using the following Link!")
        gupshup_api.send_message(gupshup_api.SENDER, url)
    except ValueError:
        gupshup_api.send_message(gupshup_api.SENDER, "Please enter a valid number for partial payment amount")

@app.route("/success_page", methods = ["GET", "POST"])
def success_page():
    return render_template("success.html")
@app.route("/failure_page", methods = ["GET", "POST"])
def failure_page():
    return render_template("failure.html")

@app.route('/success', methods=['POST'])
def payment_success():
    if gupshup_api.CONSERVATION_STEP==6:#Pay Now
        try:
            TIMESTAMP= datetime.datetime.now()
            cursor=connection.cursor()
            cursor.execute("INSERT INTO PAY_NOW(TRANSACTION_ID,INVOICE_ID,TOTAL_AMOUNT_PAID,DISCOUNT_TYPE,DISCOUNT_AMOUNT,OVERDUE_FEE_TYPE,OVERDUE_FEE,TIMESTAMP) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(gupshup_api.TNXID,gupshup_api.INVOICE_ID,gupshup_api.REQURIED_FIELDS['total'],gupshup_api.TYPE_DISCOUNT,gupshup_api.DISCOUNT,gupshup_api.TYPE_OVERDUE,gupshup_api.OVERDUE,TIMESTAMP))
            connection.commit()
            cursor.execute("UPDATE INVOICE SET INVOICE_STATUS=%s WHERE INVOICE_ID=%s",("PAID",gupshup_api.INVOICE_ID))
            connection.commit()
            gupshup_api.CONSERVATION_STEP=0
        except Exception as e:
            print(f'Exception In Pay Now Insert {e}')
        finally:
            cursor.close()
    if gupshup_api.SENDER:
        gupshup_api.send_message(gupshup_api.SENDER,f"Your transaction ID is {gupshup_api.TNXID} and the status is Success.")
    if gupshup_api.CONSERVATION_STEP==201:#Pay Partial 
        try:
            date=datetime.datetime.now().date()
            cursor=connection.cursor()
            installment_id=generate_installment_code()
            cursor.execute("INSERT INTO INSTALLMENT(INSTALLMENT_ID,INVOICE_ID,SELECTED_DATE,AMOUNT,DISCOUNT_TYPE,DISCOUNT_AMOUNT,OVERDUE_FEE_TYPE,OVERDUE_FEE,TRANSACTION_ID,STATUS) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(installment_id,gupshup_api.INVOICE_ID,date,gupshup_api.PARTIAL_AMOUNT,gupshup_api.TYPE_DISCOUNT,gupshup_api.DISCOUNT,gupshup_api.TYPE_OVERDUE,gupshup_api.OVERDUE,gupshup_api.TNXID,'PAID'))
            connection.commit()
            gupshup_api.REQURIED_FIELDS['total']=gupshup_api.REQURIED_FIELDS['total']-gupshup_api.PARTIAL_AMOUNT
            gupshup_api.CONSERVATION_STEP=3
            gupshup_api.send_message_partial(gupshup_api.SENDER,"Please click 'Continue' to proceed with making the remaining amounts as remainders.")
        except Exception as e:
            print(f'Exception in Partial Paid {e}')
        finally:
            cursor.close()

    if gupshup_api.CONSERVATION_STEP==501:#Installments Payments
        try:
            cursor=connection.cursor()
            cursor.execute("UPDATE INSTALLMENT SET STATUS=%s, TRANSACTION_ID=%s WHERE INSTALLMENT_ID=%s", ("PAID", gupshup_api.TNXID, gupshup_api.INSTALLMENT_ID))
            cursor.execute("SELECT INSTALLMENT_ID,STATUS FROM INSTALLMENT WHERE INVOICE_ID = %s",(gupshup_api.INVOICE_ID,))
            records=cursor.fetchall()
            count=0
            for i in records:
                if i[1] == 'PAID':
                    count+=1
            if count==len(records):
                cursor.execute("UPDATE INVOICE SET INVOICE_STATUS=%s WHERE INVOICE_ID=%s", ("PAID", gupshup_api.INVOICE_ID))
            connection.commit()
            gupshup_api.CONSERVATION_STEP=0
        except Exception as e:
            print(f'Exception in Update {e}')
        finally:
            cursor.close()
    return "Payment successful", 200


@app.route('/failure', methods=['POST']) 
def payment_failure():
    data = request.form
    txnid = data.get('txnid')
    status = data.get('status')
    gupshup_api.SENDER = gupshup_api.TRANSCATIONS.get(txnid)
    if gupshup_api.SENDER:
        gupshup_api.send_message(gupshup_api.SENDER,f"Your transaction ID is {txnid} and the status is {status}.")
    return "Payment failed", 200


@app.route("/edit")
def edit():
    token = request.args.get('token')
    from_number = gupshup_api.TOKENS.get(token)
    if not from_number:
        return "Invalid or expired token. Please start the process again on WhatsApp.", 400

    return render_template('edit.html', token=token, data=gupshup_api.REQURIED_FIELDS)

@app.route('/installment')
def installment():
    token=request.args.get('token')
    gupshup_api.SENDER=gupshup_api.TOKENS.get(token)
    if not gupshup_api.SENDER:
        return "Invalid or expired token. Please start the process again on WhatsApp.", 400
    
    return render_template("installment.html",token=token,final_amount=gupshup_api.REQURIED_FIELDS['total'])

@app.route('/confirmed_data',methods=['POST'])
def confirmed_data():
    token = request.form['token']
    gupshup_api.SENDER = gupshup_api.TOKENS.get(token)
    company_name=request.form['companyName']
    invoice_number=request.form['invoiceNumber']
    subtotal=request.form['subTotal']
    tax=request.form['tax']
    total=request.form['total']
    gupshup_api.REQURIED_FIELDS['Company_Name']=str(company_name)
    gupshup_api.REQURIED_FIELDS['invoice_number']=str(invoice_number)
    gupshup_api.REQURIED_FIELDS['subtotal']=float(subtotal)
    gupshup_api.REQURIED_FIELDS['tax']=float(tax)
    gupshup_api.REQURIED_FIELDS['total']=float(total)
    gupshup_api.CONSERVATION_STEP=2
    formatted_message = f"Invoice Summary:\n\n"
    formatted_message += f"Company Name: {gupshup_api.REQURIED_FIELDS['Company_Name']}\n"
    formatted_message += f"Invoice Number: {gupshup_api.REQURIED_FIELDS['invoice_number']}\n"
    formatted_message += f"Invoice Date: {gupshup_api.REQURIED_FIELDS['invoice_date']}\n"
    formatted_message += f"Due Date: {gupshup_api.REQURIED_FIELDS['due_date']}\n"
    formatted_message += f"Subtotal: {gupshup_api.REQURIED_FIELDS['subtotal']:.2f}\n"
    formatted_message += f"Tax: {gupshup_api.REQURIED_FIELDS['tax']:.2f}\n"
    formatted_message += f"Total: {gupshup_api.REQURIED_FIELDS['total']:.2f}\n\n"
    gupshup_api.send_edit_confirm_template(gupshup_api.SENDER,formatted_message)
    return 'Data received', 200

@app.route('/submit_installment',methods=['POST'])
def submit_installment():
    form_data = request.form.to_dict()
    token = form_data.pop('token',None)
    gupshup_api.SENDER = gupshup_api.TOKENS.get(token)

    try:
        cursor=connection.cursor()
        selected_dates=[]
        amount=[]
        for i,j in form_data.items():
            if 'amount' in i:
                amount.append(j)
            else:
                selected_dates.append(j)
        for i in range(len(selected_dates)):
            installment_id=generate_installment_code()
            cursor.execute("INSERT INTO INSTALLMENT(INSTALLMENT_ID,INVOICE_ID,SELECTED_DATE,AMOUNT,DISCOUNT_TYPE,DISCOUNT_AMOUNT,OVERDUE_FEE_TYPE,OVERDUE_FEE,TRANSACTION_ID,STATUS) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(installment_id,gupshup_api.INVOICE_ID,selected_dates[i],amount[i],gupshup_api.TYPE_DISCOUNT,gupshup_api.DISCOUNT,gupshup_api.TYPE_OVERDUE,gupshup_api.OVERDUE,None,'PENDING'))
            connection.commit()
    except Exception as e:
        print(f'NOT INSERTED IN PARTIAL OR INSTALLMENT {e}')
    finally:
        cursor.close()

    data='Your Submitted Details Are:\n'
    i=0
    for key,value in form_data.items():
        if 'amount' in key:
            data+=f'Amount: {value} '
        else:
            data+=f'Date: {value}\n'
    data+='You Will Get Remainders On that Dates!'
    gupshup_api.send_message(gupshup_api.SENDER,data)
    gupshup_api.CONSERVATION_STEP=0
    
    return 'Data received', 200

def generate_msme_id(name):
    now = datetime.datetime.now()
    datetime_str = now.strftime('%Y%m%d%H%M%S%f')
    unique_str = name + datetime_str
    user_id = hashlib.sha256(unique_str.encode()).hexdigest()
    return user_id

def generate_vendor_id(name):
    now = datetime.datetime.now()
    datetime_str = now.strftime('%Y%m%d%H%M%S%f')
    unique_str = name + datetime_str
    user_id = hashlib.sha256(unique_str.encode()).hexdigest()
    return user_id

def generate_installment_code():
    unique_code = secrets.randbelow(900000) + 100000
    return unique_code

def generate_hash():
    unique_input = str(time.time()) + str(uuid.uuid4())
    sha256 = hashlib.sha256()
    sha256.update(unique_input.encode('utf-8'))
    hash_code = sha256.hexdigest()
    return hash_code

if __name__ == '__main__':
    app.run(port=5000)
