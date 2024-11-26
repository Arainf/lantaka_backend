from flask import jsonify, url_for, request, Response
from sqlalchemy.orm import joinedload, load_only
from model import Room, Venue, RoomType, GuestDetails


def get_room_and_venue():
    try:
        # Fetch rooms with their associated room types and guest details (via room_reservations)
        rooms = Room.query.options(
            joinedload(Room.room_type),  # Eagerly load room_type relationship
            joinedload(Room.room_reservations)  # Eagerly load room_reservations relationship
        ).all()

        # Fetch venues with only the required fields and guest details (via venue_reservations)
        venues = Venue.query.options(
            load_only(
                Venue.venue_id,
                Venue.venue_name,
                Venue.venue_description,
                Venue.venue_status,
                Venue.venue_pricing_internal,
                Venue.venue_pricing_external,
                Venue.venue_capacity,
                Venue.venue_img,
            ),
            joinedload(Venue.venue_reservations)  # Eagerly load venue_reservations relationship
        ).all()

        # Extract rooms data, including room type details and guest names for reservations with status 'done'
        rooms_data = [
            {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "room_status": room.room_status,
                "room_type": {
                    "room_type_id": room.room_type.room_type_id,
                    "room_type_name": room.room_type.room_type_name,
                    "room_type_description": room.room_type.room_type_description,
                    "room_type_price_internal": room.room_type.room_type_price_internal,
                    "room_type_price_external": room.room_type.room_type_price_external,
                    "room_type_capacity": room.room_type.room_type_capacity,
                    "room_type_img_url": url_for(
                        "serve_image", item_id=room.room_id, type="room", _external=True
                    )
                    if room.room_type and room.room_type.room_type_img
                    else None,
                } if room.room_type else None,
                "guests": [
                    reservation.guest.guest_fName + " " + reservation.guest.guest_lName 
                    for reservation in room.room_reservations
                    if reservation.room_reservation_status == 'done' and reservation.guest
                ]
            }
            for room in rooms
        ]

        # Extract venues data, including guest names for reservations with status 'done'
        venues_data = [
            {
                "venue_id": venue.venue_id,
                "venue_name": venue.venue_name,
                "venue_description": venue.venue_description,
                "venue_status": venue.venue_status,
                "venue_pricing_internal": venue.venue_pricing_internal,
                "venue_pricing_external": venue.venue_pricing_external,
                "venue_capacity": venue.venue_capacity,
                "venue_img_url": url_for(
                    "serve_image", item_id=venue.venue_id, type="venue", _external=True
                )
                if venue.venue_img
                else None,
                "guests": [
                    reservation.guest.guest_fName + " " + reservation.guest.guest_lName 
                    
                    for reservation in venue.venue_reservations
                    if reservation.venue_reservation_status == 'done' and reservation.guest
                ]
            }
            for venue in venues
        ]

        # Return the combined data as JSON
        return jsonify({"rooms": rooms_data, "venues": venues_data}), 200

    except Exception as e:
        # Handle any errors gracefully
        return (
            jsonify(
                {
                    "error": "An error occurred while fetching rooms and venues",
                    "message": str(e),
                }
            ),
            500,
        )


def serve_image(item_id):
    item_type = request.args.get('type')
    if item_type == 'room':
        if item_id.isdigit():
            # If the item_id is numeric, assume it's a RoomType ID
            room_type = RoomType.query.get(item_id)
            if room_type and room_type.room_type_img:
                return Response(room_type.room_type_img, mimetype='image/webp')
        else:
            # Otherwise, assume it's a Room identifier
            room = Room.query.filter_by(room_id=item_id).first()
            if room and room.room_type and room.room_type.room_type_img:
                return Response(room.room_type.room_type_img, mimetype='image/webp')
    elif item_type == 'venue':
        venue = Venue.query.get(item_id)
        if venue and venue.venue_img:
            return Response(venue.venue_img, mimetype='image/webp')
    return jsonify({'error': 'Image not found'}), 404


def get_RoomTypes():
    try:
        # Fetch all room types from the database
        room_types = RoomType.query.all()
        
        # Convert the room types to a list of dictionaries
        room_types_list = [
            {
                "room_type_id": room_type.room_type_id,
                "room_type_name": room_type.room_type_name,
            }
            for room_type in room_types
        ]
        
        # Return the room types as a JSON response
        return jsonify(room_types_list), 200
    except Exception as e:
        # Handle any unexpected errors and return an appropriate error response
        return jsonify({"error": "Failed to fetch room types", "message": str(e)}), 500