# ================================================ #
#                                                  #
#    Welcome to the Lantaka Project Backend!       #
#                                                  # 
#   Powered by Flask and Python, with MySQL        #
#   handling data storage for seamless room        #
#   reservations and event management.             #
#                                                  #
#   Enjoy exploring the backend, and feel free     #
#   to reach out with any questions or feedback!   #
#                                                  #
# ================================================ #

# ================================================ #
import base64
import bcrypt
import subprocess
import time
import json
import os
from flask import Flask, request, jsonify, Response, session
from marshmallow import Schema, fields, validate, ValidationError
from flask_marshmallow import Marshmallow  # Correct import
from werkzeug.utils import secure_filename  # For secure image uploads
from flask_cors import CORS
from model import db, Account, Room, RoomType, Venue, VenueReservation, RoomReservation, GuestDetails, Receipt, Notification
from datetime import datetime, time, date
from defaultValues import rooms, roomTypes, venues
from collections import defaultdict
from definedFunctions.apiAccountModel import get_accounts
from definedFunctions.apiGuestModel import get_guests
from definedFunctions.apiDiscounts import get_discounts, insert_discounts
from definedFunctions.apiAdditionalFees import get_AdditionalFees, insert_AdditionalFees
from definedFunctions.apiSubmitReservation import submit_reservation
from definedFunctions.apiReservations import get_Reservations
from definedFunctions.apiPrice import get_Price
from definedFunctions.apiDeleteGroupedReservation import delete_reservations
from definedFunctions.apiNotification import get_Notification, create_Notification, delete_Notification, update_Notification
# ================================================ #

app = Flask(__name__)
CORS(app)

# Configuration for MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/lantaka_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow
db.init_app(app)  # Initialize with app
ma = Marshmallow(app)  # Correct initialization

# Marshmallow schema for validation
class AccountSchema(Schema):
    account_role = fields.Str(required=True, validate=validate.OneOf(["Administrator", "Employee"]))
    fName = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    lName = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    phone = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    dob = fields.Date(required=True)
    gender = fields.Str(validate=validate.OneOf(["male", "female"]))

# Initialize schema objects
account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)


xampp_path = r"C:\xampp\xampp-control.exe"
xampp_control_path = r"C:\xampp\xampp_start.exe"  # Update this path if your XAMPP is installed in a different location

# Function to start XAMPP
def start_xampp():
    try:
        print("Starting XAMPP...")
        try:
            subprocess.run(xampp_control_path, shell=True)
            print("XAMPP and MySQL server started.")
        except FileNotFoundError:
            print("The path to xampp_start.exe is incorrect.")
        print("MySQL server started.")
    except Exception as e:
        print("Error starting XAMPP or MySQL:", e)

# Route for account registration
@app.route('/register', methods=['POST'])
def register():
    try:
        # Validate the request form data
        data = account_schema.load(request.form)

        # Extract values after validation
        role = data['account_role']
        firstName = data['fName']
        lastName = data['lName']
        username = "LRS" + lastName.lower()
        email = data['email']
        password = data['password']
        phone = data['phone']
        dob = data['dob']
        gender = data['gender']

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


        # Check if the account already exists
        existing_accounts = Account.query.filter_by(account_email=email).first()
        if existing_accounts:
            return jsonify({"message": "Email already exists"}), 400

        # Create a new account
        new_account = Account(
            account_role=role,
            account_fName=firstName,
            account_lName=lastName,
            account_username=username,
            account_email=email,
            account_password=hashed_password.decode('utf-8'),
            account_phone=phone,
            account_dob=dob,
            account_gender=gender,
            account_status="active",
            account_last_login=""
        )

        # Add and commit to the database
        db.session.add(new_account)
        db.session.commit()

        return jsonify({"message": "success"}), 201

    except ValidationError as err:
        # Return validation errors from Marshmallow
        return jsonify({"errors": err.messages}), 400





