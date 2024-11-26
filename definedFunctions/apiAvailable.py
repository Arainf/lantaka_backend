from flask import jsonify
from model import RoomType, Room, RoomReservation, Venue, VenueReservation
from datetime import datetime 

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
            RoomReservation.room_reservation_status.in_(["waiting", "ready", "onUse" ]),
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
