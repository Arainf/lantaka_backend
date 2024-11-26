from flask import jsonify
from model import db, Venue, Room, RoomType, VenueReservation, RoomReservation, GuestDetails, Receipt, Account
from datetime import datetime
from collections import defaultdict
import base64

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

def get_venue_data():
    venues = Venue.query.all()
    if venues:
        venuesHolder = []
        for venue in venues:
            venue_image_url = None
            if venue.venue_img:
                venue_image_blob = base64.b64encode(venue.venue_img).decode('utf-8')
                venue_image_url = f"data:image/webp;base64,{venue_image_blob}"
            
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
    return jsonify({"error": "No venue data found"}), 404

def get_room_data():
    rooms = Room.query.all()
    if rooms:
        roomsHolder = []
        for room in rooms:
            room_image_url = None
            if room.room_type and room.room_type.room_type_img:
                room_image_blob = base64.b64encode(room.room_type.room_type_img).decode('utf-8')
                room_image_url = f"data:image/webp;base64,{room_image_blob}"
            
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
    return jsonify({"error": "No room data found"}), 404

def get_reservations():
    roomReservations = RoomReservation.query.all()
    venueReservations = VenueReservation.query.all()

    if not roomReservations and not venueReservations:
        return jsonify({"error": "No reservations found"}), 404

    reservationsHolder = []
    date_time_format = "%Y-%m-%d %H:%M:%S"
    room_counts = defaultdict(int)
    venue_counts = defaultdict(int)

    for reservation in roomReservations:
        room_counts[reservation.guest_id] += 1

    for reservation in venueReservations:
        venue_counts[reservation.guest_id] += 1

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
            "guest_name": f"{guest.guest_fName} {guest.guest_lName}",
            "guest_email": guest.guest_email,
            "account_name": f"{account.account_fName} {account.account_lName}",
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
            "guest_name": f"{guest.guest_fName} {guest.guest_lName}",
            "guest_email": guest.guest_email,
            "account_name": f"{account.account_fName} {account.account_lName}",
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

def get_calendar_reservations(date):
    try:
        # Convert the date string to a datetime object
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Query room reservations
        room_reservations = RoomReservation.query.filter(
            RoomReservation.room_reservation_booking_date_start <= target_date,
            RoomReservation.room_reservation_booking_date_end >= target_date
        ).all()
        
        # Query venue reservations
        venue_reservations = VenueReservation.query.filter(
            VenueReservation.venue_reservation_booking_date_start <= target_date,
            VenueReservation.venue_reservation_booking_date_end >= target_date
        ).all()
        
        calendar_data = []
        
        # Process room reservations
        for reservation in room_reservations:
            guest = GuestDetails.query.filter_by(guest_id=reservation.guest_id).first()
            account = Account.query.filter_by(account_id=reservation.account_id).first()
            
            calendar_data.append({
                "checkIn": reservation.room_reservation_check_in_time.strftime('%H:%M:%S'),
                "checkOut": reservation.room_reservation_check_out_time.strftime('%H:%M:%S'),
                "dateEnd": reservation.room_reservation_booking_date_end.strftime('%Y-%m-%d'),
                "dateStart": reservation.room_reservation_booking_date_start.strftime('%Y-%m-%d'),
                "employee": f"{account.account_fName} {account.account_lName}",
                "guests": f"{guest.guest_fName} {guest.guest_lName}",
                "id": reservation.room_id,
                "reservationid": reservation.room_reservation_id,
                "status": reservation.room_reservation_status,
                "type": "room"
            })
        
        # Process venue reservations
        for reservation in venue_reservations:
            guest = GuestDetails.query.filter_by(guest_id=reservation.guest_id).first()
            account = Account.query.filter_by(account_id=reservation.account_id).first()
            
            calendar_data.append({
                "checkIn": reservation.venue_reservation_check_in_time.strftime('%H:%M:%S'),
                "checkOut": reservation.venue_reservation_check_out_time.strftime('%H:%M:%S'),
                "dateEnd": reservation.venue_reservation_booking_date_end.strftime('%Y-%m-%d'),
                "dateStart": reservation.venue_reservation_booking_date_start.strftime('%Y-%m-%d'),
                "employee": f"{account.account_fName} {account.account_lName}",
                "guests": f"{guest.guest_fName} {guest.guest_lName}",
                "id": reservation.venue_id,
                "reservationid": reservation.venue_reservation_id,
                "status": reservation.venue_reservation_status,
                "type": "venue"
            })
        
        return jsonify(calendar_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500