@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    # Find the user by username
    user = Account.query.filter_by(account_username=username).first()

    if user and bcrypt.checkpw(password.encode('utf-8'), user.account_password.encode('utf-8')):
        # Update last login time
        user.account_last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        # Return relevant user data
        return jsonify({
            "message": "Login successful",
            "account_id": user.account_id,
            "role": user.account_role,
            "first_name": user.account_fName,
            "last_name": user.account_lName,
            "email": user.account_email,
            "phone": user.account_phone,
            "dob": user.account_dob.strftime('%Y-%m-%d'),  # Format date
            "gender": user.account_gender,
            "status": user.account_status,
            "last_login": user.account_last_login
        }), 200 
    else:
        return jsonify({"message": "Invalid credentials"}), 401




@app.route("/api/reservations", methods=["GET"])
def get_reservations():
    roomReservations = RoomReservation.query.all()
    venueReservations = VenueReservation.query.all()

    if not roomReservations and not venueReservations:
        return jsonify({"error": "No reservations found"}), 404

    reservationsHolder = []

    # Define date and time format
    date_time_format = "%Y-%m-%d %H:%M:%S"

    # Dictionaries to count rooms and venues per guest
    room_counts = defaultdict(int)
    venue_counts = defaultdict(int)

    # Calculate number of rooms and venues for each guest
    for reservation in roomReservations:
        room_counts[reservation.guest_id] += 1

    for reservation in venueReservations:
        venue_counts[reservation.guest_id] += 1

    # Process room reservations
    for reservation in roomReservations:
        check_in_datetime = datetime.combine(reservation.room_reservation_booking_date_start, reservation.room_reservation_check_in_time)
        check_out_datetime = datetime.combine(reservation.room_reservation_booking_date_end, reservation.room_reservation_check_out_time)
        guest = GuestDetails.query.filter_by(guest_id=reservation.guest_id).first()
        account = Account.query.filter_by(account_id=reservation.account_id).first()
        receipt = Receipt.query.filter_by(receipt_id=reservation.receipt_id).first()

        reservation_data = {
            "reservation_id": reservation.room_reservation_id,
            "guest_type": guest.guest_type,
            "reservation": reservation.room_id,
            "guest_name": guest.guest_fName + " " + guest.guest_lName,
            "guest_email": guest.guest_email,
            "account_name": account.account_fName + " " + account.account_lName,
            "receipt_date": receipt.receipt_date,
            "receipt_initial_total": receipt.receipt_initial_total,
            "receipt_total_amount": receipt.receipt_total_amount,
            "receipt_discount": receipt.receipt_discounts,
            "check_in_date": check_in_datetime.strftime(date_time_format),
            "check_out_date": check_out_datetime.strftime(date_time_format),
            "status": reservation.room_reservation_status,
            "additional_notes": reservation.room_reservation_additional_notes,
            "number_of_rooms": room_counts[reservation.guest_id],
            "number_of_venues": venue_counts[reservation.guest_id]
        }
        reservationsHolder.append(reservation_data)

    # Process venue reservations
    for reservation in venueReservations:
        check_in_datetime = datetime.combine(reservation.venue_reservation_booking_date_start, reservation.venue_reservation_check_in_time)
        check_out_datetime = datetime.combine(reservation.venue_reservation_booking_date_end, reservation.venue_reservation_check_out_time)
        guest = GuestDetails.query.filter_by(guest_id=reservation.guest_id).first()
        account = Account.query.filter_by(account_id=reservation.account_id).first()
        receipt = Receipt.query.filter_by(receipt_id=reservation.receipt_id).first()

        reservation_data = {
            "reservation_id": reservation.venue_reservation_id,
            "guest_type": guest.guest_type,
            "reservation": reservation.venue_id,
            "guest_name": guest.guest_fName + " " + guest.guest_lName,
            "guest_email": guest.guest_email,
            "account_name": account.account_fName + " " + account.account_lName,
            "receipt_date": receipt.receipt_date,
            "receipt_initial_total": receipt.receipt_initial_total,
            "receipt_total_amount": receipt.receipt_total_amount,
            "receipt_discount": receipt.receipt_discounts,
            "check_in_date": check_in_datetime.strftime(date_time_format),
            "check_out_date": check_out_datetime.strftime(date_time_format),
            "status": reservation.venue_reservation_status,
            "additional_notes": reservation.venue_reservation_additional_notes,
            "number_of_rooms": room_counts[reservation.guest_id],
            "number_of_venues": venue_counts[reservation.guest_id]
        }
        reservationsHolder.append(reservation_data)

    return jsonify(reservationsHolder), 200



