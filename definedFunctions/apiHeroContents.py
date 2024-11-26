from flask import jsonify, request
from model import db, Venue, Room, VenueReservation, RoomReservation
from datetime import datetime

def api_everythingCard():
    # Retrieve the date parameter from the query string
    date = request.args.get('date', None)

    try:
        # If a date is provided, parse it; otherwise, skip
        date_obj = None
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # Fetch all rooms and venues
        rooms = Room.query.all()
        venues = Venue.query.all()

        # Prepare default statuses
        reservation_status = {}
        if date_obj:
            # Query reservations for the given date
            venue_reservations = VenueReservation.query.filter(
                VenueReservation.venue_reservation_booking_date_start <= date_obj,
                VenueReservation.venue_reservation_booking_date_end >= date_obj
            ).all()
            room_reservations = RoomReservation.query.filter(
                RoomReservation.room_reservation_booking_date_start <= date_obj,
                RoomReservation.room_reservation_booking_date_end >= date_obj
            ).all()

            # Map reservation status
            for reserve in venue_reservations:
                reservation_status[f'venue_{reserve.venue_id}'] = reserve.venue_reservation_status
            for reserve in room_reservations:
                reservation_status[f'room_{reserve.room_id}'] = reserve.room_reservation_status

        # Group rooms by room type and add reservation status
        double_rooms = [
            {**room.to_dict(), "status": reservation_status.get(f'room_{room.room_id}', 'normal')}
            for room in rooms if room.room_type_id == 1
        ]
        triple_rooms = [
            {**room.to_dict(), "status": reservation_status.get(f'room_{room.room_id}', 'normal')}
            for room in rooms if room.room_type_id == 2
        ]
        matrimonial_rooms = [
            {**room.to_dict(), "status": reservation_status.get(f'room_{room.room_id}', 'normal')}
            for room in rooms if room.room_type_id == 3
        ]

        # Add venues and their reservation status
        venues_holder = [
            {**venue.to_dict(), "status": reservation_status.get(f'venue_{venue.venue_id}', 'normal')}
            for venue in venues
        ]

        return jsonify({
            "double_rooms": double_rooms,
            "triple_rooms": triple_rooms,
            "matrimonial_rooms": matrimonial_rooms,
            "venues_holder": venues_holder
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
