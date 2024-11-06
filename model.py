from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()  # Don't pass app here yet

class Account(db.Model):
    account_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_role = db.Column(db.Enum("Administrator", "Employee"))
    account_fName = db.Column(db.String(100))
    account_lName = db.Column(db.String(100))
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

    def __init__(self, account_role, account_fName, account_lName, account_username, account_email, account_password, account_phone, account_dob, account_gender, account_status, account_last_login):
        self.account_role = account_role
        self.account_fName = account_fName
        self.account_lName = account_lName
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
    guest_type = db.Column(db.Enum("internal", "external"), nullable=False)
    guest_fName = db.Column(db.String(100))
    guest_lName = db.Column(db.String(100))
    guest_pop = db.Column(db.LargeBinary, nullable=True)
    guest_email = db.Column(db.String(100), unique=True)
    guest_phone = db.Column(db.String(100))
    guest_gender = db.Column(db.Enum("male", "female"), nullable=False)
    guest_messenger_account = db.Column(db.String(100), nullable=False)
    guest_poi = db.Column(db.LargeBinary, nullable=True)
    guest_designation = db.Column(db.String(100), nullable=False)
    guest_address = db.Column(db.String(100), nullable=False)
    guest_client = db.Column(db.String(100), nullable=False)

    def __init__(self, guest_type, guest_fName, guest_lName, guest_pop, guest_email, guest_phone, guest_gender, guest_messenger_account, guest_poi, guest_designation, guest_address, guest_client):
        self.guest_type = guest_type
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
    room_id = db.Column(db.String(50), primary_key=True)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.room_type_id'))  # Fixed ForeignKey reference
    room_type = db.relationship('RoomType', backref='rooms')  # Added backref for convenience
    room_name = db.Column(db.String(100), nullable=False)
    room_status = db.Column(db.Enum("ready", "onMaintenance", "onCleaning"), nullable=False)  # Added nullable=False for consistency

    def __init__(self,room_id, room_type_id, room_name, room_status):
        self.room_id = room_id
        self.room_type_id = room_type_id
        self.room_name = room_name
        self.room_status = room_status
    
# In your Room model
    def to_dict(self, is_available=False):
        return {
            "room_id": self.room_id,
            "room_type_id": self.room_type_id,
            "room_status": is_available,  # Include room_status field here
            # Add other fields as needed
        }


class RoomType(db.Model):
    room_type_id = db.Column(db.Integer, primary_key=True)
    room_type_name = db.Column(db.String(100))
    room_type_description = db.Column(db.String(1000), nullable=True)
    room_type_price = db.Column(db.Float, nullable=False)
    room_type_capacity = db.Column(db.Integer, nullable=False)
    room_type_img = db.Column(db.LargeBinary(length=2**32 - 1), nullable=True)  # Use LONGBLOB for very large images


    def __init__(self, room_type_name, room_type_description, room_type_price, room_type_capacity, room_type_img):
        self.room_type_name = room_type_name
        self.room_type_description = room_type_description
        self.room_type_price = room_type_price
        self.room_type_capacity = room_type_capacity
        self.room_type_img = room_type_img

class Venue(db.Model):
    venue_id = db.Column(db.String(50), primary_key = True)
    venue_name = db.Column(db.String(100))
    venue_description = db.Column(db.String(1000), nullable=False)
    venue_status = db.Column(db.Enum("reserve", "available", "pending"), nullable=False)
    venue_pricing = db.Column(db.Float, nullable=False)
    venue_capacity = db.Column(db.Integer, nullable=False)
    venue_img = db.Column(db.LargeBinary(length=2**32 - 1), nullable=True)  # Added nullable=False for consistency

    def __init__(self, venue_id, venue_name, venue_description, venue_status, venue_pricing, venue_capacity, venue_img):
        self.venue_id = venue_id
        self.venue_name = venue_name
        self.venue_description = venue_description
        self.venue_status = venue_status
        self.venue_pricing = venue_pricing
        self.venue_capacity = venue_capacity
        self.venue_img = venue_img

class VenueReservation(db.Model):
    venue_reservation_id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.String(50), db.ForeignKey('venue.venue_id'))
    venue = db.relationship('Venue', backref='venue_reservations')
    guest_id = db.Column(db.Integer, db.ForeignKey('guest_details.guest_id'))
    guest = db.relationship('GuestDetails', backref='venue_reservations')
    account_id = db.Column(db.Integer, db.ForeignKey('account.account_id'))
    account = db.relationship('Account', backref='venue_reservations')
    venue_reservation_booking_date_start = db.Column(db.Date, nullable=False)
    venue_reservation_booking_date_end = db.Column(db.Date, nullable=False)
    venue_reservation_check_in_time = db.Column(db.Time, nullable=False)
    venue_reservation_check_out_time = db.Column(db.Time, nullable=False)
    venue_reservation_status = db.Column(db.Enum("waiting", "ready", "onUse" , "cancelled" , "doneReservation"), nullable=False)

    def __init__(self, venue_reservation_id,venue_id, guest_id, account_id, venue_reservation_booking_date_start, venue_reservation_booking_date_end,venue_reservation_check_in_time, venue_reservation_check_out_time, venue_reservation_status):
        self.venue_reservation_id = venue_reservation_id
        self.venue_id = venue_id
        self.guest_id = guest_id
        self.account_id = account_id
        self.venue_reservation_booking_date_start = venue_reservation_booking_date_start
        self.venue_reservation_booking_date_end = venue_reservation_booking_date_end
        self.venue_reservation_check_in_time = venue_reservation_check_in_time
        self.venue_reservation_check_out_time = venue_reservation_check_out_time
        self .venue_reservation_status = venue_reservation_status

class RoomReservation(db.Model):
    room_reservation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.String(50), db.ForeignKey('room.room_id'))
    room = db.relationship('Room', backref='room_reservations')
    guest_id = db.Column(db.Integer, db.ForeignKey('guest_details.guest_id'))
    guest = db.relationship('GuestDetails', backref='room_reservations')
    account_id = db.Column(db.Integer, db.ForeignKey('account.account_id'))
    account = db.relationship('Account', backref='room_reservations')
    room_reservation_booking_date_start = db.Column(db.Date, nullable=False)
    room_reservation_booking_date_end = db.Column(db.Date, nullable=False)
    room_reservation_check_in_time = db.Column(db.Time, nullable=False)
    room_reservation_check_out_time = db.Column(db.Time, nullable=False)
    room_reservation_status = db.Column(db.Enum("waiting", "ready", "onUse" , "cancelled" , "done" , "onCleaning"), nullable=False)

    def __init__(self, room_id, guest_id, account_id, room_reservation_booking_date_start, room_reservation_booking_date_end, room_reservation_check_in_time, room_reservation_check_out_time, room_reservation_status):
        self.room_id = room_id
        self.guest_id = guest_id
        self.account_id = account_id
        self.room_reservation_booking_date_start = room_reservation_booking_date_start
        self.room_reservation_booking_date_end = room_reservation_booking_date_end
        self.room_reservation_check_in_time = room_reservation_check_in_time
        self.room_reservation_check_out_time = room_reservation_check_out_time
        self.room_reservation_status = room_reservation_status
        