@app.route('/api/venueData', methods=['GET'])
def get_venue_data():
    venues = Venue.query.all()
    if venues:
        venuesHolder = []
        for venue in venues:
            if venue.venue_img:
                venue_image_blob = base64.b64encode(venue.venue_img).decode('utf-8')
                venue_image_url = f"data:image/webp;base64,{venue_image_blob}"  # Assuming it's a JPEG, adjust if needed
            else:
                venue_image_url = None  # Or a default image

            venue_data = {
                "id": venue.venue_id,
                "name": venue.venue_name,
                "description": venue.venue_description,
                "status": venue.venue_status,
                "price": venue.venue_pricing,
                "capacity": venue.venue_capacity,
                "image": venue_image_url,
            }
            venuesHolder.append(venue_data)

        return jsonify(venuesHolder), 200
    else:
        return jsonify({"error": "No venue data found"}), 404


@app.route('/api/roomData', methods=['GET'])
def get_room_data():
    rooms = Room.query.all()
    if rooms:
        roomsHolder = []
        for room in rooms:
            if room.room_type and room.room_type.room_type_img:
                room_image_blob = base64.b64encode(room.room_type.room_type_img).decode('utf-8')
                room_image_url = f"data:image/webp;base64,{room_image_blob}"  # Assuming it's a JPEG, adjust if needed
            else:
                room_image_url = None  # Or a default image

            room_data = {
                "id": room.room_id,
                "name": room.room_name,
                "type": room.room_type.room_type_name,
                "description": room.room_type.room_type_description,
                "status": room.room_status,
                "image": room_image_url,
            }
            roomsHolder.append(room_data)
        return jsonify(roomsHolder), 200
    else:
        return jsonify({"error": "No room data found"}), 404
    
@app.route('/api/details/rooms/<string:item_id>', methods=['GET'])
def get_room_details(item_id):
    currentDate = request.args.get('date')
    room = Room.query.get(item_id)
    if room:
        return get_room_details_response(room, currentDate)
    return jsonify({'error': 'Room not found'}), 404

@app.route('/api/details/venues/<string:item_id>', methods=['GET'])
def get_venue_details(item_id):
    currentDate = request.args.get('date')
    venue = Venue.query.get(item_id)
    if venue:
        return get_venue_details_response(venue, currentDate)
    return jsonify({'error': 'Venue not found'}), 404


def get_room_details_response(room , currentDate):
    current_booking = RoomReservation.query.filter_by(room_id=room.room_id).filter(
        (RoomReservation.room_reservation_booking_date_start <= currentDate) & 
        (RoomReservation.room_reservation_booking_date_end >= currentDate)).first()
    if current_booking:
        print(current_booking)
        return jsonify({
            'date': currentDate,
            'name': room.room_name,
            'type': 'room',
            'employee': f"{current_booking.account.account_fName} {current_booking.account.account_lName}",
            'guest_name': f"{current_booking.guest.guest_fName} {current_booking.guest.guest_lName}" if current_booking else None,
            'check_in': current_booking.room_reservation_booking_date_start.isoformat() if current_booking else None,
            'check_out': current_booking.room_reservation_booking_date_end.isoformat() if current_booking else None,
            'image_url': f"http://localhost:5000/api/image/{room.room_id}?type=room"
        })
    else:
         return jsonify({
            'date': currentDate,
            'name': room.room_name,
            'type': 'room',
            'guest_name': "No Reservation",
            'check_in': "No Reservation",
            'check_out': "No Reservation",
            'image_url': f"http://localhost:5000/api/image/{room.room_id}?type=room"
        })

def get_venue_details_response(venue, currentDate):
    current_booking = VenueReservation.query.filter_by(venue_id=venue.venue_id).filter(
        (VenueReservation.venue_reservation_booking_date_start <= currentDate) & 
        (VenueReservation.venue_reservation_booking_date_end >= currentDate)).first()
    if current_booking:
        return jsonify({
            'name': venue.venue_name,
            'type': 'venue',
            'employee': f"{current_booking.account.account_fName} {current_booking.account.account_lName}",
            'guest_name': f"{current_booking.guest.guest_fName} {current_booking.guest.guest_lName}" if current_booking else None,
            'check_in': current_booking.venue_reservation_booking_date_start.isoformat() if current_booking else None,
            'check_out': current_booking.venue_reservation_booking_date_end.isoformat() if current_booking else None,
            'image_url': f"http://localhost:5000/api/image/{venue.venue_id}?type=venue"
        })
    else:
         return jsonify({
            'date': currentDate,
            'name': venue.venue_name,
            'type': 'venue',
            'guest_name': "No Reservation",
            'check_in': "No Reservation",
            'check_out': "No Reservation",
            'image_url': f"http://localhost:5000/api/image/{venue.venue_id}?type=venue"
        })


