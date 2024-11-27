from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
from flask_mail import Mail
from model import db, Room, RoomType, Venue, VenueReservation
from schemas import ma
from utils import search_guests
from definedFunctions.auth import register, login, simple_login
from definedFunctions.reservations import submit_reservation, update_reservation_status, get_reservation_calendar
from definedFunctions.data_retrieval import get_venue_data, get_room_data, get_reservations, api_everythingAvailable, get_calendar_reservations
from definedFunctions.apiAccountModel import get_accounts
from definedFunctions.apiGuestModel import get_guests
from definedFunctions.apiDiscounts import get_discounts, insert_discounts
from definedFunctions.apiAdditionalFees import get_AdditionalFees, insert_AdditionalFees, get_additional_fees, add_fee, update_fee, delete_fee, delete_guests, delete_account, test
from definedFunctions.apiReservations import get_Reservations, get_waiting_reservations, get_ready_reservations, get_onUse_reservations
from definedFunctions.apiPrice import get_Price
from definedFunctions.apiDeleteGroupedReservation import delete_reservations
from definedFunctions.apiStatusGroupedChange import change_status
from definedFunctions.apiAvailable import get_availability, api_availableRooms , api_availableVenues
from definedFunctions.apiReservationNotes import update_notes
from apiGenerateFolio import generate_pdf_route
from definedFunctions.apiContents import get_room_and_venue, get_RoomTypes, serve_image
from definedFunctions.apiRoomVenueContent import delete_venue_room, update_venue_room, create_venue_room
from definedFunctions.apiUtilities import add_discount, edit_discount, delete_discount
from definedFunctions.apiRoomTypes import get_room_types, update_room_type
from definedFunctions.apiNotification import mark_Read_Notification, create_Notification, get_Notification
from definedFunctions.apiMailer import send_email_confirmation
from definedFunctions.apiHeroContents import api_everythingCard
from definedFunctions.apiDashboardData import get_dashboard_data
from defaultValues import rooms, roomTypes, venues
from definedFunctions.scheduler import init_cleaning_scheduler

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/lantaka_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

# Email configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='lantakahotel2024@gmail.com',
    MAIL_PASSWORD='apve glqg cyux pqzj',
    MAIL_DEFAULT_SENDER='lantakahotel2024@gmail.com',
)

# Initialize extensions
db.init_app(app)
ma.init_app(app)
mail = Mail(app)
app.mail = mail

# Dashboard
@app.route('/api/dashboardData', methods=['GET'])
def dashboard_data():
    return get_dashboard_data()

# Route registrations
app.add_url_rule('/register', 'register', register, methods=['POST'])
app.add_url_rule('/login', 'login', login, methods=['POST'])
app.add_url_rule('/deletelogin', 'simple_login', simple_login, methods=['POST'])
app.add_url_rule('/api/submitReservation', 'submit_reservation', submit_reservation, methods=['POST'])
app.add_url_rule('/api/reservationCalendar/<int:event_id>', 'update_reservation_status', update_reservation_status, methods=['PUT'])
app.add_url_rule('/api/venueData', 'get_venue_data', get_venue_data, methods=['GET'])
app.add_url_rule('/api/roomData', 'get_room_data', get_room_data, methods=['GET'])
app.add_url_rule('/api/reservations', 'get_reservations', get_reservations, methods=['GET'])

