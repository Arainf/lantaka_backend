import base64
import bcrypt
from flask import Flask, request, jsonify, Response
from marshmallow import Schema, fields, validate, ValidationError
from flask_marshmallow import Marshmallow  # Correct import
from werkzeug.utils import secure_filename  # For secure image uploads
from flask_cors import CORS
from model import db, Account, Room, RoomType, Venue, VenueReservation
from datetime import datetime
from defaultValues import rooms, roomTypes, venues
from dummydata import venue_reservations, guests, accounts

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
    profileImageFile = fields.Raw(required=False)

# Initialize schema objects
account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)

# Simple route to test the API
@app.route('/', methods=['GET'])
def get_account():
    return jsonify("Hello World")

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
        username = firstName.lower() + lastName.lower()
        email = data['email']
        password = data['password']
        phone = data['phone']
        dob = data['dob']
        gender = data['gender']

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Handle profile image upload securely
        image_file = request.files.get('profileImageFile')
        account_img = None
        if image_file:
            filename = secure_filename(image_file.filename)
            if filename.endswith(('png', 'jpg', 'jpeg')):
                account_img = image_file.read()
            else:
                return jsonify({"message": "Invalid image format"}), 400

        # Check if the account already exists
        existing_accounts = Account.query.filter_by(account_email=email).first()
        if existing_accounts:
            return jsonify({"message": "Email already exists"}), 400

        # Create a new account
        new_account = Account(
            account_role=role,
            account_fName=firstName,
            account_lName=lastName,
            account_img=account_img,
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

        if user.account_img:
            image_blob = base64.b64encode(user.account_img).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_blob}"  # Assuming it's a JPEG, adjust if needed
        else:
            image_url = None  # Or a default image

        
        # Return relevant user data
        return jsonify({
            "message": "Login successful",
            "account_id": user.account_id,
            "imageUrl": image_url,
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


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    users = Account.query.all()
    if users:
        accounts = []
        for user in users:
            # Convert the blob (user.account_img) to a base64 string
            if user.account_img:
                image_blob = base64.b64encode(user.account_img).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{image_blob}"  # Assuming it's a JPEG, adjust if needed
            else:
                image_url = None  # Or a default image

            account_data = {
                "id": user.account_id,
                "email": user.account_email,
                "firstName": user.account_fName,
                "lastName": user.account_lName,
                "username": user.account_username,
                "imageUrl": image_url,  # Send the base64 string to the frontend
                "role": user.account_role,  # Include role in profile data
                "PhoneNumber": user.account_phone,
                "dob": user.account_dob.strftime('%Y-%m-%d'),  # Format date
                "gender": user.account_gender,
                "status": user.account_status,
                "created_at": user.account_created_at.strftime('%Y-%m-%d'), # Format
                "updated_at": user.account_updated_at.strftime('%Y-%m-%d'),
            }
            accounts.append(account_data)

        return jsonify(accounts), 200
    else:
        return jsonify({"error": "No accounts found"}), 404



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
    

@app.route('/api/rooms/<string:room_id>', methods=['GET'])
def get_room_details(room_id):
    room = Room.query.filter_by(room_id=room_id).first()
    if room:
        room_type = RoomType.query.filter_by(room_type_id=room.room_type_id).first()
        # guest = GuestDetails.query.filter_by(room_id=room.room_id).first()  # Assuming you have a relation with guests

        # Constructing the image URL
        image_url = f"http://localhost:5000/api/roomImage/{room_id}" if room_type and room_type.room_type_img else None
        
        room_data = {
            'room_name': room.room_name,
            'guest_name': "guest",  # f"{guest.guest_fName} {guest.guest_lName}" if guest else None,
            'check_in': '2024-05-30',  # Replace with actual data
            'check_out': '2024-05-30',  # Replace with actual data
            'image_url': image_url  # Adding the image URL to the response
        }
        return jsonify(room_data), 200
    else:
        return jsonify({'error': 'Room not found'}), 404


@app.route('/api/roomImage/<string:room_id>', methods=['GET'])
def serve_room_image(room_id):
    room = Room.query.filter_by(room_id=room_id).first()
    if room:
        room_type = RoomType.query.filter_by(room_type_id=room.room_type_id).first()
        if room_type and room_type.room_type_img:
            return Response(room_type.room_type_img, mimetype='image/webp')  # Adjust the mimetype accordingly
        else:
            return jsonify({'error': 'Image not found'}), 404
    else:
        return jsonify({'error': 'Room not found'}), 404
    

@app.route('/api/venues/<string:venue_id>', methods=['GET'])
def get_venue_details(venue_id):
    venue = Venue.query.filter_by(venue_id=venue_id).first()
    if venue:
        # guest = GuestDetails.query.filter_by(room_id=room.room_id).first()  # Assuming you have a relation with guests

        # Constructing the image URL
        image_url = f"http://localhost:5000/api/venueImage/{venue_id}"
        
        venue_data = {
            'venue_name': venue.venue_name,
            'guest_name': "guest",  # f"{guest.guest_fName} {guest.guest_lName}" if guest else None,
            'check_in': '2024-05-30',  # Replace with actual data
            'check_out': '2024-05-30',  # Replace with actual data
            'image_url': image_url  # Adding the image URL to the response
        }
        return jsonify(venue_data), 200
    else:
        return jsonify({'error': 'Room not found'}), 404

@app.route('/api/venueImage/<string:venue_id>', methods=['GET'])
def serve_venue_image(venue_id):
    venue = Venue.query.filter_by(venue_id=venue_id).first()
    if venue:
        if venue.venue_img:
            return Response(venue.venue_img, mimetype='image/webp')  # Adjust the mimetype accordingly
        else:
            return jsonify({'error': 'Image not found'}), 404
    else:
        return jsonify({'error': 'Room not found'}), 404
    

@app.route('/api/availabilityVenue/<string:date>', methods=['GET'])
def get_availability_venue(date):
    available_venue = VenueReservation.query.filter_by(venue_reservation_booking_date=date).all()
    if available_venue:
        venues_data = []
        for venue in available_venue:
            venues_data.append({
                'id':venue.venue_id,
                'status': venue.venue_reservation_status
            })
        return jsonify(venues_data), 200
    else:
        return jsonify({"error": "No venues available on the given date"}), 404



# Ensure the application context is active before creating tables
if __name__ == '__main__':
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
            db.session.add_all(accounts)
            db.session.add_all(guests)
            db.session.add_all(venue_reservations)
            db.session.commit()
            print("Venues inserted successfully!")
        else:
            print("Venues already exist, skipping insertion.")


    app.run(host='0.0.0.0', debug=True, port=5000)