@app.route('/api/image/<string:item_id>', methods=['GET'])
def serve_image(item_id):
    item_type = request.args.get('type')
    if item_type == 'room':
        room = Room.query.get(item_id)
        if room and room.room_type and room.room_type.room_type_img:
            return Response(room.room_type.room_type_img, mimetype='image/webp')
    elif item_type == 'venue':
        venue = Venue.query.get(item_id)
        if venue and venue.venue_img:
            return Response(venue.venue_img, mimetype='image/webp')
    return jsonify({'error': 'Image not found'}), 404


@app.route('/api/reservationCalendar', methods=['GET'])
def get_reservation_calendar():
    reservationsVenue = VenueReservation.query.all()
    reservationsRoom = RoomReservation.query.all()
    if reservationsVenue or reservationsRoom:
        reservations = []

        for venue in reservationsVenue:
            reservations.append({
                'reservationid': venue.venue_reservation_id,
                'id': venue.venue_id,
                'type':'venue',
                'dateStart': venue.venue_reservation_booking_date_start.isoformat(),
                'dateEnd': venue.venue_reservation_booking_date_end.isoformat(),
                'status': venue.venue_reservation_status,
                'guests': f"{venue.guest.guest_fName} {venue.guest.guest_lName}",
                'employee': f"{venue.account.account_fName} {venue.account.account_lName}",
                'checkIn': venue.venue_reservation_check_in_time.isoformat(),
                'checkOut': venue.venue_reservation_check_out_time.isoformat(),
            })

        for room in reservationsRoom:
            reservations.append({
                'reservationid': room.room_reservation_id,
                'id': room.room_id,
                'type':'room',
                'dateStart': room.room_reservation_booking_date_start.isoformat(),
                'dateEnd': room.room_reservation_booking_date_end.isoformat(),
                'status': room.room_reservation_status,
                'guests': f"{room.guest.guest_fName} {room.guest.guest_lName}",
                'employee': f"{room.account.account_fName} {room.account.account_lName}",
                'checkIn': room.room_reservation_check_in_time.isoformat(),
                'checkOut': room.room_reservation_check_out_time.isoformat(),
            })

        return jsonify(reservations), 200
    else:
        return jsonify({"error": "No reservations found"}), 404


@app.route('/api/everythingAvailable', methods=['GET'])
def api_everythingAvailable():
    rooms = Room.query.all()
    venues = Venue.query.all()
    
    # Group rooms by room type
    double_rooms = [room.to_dict(is_available=False) for room in rooms if room.room_type_id == 1]
    triple_rooms = [room.to_dict(is_available=False) for room in rooms if room.room_type_id == 2]
    matrimonial_rooms = [room.to_dict(is_available=False) for room in rooms if room.room_type_id == 3]
    venues_holder = [venue.to_dict(is_available=False) for venue in venues ]

    return jsonify({
        "double_rooms": double_rooms,
        "triple_rooms": triple_rooms,
        "matrimonial_rooms": matrimonial_rooms,
        "venues_holder": venues_holder
    })

