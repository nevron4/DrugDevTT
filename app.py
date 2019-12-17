from flask import Flask, jsonify, abort, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
import datetime as dt
import os
from celery import Celery
from celery.result import ResultBase
from celery.schedules import crontab
import random
import string

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Celery
celery = Celery('tasks', broker='redis://localhost:6379/0')
celery.conf.result_backend = 'redis://localhost:6379/0'

# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)


# Address Class/Model
class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('contact.username'), nullable=False)


# Address Schema
class AddressSchema(ma.Schema):
    id = fields.Integer()
    email = fields.Email(many=True)
    person_id = fields.String()


# Contact Class/Model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    addresses = db.relationship('Address', backref='contact', lazy=True)

    def __init__(self, username, first_name, last_name, addresses):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.addresses = [Address(email=addresses)]


# Contact Schema
class ContactSchema(ma.Schema):
    username = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    addresses = fields.Nested(AddressSchema, many=True)


# Email Class/Model
class Email(db.Model):
    email_id = db.Column(db.Integer, primary_key=True)
    from_email = db.Column(db.String(100))
    to_email = db.Column(db.String(100))
    date = db.Column(db.DateTime())
    subject = db.Column(db.String(100))
    text = db.Column(db.String(500))

    def __init__(self, from_email, to_email, date, subject, text):
        self.from_email = from_email
        self.to_email = to_email
        self.date = date
        self.subject = subject
        self.text = text


# Email Schema
class EmailSchema(ma.Schema):
    from_email = fields.Email()
    to_email = fields.Email()
    date = fields.String()
    subject = fields.String()
    text = fields.String()


# Init schema
contact_schema = ContactSchema(strict=True)
contacts_schema = ContactSchema(many=True, strict=True)
address_schema = AddressSchema(many=True, strict=True)
email_schema = EmailSchema(strict=True)
emails_schema = EmailSchema(many=True, strict=True)

NOT_FOUND = 'Not found'
BAD_REQUEST = 'Bad request'

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': NOT_FOUND}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': BAD_REQUEST}), 400)


# Create a Contact
@app.route('/contact', methods=['POST'])
def add_contact():
    username = request.json['username']
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    addresses = request.json['addresses']

    if type(addresses) is not list:
        abort(make_response(jsonify({'error': 'Addresses need to be list.'}), 404))

    if Contact.query.filter(Contact.username == username).count():
        abort(make_response(jsonify({'error': 'Username exist'}), 500))

    for mail in addresses:
        if Contact.query.filter(Contact.username == username).count():
            new_address = Address(email=mail, person_id=username)
            db.session.add(new_address)
            db.session.commit()
        else:
            new_contact = Contact(username, first_name, last_name, mail)
            db.session.add(new_contact)
            db.session.commit()
    contact = Contact.query.filter(Contact.username == username).one()
    return contact_schema.jsonify(contact)


# Get All Contacts
@app.route('/contact', methods=['GET'])
def get_contacts():
    all_contacts = Contact.query.all()
    result = contacts_schema.dump(all_contacts)
    return jsonify(result.data)


# Get Single Contact
@app.route('/contact/<username>', methods=['GET'])
def get_contact(username):
    contact = Contact.query.filter(Contact.username == username).one()
    return contact_schema.jsonify(contact)


# Update a Contact
@app.route('/contact/<username>', methods=['PUT'])
def update_contact(username):
    contact = Contact.query.filter(Contact.username == username).one()
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    contact.username = username
    contact.first_name = first_name
    contact.last_name = last_name
    db.session.commit()
    return contact_schema.jsonify(contact)


# Delete Contact
@app.route('/contact/<username>', methods=['DELETE'])
def delete_contact(username):
    try:
        contact = Contact.query.filter(Contact.username == username).one()
    except:
        abort(make_response(jsonify({'error': 'username does not exist'}), 404))
    emails = Address.query.filter(Address.person_id == username)
    for mail in emails:
        db.session.delete(mail)
    db.session.delete(contact)
    db.session.commit()
    return contact_schema.jsonify(contact)


# Send mail
@app.route('/contact/<username>/email', methods=['POST'])
def send_email(username):
    contact = Address.query.filter(Address.person_id == username).first()
    print(contact.email)
    from_email = contact.email
    to_email = request.json['to_email']
    date = dt.datetime.now()
    subject = request.json['subject']
    text = request.json['text']
    new_email = Email(from_email, to_email, date, subject, text)
    db.session.add(new_email)
    db.session.commit()
    try:
        email_schema.jsonify(new_email)
    except:
        abort(make_response(jsonify({'error': 'Not a valid email address'}), 500))
    return email_schema.jsonify(new_email)


def list_user_emails(username):
    email_list = []
    addresses = Address.query.filter(Address.person_id == username)
    for address in addresses:
        email_list.append(address.email)
    return email_list


# Get user emails
@app.route('/contact/<username>/email', methods=['GET'])
def get_emails(username):
    email_list = list_user_emails(username)
    all_user_emails = Email.query.filter(Email.to_email.in_(email_list))
    result = emails_schema.dump(all_user_emails)
    return jsonify(result.data)


# Get Single email
@app.route('/contact/<username>/email/<email_id>', methods=['GET'])
def get_email(username, email_id):
    email_list = list_user_emails(username)
    email_q = Email.query.get(email_id)
    if email_q.to_email in email_list:
        email = email_q
    else:
        email = ''
    return email_schema.jsonify(email)


# Delete email
@app.route('/contact/<username>/email/<email_id>', methods=['DELETE'])
def delete_email(username, email_id):
    email_list = list_user_emails(username)
    email_q = Email.query.get(email_id)
    if email_q.to_email in email_list:
        email = email_q
        db.session.delete(email)
        db.session.commit()
    return email_schema.jsonify(email)


@celery.task
def delete_contact_task(username):
    contact = Contact.query.filter(Contact.username == username).one()
    emails = Address.query.filter(Address.person_id == username)
    for mail in emails:
        db.session.delete(mail)
    db.session.delete(contact)
    db.session.commit()


@celery.task(name ="creates_contact_task")
def creates_contact_task():
    letters = string.ascii_lowercase
    rand = ''.join(random.choice(letters) for i in range(10))
    new_contact = Contact(rand, rand, rand, (f'{rand}@mail.com'))
    db.session.add(new_contact)
    db.session.commit()
    delete_task = delete_contact_task.apply_async(args=[rand], countdown=60)


celery.add_periodic_task(15.0, creates_contact_task)

# Run Server
if __name__ == '__main__':
    app.run(debug=True)
