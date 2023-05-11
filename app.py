from flask import Flask,request,jsonify,json,Blueprint ,render_template, url_for,make_response,send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from marshmallow import Schema,fields
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager,create_access_token
import psycopg2
from fpdf import FPDF
from reportlab.pdfgen import canvas
import io


auth = Blueprint('auth', __name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/Invoice'
app.config['JWT_SECRET_KEY'] = 'super-secret'
db = SQLAlchemy(app)

jwt = JWTManager(app)


class User(db.Model):
    __tablename__ = "User_table"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50),unique=True,nullable=False)
    Password = db.Column(db.String(255), nullable=False)


class Invoicedetail(db.Model):
    _tablename__="invoice_table"
    id = db.Column(db.Integer, primary_key=True)
    invoice_name = db.Column(db.String(50))
    from_name = db.Column(db.String(50),nullable=False)
    from_email = db.Column(db.String(50),nullable=False)
    from_address = db.Column(db.String(50),nullable=False)
    from_number = db.Column(db.String(50),nullable=False)
    to_name = db.Column(db.String(50),nullable=False)
    to_email = db.Column(db.String(50),nullable=False)
    to_address = db.Column(db.String(50),nullable=False)
    to_number = db.Column(db.String(50),unique=True)
    inv_number = db.Column(db.String(20),unique=True)
    inv_date = db.Column(db.Date())
    description = db.Column(db.JSON, nullable=False)
    rate = db.Column(db.Float)
    qty = db.Column(db.String(10))
    tax_rate = db.Column(db.Float)
    total = db.Column(db.Float)


class UserSchema(Schema):
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    Password = fields.String()

class InvoicedetailSchema(Schema):
    id = fields.Integer()   
    invoice_name = fields.String()
    from_name = fields.String()
    from_email = fields.String()
    from_address = fields.String()
    from_number = fields.String()
    to_name = fields.String()
    to_email = fields.String()
    to_address = fields.String()
    to_number = fields.String()
    inv_number = fields.Integer()
    inv_date = fields.Date()
    description = fields.String()
    rate = fields.Float()
    qty = fields.String()
    tax_rate = fields.Float()
    total = fields.Float()

def __init__(self, data):
    self.invoice_name = data['invoice_name']
    self.from_name = data['from_name']
    self.from_email = data['from_email']
    self.from_address = data['from_address']
    self.from_number = data['from_number']
    self.to_name = data['to_name']
    self.to_email = data['to_email']
    self.to_address = data['to_address']
    self.to_number = data['to_number']
    self.inv_number = data['inv_number']
    self.inv_date = data['inv_date']
    self.description = json.dumps(data['description']) # convert dict to JSON string
    self.tax_rate = data['tax_rate']
    self.total =  data['total']

@app.post("/api/register")
def user_register():
    data = request.get_json()
    
    if User.query.filter(User.username == data["username"]).first():
        return{"message":"username already exists."}
    
    if User.query.filter(User.email == data["email"]).first():
        return{"message":"Email already exists"}

    user = User(username= data["username"],
                email = data["email"],
                # Password=generate_password_hash(data["Password"], method='sha256')
                Password=pbkdf2_sha256.hash(data["Password"])
                
               )
   
    db.session.add(user)

    db.session.commit()

    return {"message":"user created successfully"}, 201

@app.post("/api/login")
def user_login():
    email = request.json.get("email")
    Password = request.json.get("Password")

    user = User.query.filter_by(email = email).one_or_none()

    if user :
        access_token = create_access_token(identity=email)
        response =jsonify(message='Logged in sucessfully', access_token=access_token)
        return response, 200
    else:
        return jsonify(message='login failed'), 401


# @app.post("/api/invoice")
# def create_invoice():
#     data = request.get_json()
    
#     # subtotal= (data['rate'] * data['qty'] )
#     # tax = subtotal * (data['tax_rate']/100)
#     # total = round(subtotal+tax)
   
   
#     new_invoice = Invoicedetail(
#         invoice_name = data['invoice_name'],
#         from_name  = data['from_name'],
#         from_email  = data['from_email'],
#         from_address = data['from_address'],
#         from_number  = data['from_number'],
#         to_name =  data['to_name'],
#         to_email = data['to_email'],
#         to_address = data['to_address'],
#         to_number  = data['to_number'],
#         inv_number = data['inv_number'],
#         inv_date = data['inv_date'],
#         description = data['description'],
#         rate = data['rate'],
#         qty = data['qty'],
#         tax_rate = data['tax_rate'],
#         total = total       
#     )

#     # subtotal = 0
#     # for item in description:
#     #     product = item['product']
#     #     rate = item['rate']
#     #     qty = item['qty']
#     #     total += rate * qty
#     #     invoice_item = InvoiceItem(product=product, rate=rate, qty=qty)
#     #     invoice_detail.append(invoice_item)


#     subtotal = 0
#     for product in description:
#         subtotal += product['rate'] * product['qty']
#         tax = subtotal * data['tax_rate']
#         total = round(subtotal + tax)

#     db.session.add(new_invoice)
#     db.session.commit()

    
#     return jsonify({'message': 'Invoice created  successfully.'}), 200