@app.route('/api/availableRooms/<string:dateStart>/<string:dateEnd>', methods=['GET'])
def api_availableRooms(dateStart, dateEnd):
    # Convert string dates to date objects
    date_start = datetime.strptime(dateStart, '%Y-%m-%d').date()
    date_end = datetime.strptime(dateEnd, '%Y-%m-%d').date()

    # Get all rooms
    rooms = Room.query.all()
    
    available_rooms = []

    for room in rooms:
        # Query to find reservations that overlap with the requested date range
        overlapping_reservations = RoomReservation.query.filter(
            RoomReservation.room_id == room.room_id,
            RoomReservation.room_reservation_status == "waiting",
            RoomReservation.room_reservation_booking_date_start <= date_end,  # Starts on or before the requested end date
            RoomReservation.room_reservation_booking_date_end >= date_start   # Ends on or after the requested start date
        ).all()
        
        # Set room_status based on whether there are overlapping reservations
        room_status = len(overlapping_reservations) == 0  # True if no overlapping reservations
        room_dict = room.to_dict(is_available=room_status)  # Pass room_status to to_dict
        available_rooms.append(room_dict)

    double_rooms = [room for room in available_rooms if room['room_type_id'] == 1]
    triple_rooms = [room for room in available_rooms if room['room_type_id'] == 2]
    matrimonial_rooms = [room for room in available_rooms if room['room_type_id'] == 3]

    return jsonify({
        "double_rooms": double_rooms,
        "triple_rooms": triple_rooms,
        "matrimonial_rooms": matrimonial_rooms
    })


@app.route('/api/availableVenues/<string:dateStart>/<string:dateEnd>', methods=['GET'])
def api_availableVenues(dateStart, dateEnd):
    # Convert string dates to date objects
    date_start = datetime.strptime(dateStart, '%Y-%m-%d').date()
    date_end = datetime.strptime(dateEnd, '%Y-%m-%d').date()

    venues = Venue.query.all()
    
    available_venues = []

    print(f"Start Date: {date_start}, End Date: {date_end}")
    print(f"Total Venues: {len(venues)}")

    for venue in venues:
        # If there are no reservations in the VenueReservation table, assume it's available
        overlapping_reservations = VenueReservation.query.filter(
            VenueReservation.venue_id == venue.venue_id,
            VenueReservation.venue_reservation_status == "waiting",
            VenueReservation.venue_reservation_booking_date_start <= date_end,
            VenueReservation.venue_reservation_booking_date_end >= date_start
        ).all()

        print(f"Venue {venue.venue_id}: Overlapping Reservations: {len(overlapping_reservations)}")
        
        room_status = len(overlapping_reservations) == 0  # Available if no overlapping reservations
        venue_dict = venue.to_dict(is_available=room_status)
        available_venues.append(venue_dict)

    print(f"Available Venues: {len(available_venues)}")

    return jsonify({
        "venues_holder": available_venues,
    })



@app.route('/api/available/<string:dateStart>/<string:dateEnd>/<string:type>', methods=['GET'])
def get_availability(dateStart, dateEnd, type):
    # Convert string dates to date objects
    date_start = datetime.strptime(dateStart, '%Y-%m-%d').date()
    date_end = datetime.strptime(dateEnd, '%Y-%m-%d').date()

    # Initialize dictionaries to hold available room IDs and venue availability
    available_rooms_by_type = {}
    available_venues = {}

    # Get all room types
    room_types = RoomType.query.with_entities(RoomType.room_type_id).all()
    venue_types = Venue.query.with_entities(Venue.venue_id, Venue.venue_name).all()  # Fetch venue_id and venue_name

    # Check available rooms by room type
    for room_type in room_types:
        total_rooms = Room.query.filter_by(room_type_id=room_type.room_type_id).all()

        reserved_room_ids = RoomReservation.query.filter(
            RoomReservation.room_reservation_booking_date_start < date_end,
            RoomReservation.room_reservation_booking_date_end > date_start,
            RoomReservation.room.has(room_type_id=room_type.room_type_id)
        ).with_entities(RoomReservation.room_id).all()

        reserved_ids = {room[0] for room in reserved_room_ids}
        available_rooms = [room.room_id for room in total_rooms if room.room_id not in reserved_ids]

        available_rooms_by_type[room_type.room_type_id] = available_rooms 

    # Check venue availability
    for venue_id, venue_name in venue_types:
        total_venues = Venue.query.filter_by(venue_id=venue_id).all()

        reserved_venue_ids = VenueReservation.query.filter(
            VenueReservation.venue_reservation_booking_date_start < date_end,
            VenueReservation.venue_reservation_booking_date_end > date_start,
            VenueReservation.venue.has(venue_id=venue_id)
        ).with_entities(VenueReservation.venue_id).all()

        reserved_venue_ids_set = {venue[0] for venue in reserved_venue_ids}
        is_available = venue_id not in reserved_venue_ids_set

        if is_available:
            available_venues[venue_id] = {
                "venue_name": venue_name,
                "available": True,
                "dates": [(date_start, date_end)]  # This indicates that it's available during this period
            }
        else:
            available_venues[venue_id] = {
                "venue_name": venue_name,
                "available": False,
                "dates": []  # No available dates if reserved
            }

    # Return results based on the requested type
    if type == 'both':
        return jsonify(availability={
            'rooms': available_rooms_by_type,
            'venues': available_venues
        }), 200
    elif type == 'room':
        return jsonify(availability=available_rooms_by_type), 200
    elif type == 'venue':
        return jsonify(availability=available_venues), 200

    return jsonify(error='Invalid type specified'), 400






    
