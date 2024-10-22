from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()  # Don't pass app here yet

class Account(db.Model):
    account_id = db.Column(db.Integer, primary_key=True)
    account_role = db.Column(db.Enum("Administrator", "Employee"))
    account_fName = db.Column(db.String(100))
    account_lName = db.Column(db.String(100))
    account_img = db.Column(db.LargeBinary, nullable=True)
    account_username = db.Column(db.String(100))
    account_email = db.Column(db.String(100), unique=True)
    account_password = db.Column(db.String(100))
    account_phone = db.Column(db.String(100))
    account_dob = db.Column(db.Date)
    account_gender = db.Column(db.Enum("male", "female"))
    account_created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    account_updated_at = db.Column(db.DateTime, default=datetime.datetime.now)
    account_status = db.Column(db.Enum("active", "inactive"))
    account_last_login = db.Column(db.String(100))

    def __init__(self, account_role, account_fName, account_lName, account_img, account_username, account_email, account_password, account_phone, account_dob, account_gender, account_status, account_last_login):
        self.account_role = account_role
        self.account_fName = account_fName
        self.account_lName = account_lName
        self.account_img = account_img
        self.account_username = account_username
        self.account_email = account_email
        self.account_password = account_password
        self.account_phone = account_phone
        self.account_dob = account_dob
        self.account_gender = account_gender
        self.account_status = account_status
        self.account_last_login = account_last_login


class GuestDetails(db.Model):
    guest_id = db.Column(db.Integer, primary_key=True)
    guest_fName = db.Column(db.String(100))
    guest_lName = db.Column(db.String(100))
    guest_pop = db.Column(db.LargeBinary, nullable=False)
    guest_email = db.Column(db.String(100), unique=True)
    guest_phone = db.Column(db.String(100))
    guest_gender = db.Column(db.Enum("male", "female"), nullable=False)
    guest_messenger_account = db.Column(db.String(100), nullable=False)
    guest_poi = db.Column(db.LargeBinary, nullable=True)
    guest_designation = db.Column(db.String(100), nullable=False)
    guest_address = db.Column(db.String(100), nullable=False)
    guest_client = db.Column(db.String(100), nullable=False)

    def __init__(self, guest_fName, guest_lName, guest_pop, guest_email, guest_phone, guest_gender, guest_messenger_account, guest_poi, guest_designation, guest_address, guest_client):
        self.guest_fName = guest_fName
        self.guest_lName = guest_lName
        self.guest_pop = guest_pop
        self.guest_email = guest_email
        self.guest_phone = guest_phone
        self.guest_gender = guest_gender
        self.guest_messenger_account = guest_messenger_account
        self.guest_poi = guest_poi
        self.guest_designation = guest_designation
        self.guest_address = guest_address
        self.guest_client = guest_client



class Room(db.Model):
    room_id = db.Column(db.Integer, primary_key=True)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.room_type_id'))  # Fixed ForeignKey reference
    room_name = db.Column(db.String(100), nullable=False)
    room_status = db.Column(db.Enum("reserved", "cancelled", "pending"), nullable=False)  # Added nullable=False for consistency

    def __init__(self, room_type_id, room_name, room_status):
        self.room_type_id = room_type_id
        self.room_name = room_name
        self.room_status = room_status


class RoomType(db.Model):
    room_type_id = db.Column(db.Integer, primary_key=True)
    room_type_name = db.Column(db.String(100))
    room_type_description = db.Column(db.String(1000), nullable=True)
    room_type_price = db.Column(db.Float, nullable=False)
    room_type_capacity = db.Column(db.Integer, nullable=False)

    def __init__(self, room_type_name, room_type_description, room_type_price, room_type_capacity):
        self.room_type_name = room_type_name
        self.room_type_description = room_type_description
        self.room_type_price = room_type_price
        self.room_type_capacity = room_type_capacity
