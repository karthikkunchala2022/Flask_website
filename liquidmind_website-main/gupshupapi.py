import requests
import json
import uuid
import hashlib
import os
import base64
import time
import veryfi

class GupshupAPI:
    def __init__(self, api_key, source,CONSERVATION_STEP,TYPE_DISCOUNT,MEDIA_URL,TRANSCATIONS,TOKENS,PARTIAL_AMOUNT,MSME_ID,VENDOR_ID,INVOICE_ID,INSTALLMENT_ID,SENDER,TNXID,REQURIED_FIELDS,DISCOUNT,PAY_PARTIAL_ID,TYPE_OVERDUE,OVERDUE,ITEM_LIST):
        self.api_key = api_key
        self.source = source
        self.base_url = "https://api.gupshup.io/wa/api/v1"
        self.CONSERVATION_STEP=CONSERVATION_STEP
        self.TYPE_DISCOUNT=TYPE_DISCOUNT
        self.MEDIA_URL=MEDIA_URL
        self.TRANSCATIONS=TRANSCATIONS
        self.TOKENS=TOKENS
        self.PARTIAL_AMOUNT=PARTIAL_AMOUNT
        self.MSME_ID=MSME_ID
        self.VENDOR_ID=VENDOR_ID
        self.INVOICE_ID=INVOICE_ID
        self.INSTALLMENT_ID=INSTALLMENT_ID
        self.SENDER=SENDER
        self.TNXID=TNXID
        self.REQURIED_FIELDS=REQURIED_FIELDS
        self.DISCOUNT=DISCOUNT
        self.PAY_PARTIAL_ID=PAY_PARTIAL_ID
        self.TYPE_OVERDUE=TYPE_OVERDUE
        self.OVERDUE=OVERDUE
        self.ITEM_LIST=ITEM_LIST



    def send_message(self, destination, message):
        url = f"{self.base_url}/msg"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': self.api_key
        }
        payload = {
            'src.name':'LakshmanaVinay',
            'channel': 'whatsapp',
            'source': self.source,
            'destination': destination,
            'message': message
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()
    
    def send_template(self, destination, message):
        print(f'Destination Is: {destination}')
        url = f"{self.base_url}/msg"
        headers = {
            'cache-control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': self.api_key
        }
        payload = {
            'src.name':'LakshmanaVinay',
            'channel': 'whatsapp',
            'source': self.source,
            'destination': destination,
            'message': json.dumps(message)
        }
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response content:", response.text)
            response.raise_for_status()
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            print("Failed to decode JSON response:")
            print(response.text)
            raise e
    
    def send_text(self, destination, text):
        message = f'{{"type":"text","text":"{text}"}}'
        return self.send_message(destination, message)

    def send_media(self, destination, MEDIA_URL, media_type):
        message = f'{{"type":"{media_type}","originalUrl":"{self.MEDIA_URL}"}}'
        return self.send_message(destination, message)
    
    def send_interactive_template(self, destination, body, button1, button2,button3):
        message={
            "type":"quick_reply",
            "content":{
                "type":"text",
                "text":body
            },
            "options":[
                {
                    "type":"text",
                    "title":button1,
                    "postbackText":button1
                },
                {
                    "type":"text",
                    "title":button2,
                    "postbackText":button2
                },
                {
                    "type":"text",
                    "title":button3,
                    "postbackText":button3
                }
            ]
        }
        self.send_template(destination, message)
    def send_start_conservation(self,destination,body):
        message={
            "type":"quick_reply",
            "content":{
                "type":"text",
                "text":body
            },
            "options":[
                {
                    "type":"text",
                    "title":"Installment Pay",
                    "postbackText":"installment_pay"
                },
                {
                    "type":"text",
                    "title":"Start",
                    "postbackText":"start_liquidmind"
                },
                {
                    "type":"text",
                    "title":"Stop",
                    "postbackText":"quit_liquidmind"
                }
            ]
        }
        self.send_template(destination,message)
    
    def send_discount_request(self,destination,body,btn1,btn2,btn3):
        message={
            "type":"quick_reply",
            "content":{
                "type":"text",
                "text":body
            },
            "options":[
                {
                    "type":"text",
                    "title":btn1,
                    "postbackText":btn1
                },
                {
                    "type":"text",
                    "title":btn2,
                    "postbackText":btn2
                },
                {
                    "type":"text",
                    "title":btn3,
                    "postbackText":btn3
                }
            ]
        }
        self.send_template(destination, message)
    
    def send_edit_confirm_template(self,destination,extracted_data):
        message={
            "type":"quick_reply",
            "content":{
                "type":"text",
                "text":extracted_data
            },
            "options":[
                {
                    "type":"text",
                    "title":"Edit",
                    "postbackText":"edit"
                },
                {
                    "type":"text",
                    "title":"Confirm",
                    "postbackText":"confirm"
                }
            ]
        }
        self.send_template(destination,message)
    def send_message_restrict(self,destination,body):
        message={
                "type":"quick_reply",
                "content":{
                    "type":"text",
                    "text":body
                },
                "options":[
                    {
                        "type":"text",
                        "title":"Stop",
                        "postbackText":"quit_liquidmind"
                    }
                ]
            }
        self.send_template(destination,message)

    def send_message_partial(self,destination,body):
        message={
                "type":"quick_reply",
                "content":{
                    "type":"text",
                    "text":body
                },
                "options":[
                    {
                        "type":"text",
                        "title":"Continue",
                        "postbackText":"pay later"
                    }
                ]
            }
        self.send_template(destination,message)

    def extract_data_through_veryfi_api(self,image_url):
        
        client_veryfi = veryfi.Client(
            os.environ['VERYFI_CLIENT_ID'], 
            os.environ['VERYFI_CLIENT_SECRET'], 
            os.environ['VERYFI_USERNAME'], 
            os.environ['VERYFI_API_KEY']
        )
        
        categories = ['Travel', 'Airfare', 'Lodging', 'Job Suppliers and Materials', 'Grocery']
        
        res = client_veryfi.process_document_url(image_url, categories)

        #print(res)
        
        REQURIED_FIELDS = {
            "Company_Name": res.get('vendor', {}).get('raw_name', None),
            "invoice_number": res.get("invoice_number", "N/A"),
            "invoice_date": res.get("date", "N/A"),
            "due_date": res.get("due_date", "N/A"),
            "advance" : res.get("advance", 0.0),
            "discount" : res.get("discount", 0.0),
            "subtotal": res.get("subtotal", 0.0),
            "tax": res.get("tax", 0.0) if res.get("tax") is not None else 0.0,
            "total": res.get("total", 0.0)
        }

        self.REQURIED_FIELDS=REQURIED_FIELDS

        formatted_message = f"Invoice Summary:\n\n"
        formatted_message +=f"Company Name: {self.REQURIED_FIELDS['Company_Name']}\n"
        formatted_message += f"Invoice Number: {self.REQURIED_FIELDS['invoice_number']}\n"
        formatted_message += f"Invoice Date: {self.REQURIED_FIELDS['invoice_date']}\n"
        formatted_message += f"Due Date: {self.REQURIED_FIELDS['due_date']}\n"
        formatted_message += f"Subtotal: {self.REQURIED_FIELDS['subtotal']:.2f}\n"
        formatted_message += f"Tax: {self.REQURIED_FIELDS['tax']:.2f}\n"
        formatted_message += f"Total: {self.REQURIED_FIELDS['total']:.2f}\n\n"
        
        formatted_message += "Items:\n"
        for item in res.get('line_items', []):
            description = item.get('description', 'N/A')
            quantity = item.get('quantity', 0)
            unit_price = item.get('price', 0.0) 
            item_discount = item.get('discount', 0.0)
            item_tax = item.get('tax', 0.0)
            total = item.get('total', 0.0)
            self.ITEM_LIST.append([description,quantity,unit_price,item_discount,item_tax,total])
            formatted_message += (
                f"- Description: {description}\n"
                f"  Quantity: {quantity}\n"
                f"  Unit Price: {unit_price}\n"
                f"  Discount: {item_discount}\n"
                f"  Tax: {item_tax}\n"
                f"  Total: {total}\n\n"
            )

        return formatted_message
    
    def send_confirmed_message(self,destination,body):
        formatted_message = f"Invoice Summary:\n\n"
        formatted_message += f"Invoice Number: {self.REQURIED_FIELDS['invoice_number']}\n"
        formatted_message += f"Invoice Date: {self.REQURIED_FIELDS['invoice_date']}\n"
        formatted_message += f"Due Date: {self.REQURIED_FIELDS['due_date']}\n"
        formatted_message += f"Subtotal: {self.REQURIED_FIELDS['subtotal']:.2f}\n"
        formatted_message += f"Tax: {self.REQURIED_FIELDS['tax']:.2f}\n"
        formatted_message += f"Total: {self.REQURIED_FIELDS['total']:.2f}\n"
        body=body+'\n\n'+formatted_message
        return self.send_message(destination, body)

    def generate_test_payment_url(self,SENDER,DISCOUNT):
        txnid = str(uuid.uuid4())
        if self.TYPE_DISCOUNT=="percentage discount":
            amount=float(self.REQURIED_FIELDS["total"])-float(self.REQURIED_FIELDS['total'])*(float(DISCOUNT)/100)
        elif self.TYPE_DISCOUNT=="amount discount":
            amount=float(self.REQURIED_FIELDS["total"])-float(DISCOUNT)
        else:
            amount=self.REQURIED_FIELDS["total"]
        self.REQURIED_FIELDS['total']=amount
        amount=str(amount)
        firstname = "Meet"
        email = "test@gmail.com"
        phone = "9876543210"
        productinfo = "iPhone"
        key = "Eh0B0B"
        salt = "Hljr0wB63gVgZ1Aq6GWKsBKgxdw6tfAB"
        surl = "https://75ec-122-174-150-104.ngrok-free.app/success_page"
        furl = "https://75ec-122-174-150-104.ngrok-free.app/failure_page"
        hash_string = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{salt}"
        hash = hashlib.sha512(hash_string.encode()).hexdigest()
        url = "https://test.payu.in/_payment"
        payload = {
            "key": key,
            "txnid": txnid,
            "amount": amount,
            "productinfo": productinfo,
            "firstname": firstname,
            "email": email,
            "phone": phone,
            "surl": surl,
            "furl": furl,
            "hash": hash
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            self.TRANSCATIONS[txnid] = self.SENDER
            return response.url
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None 
    
    def generate_test_payment_url_partial(self,SENDER,amount):
        txnid = str(uuid.uuid4())
        amount=str(amount)
        firstname = "Meet"
        email = "test@gmail.com"
        phone = "9876543210"
        productinfo = "iPhone"
        key = "Eh0B0B"
        salt = "Hljr0wB63gVgZ1Aq6GWKsBKgxdw6tfAB"
        surl = "https://75ec-122-174-150-104.ngrok-free.app/success_page"
        furl = "https://75ec-122-174-150-104.ngrok-free.app/failure_page"
        hash_string = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{salt}"
        hash = hashlib.sha512(hash_string.encode()).hexdigest()
        url = "https://test.payu.in/_payment"
        payload = {
            "key": key,
            "txnid": txnid,
            "amount": amount,
            "productinfo": productinfo,
            "firstname": firstname,
            "email": email,
            "phone": phone,
            "surl": surl,
            "furl": furl,
            "hash": hash
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            self.TRANSCATIONS[txnid] = self.SENDER
            return response.url
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None 
    def phonepe(self,SENDER,DISCOUNT):
        if self.TYPE_DISCOUNT=="percentage discount":
            amount=float(self.REQURIED_FIELDS["total"])-float(self.REQURIED_FIELDS['total'])*(float(DISCOUNT)/100)
        elif self.TYPE_DISCOUNT=="amount discount":
            amount=float(self.REQURIED_FIELDS["total"])-float(DISCOUNT)
        else:
            amount=self.REQURIED_FIELDS["total"]
        self.REQURIED_FIELDS['total']=amount
        amount=str(amount)
        REDIRECT_URL = "https://75ec-122-174-150-104.ngrok-free.app/success_page"
        CALLBACK_URL = "https://75ec-122-174-150-104.ngrok-free.app/success"
        name = "Meet"
        email = "abc@gmail.com"
        print(amount)
        amount = float(amount)
        mobile = 7291048296
        order_id = str(int(time.time()))
        description = 'Payment for Product/Service'
        payment_data = {
            'merchantId': os.environ['PHONEPE_MERCHANT_ID'],
            'merchantTransactionId': str(uuid.uuid4()),
            'merchantUserId': "MUID123",
            'amount': int(amount * 100),
            'redirectUrl': REDIRECT_URL,
            'redirectMode': "REDIRECT",
            'callbackUrl': CALLBACK_URL,
            'merchantOrderId': order_id,
            'mobileNumber': mobile,
            'message': description,
            'email': email,
            'shortName': name,
            'paymentInstrument': {
                'type': "PAY_PAGE",
            }
        }
        self.TNXID='TNX' + payment_data['merchantTransactionId']
        json_encode = json.dumps(payment_data)
        payload_main = base64.b64encode(json_encode.encode()).decode()
        salt_index = 1
        payload = payload_main + "/pg/v1/pay" + os.environ['PHONEPE_API_KEY']
        sha256 = hashlib.sha256(payload.encode()).hexdigest()
        final_x_header = sha256 + '###' + str(salt_index)
        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": final_x_header,
            "accept": "application/json"
        }
        request_data = json.dumps({'request': payload_main})
        response = requests.post('https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/pay', headers=headers, data=request_data)
        if response.status_code == 200:
            res=response.json()
            if res.get('success')==True:
                pay_url=res['data']['instrumentResponse']['redirectInfo']['url']
                self.TRANSCATIONS[self.TNXID] = self.SENDER
                return f'{pay_url}'
            else:
                return None
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None 
    
    def phonepe_partial(self,SENDER,amount):
        amount=str(amount)
        REDIRECT_URL = "https://75ec-122-174-150-104.ngrok-free.app/success_page"
        CALLBACK_URL = "https://75ec-122-174-150-104.ngrok-free.app/success"
        name = "Meet"
        email = "abc@gmail.com"
        print(amount)
        amount = float(amount)
        mobile = 7291048296
        order_id = str(int(time.time()))
        description = 'Payment for Product/Service'
        payment_data = {
            'merchantId': os.environ['PHONEPE_MERCHANT_ID'],
            'merchantTransactionId': str(uuid.uuid4()),
            'merchantUserId': "MUID123",
            'amount': int(amount * 100),
            'redirectUrl': REDIRECT_URL,
            'redirectMode': "REDIRECT",
            'callbackUrl': CALLBACK_URL,
            'merchantOrderId': order_id,
            'mobileNumber': mobile,
            'message': description,
            'email': email,
            'shortName': name,
            'paymentInstrument': {
                'type': "PAY_PAGE",
            }
        }
        self.TNXID = 'TNX' + payment_data['merchantTransactionId']
        json_encode = json.dumps(payment_data)
        payload_main = base64.b64encode(json_encode.encode()).decode()
        salt_index = 1
        payload = payload_main + "/pg/v1/pay" + os.environ['PHONEPE_API_KEY']
        sha256 = hashlib.sha256(payload.encode()).hexdigest()
        final_x_header = sha256 + '###' + str(salt_index)
        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": final_x_header,
            "accept": "application/json"
        }
        request_data = json.dumps({'request': payload_main})
        response = requests.post('https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/pay', headers=headers, data=request_data)
        if response.status_code == 200:
            res=response.json()
            if res.get('success')==True:
                pay_url=res['data']['instrumentResponse']['redirectInfo']['url']
                self.TRANSCATIONS[self.TNXID] = self.SENDER
                return f'{pay_url}'
            else:
                return None
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None 