@app.route('/api/reservationCalendar/<int:event_id>', methods=['PUT'])
def update_reservation_status(event_id):
    # Retrieve query parameters
    reservation_id = request.args.get('id')
    new_status = request.args.get('status')
    event_type = request.args.get('type')

    # Print values for debugging
    print(f"Reservation ID: {reservation_id}, Status: {new_status}, Event Type: {event_type}")

    # Check required fields
    if not reservation_id or not new_status or not event_type:
        return jsonify({'error': 'Missing required fields: id, status, or type'}), 400

    # Normalize case for event_type
    event_type = event_type.lower()

    try:
        # Update based on type
        if event_type == 'venue':
            reservation = VenueReservation.query.filter_by(venue_reservation_id=event_id).first()
            if reservation:
                reservation.venue_reservation_status = new_status
                db.session.commit()
                return jsonify({'message': 'Venue reservation status updated successfully'}), 200
            else:
                return jsonify({'error': 'Venue reservation not found'}), 404

        elif event_type == 'room':
            reservation = RoomReservation.query.filter_by(room_reservation_id=event_id).first()
            if reservation:
                reservation.room_reservation_status = new_status
                db.session.commit()
                return jsonify({'message': 'Room reservation status updated successfully'}), 200
            else:
                return jsonify({'error': 'Room reservation not found'}), 404

        else:
            return jsonify({'error': 'Invalid reservation type'}), 400

    except Exception as e:
        db.session.rollback()
        print(f"Error updating reservation: {e}")
        return jsonify({'error': 'An error occurred while updating the reservation'}), 500



@app.route('/api/reservationStatus/<string:date>', methods=['GET'])
def get_reservation_status(date):
    try:
        # Convert string date to datetime object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # Query venue reservations
        venue_reservations = VenueReservation.query.filter(
            VenueReservation.venue_reservation_booking_date_start <= date_obj,
            VenueReservation.venue_reservation_booking_date_end >= date_obj
        ).all()

        # Query room reservations
        room_reservations = RoomReservation.query.filter(
            RoomReservation.room_reservation_booking_date_start <= date_obj,
            RoomReservation.room_reservation_booking_date_end >= date_obj
        ).all()

        # Combine and format results
        reservation_data = []
        for reserve in venue_reservations:
            reservation_data.append({
                'id': reserve.venue_id,
                'status': reserve.venue_reservation_status,
                'type': 'venue'
            })
        for reserve in room_reservations:
            reservation_data.append({
                'id': reserve.room_id,
                'status': reserve.room_reservation_status,
                'type': 'room'
            })

        # If no reservations are found, set all statuses to normal
        if not reservation_data:
            # Create a list of all venues and rooms from your defined lists
            all_venues_and_rooms = [
                {'id': venue.venue_id, 'type': 'venue'} for venue in venues
            ] + [
                {'id': room.room_id, 'type': 'room'} for room in rooms
            ]

            for item in all_venues_and_rooms:
                reservation_data.append({
                    'id': item['id'],
                    'status': 'normal',
                    'type': item['type']
                })
            return jsonify(reservation_data), 200

        return jsonify(reservation_data), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

# @app.route('/api/reservationCalendar/<int:event_id>', methods=['PUT'])
# def update_reservation_status(event_id):
#     # Retrieve query parameters
#     reservation_id = request.args.get('id')
#     new_status = request.args.get('status')
#     event_type = request.args.get('type')

#     # Print values for debugging
#     print(f"Reservation ID: {reservation_id}, Status: {new_status}, Event Type: {event_type}")