# Other route registrations (from definedFunctions)
app.add_url_rule('/api/accounts', 'get_accounts', get_accounts, methods=['GET'])
app.add_url_rule('/api/guests', 'get_guests', get_guests, methods=['GET'])
app.add_url_rule('/api/getDiscounts', 'get_discounts', get_discounts, methods=['GET'])
app.add_url_rule('/api/getAddFees', 'get_AdditionalFees', get_AdditionalFees, methods=['GET'])
app.add_url_rule('/api/getReservations', 'get_Reservations', get_Reservations, methods=['GET'])
app.add_url_rule('/api/getReservationsWaiting', 'get_waiting_reservations', get_waiting_reservations, methods=['GET'])
app.add_url_rule('/api/getReservationsReady', 'get_ready_reservations', get_ready_reservations, methods=['GET'])
app.add_url_rule('/api/getReservationsOnUse', 'get_onUse_reservations', get_onUse_reservations, methods=['GET'])
app.add_url_rule('/api/getPrice/<string:guestType>', 'get_Price', get_Price, methods=['GET'])
app.add_url_rule('/api/availableRooms/<string:dateStart>/<string:dateEnd>', 'api_availableRooms', api_availableRooms , methods=['GET'])
app.add_url_rule('/api/availableVenues/<string:dateStart>/<string:dateEnd>', 'api_availableVenues', api_availableVenues , methods=['GET'])
app.add_url_rule('/api/getRoomandVenue', 'get_room_and_venue', get_room_and_venue , methods=['GET'])
app.add_url_rule('/api/getRoomTypes', 'get_RoomTypes', get_RoomTypes , methods=['GET'])
app.add_url_rule('/api/roomTypes', 'get_room_types', get_room_types , methods=['GET'])
app.add_url_rule('/api/getAddFees2', 'get_additional_fees', get_additional_fees , methods=['GET'])
app.add_url_rule('/api/clients', 'search_guests', search_guests , methods=['GET'])
app.add_url_rule('/api/everythingAvailable', 'api_everythingAvailable', api_everythingAvailable , methods=['GET'])
app.add_url_rule('/api/image/<string:item_id>', 'serve_image', serve_image , methods=['GET'])
app.add_url_rule('/api/getreservationCalendar', 'get_reservation_calendar', get_reservation_calendar, methods=['GET'])
app.add_url_rule('/api/getCards', 'api_everythingCard', api_everythingCard, methods=['GET'])
app.add_url_rule('/api/getreservationCalendar/<string:date>', 'get_calendar_reservations', get_calendar_reservations, methods=['GET'])


# Notifications
app.add_url_rule('/api/notifications/unread', 'get_Notification', get_Notification, methods=['GET'])
app.add_url_rule('/api/notifications/create', 'create_Notification', create_Notification, methods=['POST'])
app.add_url_rule('/api/notifications/markRead', 'mark_Read_Notification', mark_Read_Notification, methods=['PATCH'])

# POST methods
app.add_url_rule('/api/insertDiscount', 'insert_discount', insert_discounts, methods=['POST'])
app.add_url_rule('/api/insertAdditionalFee', 'insert_AdditionalFees', insert_AdditionalFees, methods=['POST'])
app.add_url_rule('/api/generate-pdf', 'generate_pdf_route', cross_origin()(generate_pdf_route), methods=['POST'])
app.add_url_rule('/api/add-venue-room', 'create_venue_room', create_venue_room, methods=['POST'])
app.add_url_rule('/api/discountAdd', 'add_discount', add_discount, methods=['POST'])
app.add_url_rule('/api/addFee', 'insert_AdditionalFees', insert_AdditionalFees, methods=['POST'])

# DELETE methods
app.add_url_rule('/api/delete_reservations', 'delete_reservations', delete_reservations, methods=['DELETE'])
app.add_url_rule('/api/venue-room/<string:item_id>', 'delete_venue_room', delete_venue_room, methods=['DELETE'])
app.add_url_rule('/api/discountDelete', 'delete_discount', delete_discount, methods=['DELETE'])
app.add_url_rule('/api/deleteFee/<int:id>', 'delete_fee', delete_fee, methods=['DELETE'])
app.add_url_rule('/api/deleteGuests/<int:id>', 'delete_guests', delete_guests, methods=['DELETE'])
app.add_url_rule('/api/deleteAccount/<int:id>', 'delete_account', delete_account, methods=['DELETE'])

# PUT methods
app.add_url_rule('/api/change_status', 'change_status' , change_status, methods=['PUT'])
app.add_url_rule('/api/update_notes', 'update_notes' , update_notes, methods=['PUT'])
app.add_url_rule('/api/venue-room/<string:item_id>', 'update_venue_room' , update_venue_room, methods=['PUT'])
app.add_url_rule('/api/discountEdit', 'edit_discount' , edit_discount, methods=['PUT'])
app.add_url_rule('/api/roomTypes/<int:id>', 'update_room_type' , update_room_type, methods=['PUT'])
app.add_url_rule('/api/updateFee/<int:id>', 'update_fee' , update_fee, methods=['PUT'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_cleaning_scheduler(app)
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
    from definedFunctions.apiMailer import configure_mail
    configure_mail(app)
    app.run(host='0.0.0.0', debug=True, port=5000)

