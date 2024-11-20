from flask import jsonify, request
from model import db, RoomReservation, VenueReservation

def update_notes():
    data = request.get_json()  # Get the JSON data from the request body
    reservation_ids = data.get('reservation_ids', [])  # List of reservation IDs
    # guest_id = data.get('guest_id')  # Guest ID
    notes = data.get('notes')  # Notes to be added/updated
    reservation_type = data.get('type')  # Reservation type (room or venue)

    print("Reservation IDs received:", reservation_ids)
    # print("Guest ID received:", guest_id)
    print("Notes received:", notes)
    print("Reservation type received:", reservation_type)

    # Check if necessary data is provided
    if not reservation_ids:
        print("No reservation IDs provided")
        return jsonify({"error": "No reservation IDs provided"}), 400
    # if not guest_id:
    #     print("No guest ID provided")
    #     return jsonify({"error": "No guest ID provided"}), 400
    if not notes:
        print("No notes provided")
        return jsonify({"error": "No notes provided"}), 400
    if not reservation_type:
        print("No reservation type provided")
        return jsonify({"error": "No reservation type provided"}), 400

    try:
        # Start a transaction
        with db.session.begin():
            # If the type is "room", update the notes for RoomReservation
            if reservation_type == "room" or reservation_type == "both":
                room_reservations = RoomReservation.query.filter(
                    RoomReservation.room_reservation_id.in_(reservation_ids)
                ).all()
                print("Room reservations to update notes:", room_reservations)

                for reservation in room_reservations:
                    reservation.room_reservation_additional_notes = notes
                    db.session.add(reservation)

            # If the type is "venue", update the notes for VenueReservation
            elif reservation_type == "venue" or reservation_type == "both":
                venue_reservations = VenueReservation.query.filter(
                    VenueReservation.venue_reservation_id.in_(reservation_ids)
                ).all()
                print("Venue reservations to update notes:", venue_reservations)

                for reservation in venue_reservations:
                    reservation.venue_reservation_additional_notes = notes
                    db.session.add(reservation)

            # Handle invalid type
            else:
                print("Invalid reservation type provided")
                return jsonify({"error": "Invalid reservation type provided"}), 400

        # Commit the changes if all updates were successful
        print("Notes update successful")
        return jsonify({"message": "Successfully updated reservation notes"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error updating notes: {str(e)}")  # Log the full error
        return jsonify({"error": str(e)}), 500