#     # Check required fields
#     if not reservation_id or not new_status or not event_type:
#         return jsonify({'error': 'Missing required fields: id, status, or type'}), 400

#     # Normalize case for event_type
#     event_type = event_type.lower()

#     try:
#         # Update based on type
#         if event_type == 'venue':
#             reservation = VenueReservation.query.filter_by(venue_reservation_id=event_id).first()
#             if reservation:
#                 reservation.venue_reservation_status = new_status
#                 db.session.commit()
#                 return jsonify({'message': 'Venue reservation status updated successfully'}), 200
#             else:
#                 return jsonify({'error': 'Venue reservation not found'}), 404

#         elif event_type == 'room':
#             reservation = RoomReservation.query.filter_by(room_reservation_id=event_id).first()
#             if reservation:
#                 reservation.room_reservation_status = new_status
#                 db.session.commit()
#                 return jsonify({'message': 'Room reservation status updated successfully'}), 200
#             else:
#                 return jsonify({'error': 'Room reservation not found'}), 404

#         else:
#             return jsonify({'error': 'Invalid reservation type'}), 400

#     except Exception as e:
#         db.session.rollback()
#         print(f"Error updating reservation: {e}")
#         return jsonify({'error': 'An error occurred while updating the reservation'}), 500


# METHOD GET
app.add_url_rule('/api/accounts', 'get_accounts', get_accounts, methods=['GET'])
app.add_url_rule('/api/guests', 'get_guests', get_guests, methods=['GET'])
app.add_url_rule('/api/getDiscounts', 'get_discounts', get_discounts, methods=['GET'])
app.add_url_rule('/api/getAddFees', 'get_AdditionalFees', get_AdditionalFees, methods=['GET'])
app.add_url_rule('/api/getReservations', 'get_Reservations', get_Reservations, methods=['GET'])
app.add_url_rule('/api/getPrice/<string:guestType>', 'get_Price', get_Price, methods=['GET'])
app.add_url_rule('/api/notifications/unread', 'get_Notification', get_Notification, methods=['GET'])
                 
# METHOD POST
app.add_url_rule('/api/insertDiscount', 'insert_discount', insert_discounts, methods=['POST'])
app.add_url_rule('/api/insertAdditionalFee', 'insert_AdditionalFees', insert_AdditionalFees, methods=['POST'])
app.add_url_rule('/api/submitReservation', 'submit_reservation', submit_reservation, methods=['POST'])
app.add_url_rule('/api/notifications', 'create_Notification', create_Notification, methods=['POST'])

#METHOD PATCH
app.add_url_rule('/api/notifications/<int:notification_id>/update','update_Notification', update_Notification, methods=['PATCH'] )
app.add_url_rule('/api/notifications/<int:notification_id>/delete','delete_notification', delete_Notification, methods=['PATCH'] )
# METHOD DELETE
app.add_url_rule('/api/delete_reservations', 'delete_reservations', delete_reservations, methods=['DELETE'])
# Ensure the application context is active before creating tables
if __name__ == '__main__':
    # start_xampp()
    with app.app_context():
        db.create_all()  # Creates the tables in the database
        # Check if room types already exist
        existing_room_types = db.session.query(RoomType).all()
        if not existing_room_types:
            db.session.add_all(roomTypes)
            db.session.commit()
            print("Room types inserted successfully!")
        else:
            print("Room types already exist, skipping insertion.")

        # Check if rooms already exist
        existing_rooms = db.session.query(Room).all()
        if not existing_rooms:
            db.session.add_all(rooms)
            db.session.commit()
            print("Rooms inserted successfully!")
        else:
            print("Rooms already exist, skipping insertion.")

        # Check if venues already exist
        existing_venue = db.session.query(Venue).all()
        if not existing_venue:
            db.session.add_all(venues)
            db.session.commit()
            print("Venues inserted successfully!")
        else:
            print("Venues already exist, skipping insertion.")

        existing_dummy = db.session.query(VenueReservation).all()
        if not existing_dummy:
            # db.session.add_all(new_room_reservations)
            db.session.commit()
            print("dummies inserted successfully!")
        else:
            print("Venues already exist, skipping insertion.")


    app.run(host='0.0.0.0', debug=True, port=5000)