@app.post("/invoice")
def create_invoices():
    # Get the invoice details from the request
    data = request.get_json()
    invoice_name = request.json.get('invoice_name')  
    from_name = request.json.get('from_name')
    from_email = request.json.get('from_email')
    from_address = request.json.get('from_address')
    from_number = request.json.get('from_number')
    to_name = request.json.get('to_name')
    to_email = request.json.get('to_email')
    to_address = request.json.get('to_address')
    to_number = request.json.get('to_number')
    inv_number = request.json.get('inv_number')
    if User.query.filter(Invoicedetail.inv_number == inv_number).first():
        return{"message":"Invoice number already exists."},401
    inv_date = request.json.get('inv_date')
    description = request.json.get('description')
    rate = request.json.get('rate')
    qty = request.json.get('qty')
    tax_rate = request.json.get('tax_rate')
    total = request.json.get('total')
    
    description_json = json.dumps(data['description'])

    subtotal = 0
    for product in description:
        if product['rate'] is  not None and product['qty'] is not None:
            subtotal += product['rate'] * product['qty']
            tax = subtotal * (data['tax_rate']/100)
            total = subtotal + tax
        
   
    pdf = FPDF()
    pdf.add_page()

  
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", size=16, style='B')

    #invoice front details
    pdf.cell(200, 10, txt="INVOICE", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Invoice Number: {inv_number}", ln=1, align="L")
    pdf.cell(200, 10, txt=f"Invoice Date: {inv_date}", ln=1, align="L")
    pdf.cell(200, 10, txt=f"From: {from_name} ({from_email}), {from_address}, {from_number}", ln=1, align="L")
    pdf.cell(200, 10, txt=f"To: {to_name} ({to_email}), {to_address}, {to_number}", ln=5, align="L")

    # Add the invoice items
    pdf.set_font("Arial", size=8, style='B')
    pdf.cell(50, 10, txt="Description", border=1)
    pdf.cell(30, 10, txt="Quantity", border=1)

    pdf.cell(30, 10, txt="Rate", border=1)
    pdf.cell(30, 10, txt="Amount", border=1)
    pdf.ln()
    


    pdf.set_font("Arial", size=10)       
    for data in description:
        pdf.cell(50,10, txt=str(data['product']), border=1)
        pdf.cell(30, 10, txt=str(data['qty']), border=1)
        pdf.cell(30, 10, txt=str(data['rate']), border=1)
        amount = data['qty'] * data['rate']
        pdf.cell(30, 10, txt=str(amount), border=1)
        pdf.ln()
    
    pdf.cell(50, 10, txt="")
    pdf.cell(30, 10, txt="")
    pdf.cell(30, 10, txt="subtotal", border=1)
   #subtotal = qty *rate
    pdf.cell(30, 10, txt=str(subtotal), border=1)
    pdf.ln()
    pdf.cell(50, 10, txt="")
    pdf.cell(30, 10, txt="")
    pdf.cell(30, 10, txt="Tax", border=1)
    pdf.cell(30, 10, txt=(str(tax_rate) + " % "), border=1)
    pdf.ln()
    pdf.cell(50, 10, txt="")
    pdf.cell(30, 10, txt="")
    pdf.cell(30, 10, txt="Total", border=1)
   # tax =subtotal *(tax_rate/100)
   # total= subtotal+tax
    pdf.cell(30, 10, txt=str(total), border=1)
    pdf.ln()
    
    conn = psycopg2.connect(database="Invoice", user="postgres", password="admin", host="localhost", port="5432")
    

    cur =  conn.cursor()
   
    cur.execute('INSERT INTO invoicedetail (invoice_name, from_name, from_email, from_address, from_number,to_name,to_email,to_address,to_number,inv_number,inv_date,description,rate,qty,tax_rate,total)  VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(invoice_name, from_name, from_email, from_address, from_number,to_name,to_email,to_address,to_number,inv_number,inv_date,description_json,rate,qty,tax_rate,total))
    conn.commit()
    cur.close()
    conn.close()
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers.set('Content-Disposition', f'attachment', filename=f'{invoice_name}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    

    return response


# conn = psycopg2.connect(database="Invoice", user="postgres", password="admin", host="localhost")
# @app.route('/api/add-invoice', methods=['POST'])
# def add_invoice():
#     data = request.get_json()
#     invoice_name = data['invoice_name']
#     from_name = data['from_name']
#     from_email = data['from_email']
#     from_address = data['from_address']
#     from_number = data['from_number']
#     to_name = data['to_name']
#     to_email = data['to_email']
#     to_address = data['to_address']
#     to_number = data['to_number']
#     inv_number = data['inv_number']
#     inv_date = data['inv_date']
#     description = data['description']
#     rate = data['rate']
#     qty = data['qty']
#     tax_rate = data['tax_rate']
#     total = data['total']
    
#     cur = conn.cursor()
#     cur.execute("INSERT INTO invoicedetail (invoice_name,from_name, from_email, from_address, from_number, to_name, to_email, to_address, to_number, inv_number, inv_date, description, rate, qty, tax_rate, total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s) RETURNING id", (invoice_name,from_name, from_email, from_address, from_number, to_name, to_email, to_address, to_number, inv_number, inv_date, description, rate, qty, tax_rate, total))
#     invoice_id = cur.fetchone()[0]
    
#     items = data['items']
#     for item in items:
#         item_description = item['description']
#         item_rate = item['rate']
#         item_qty = item['qty']
#         item_tax_rate = item['tax_rate']
#         item_total = item['total']
#         cur.execute("INSERT INTO invoicedetail (invoice_id, description, rate, qty, tax_rate, total) VALUES (%s, %s, %s, %s, %s, %s)", (invoice_id, item_description, rate, item_qty, item_tax_rate, item_total))
    
#     conn.commit()

#     cur.close()
    
#     return jsonify({"message": "Invoice added successfully."})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
