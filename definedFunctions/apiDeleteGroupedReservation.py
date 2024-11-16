from flask import Flask, jsonify, request
from model import db, RoomReservation, VenueReservation, Receipt

def delete_reservations():
    data = request.get_json()  # Get the JSON data from the request body
    reservation_ids = data.get('reservation_ids', [])
    guest_id = data.get('guest_id')  # Extract guest_id from the request

    print("Reservation IDs received:", reservation_ids)
    print("Guest ID received:", guest_id)

    # Check if reservation_ids or guest_id is missing
    if not reservation_ids:
        print("No reservation IDs provided")
        return jsonify({"error": "No reservation IDs provided"}), 400
    if not guest_id:
        print("No guest ID provided")
        return jsonify({"error": "No guest ID provided"}), 400

    try:
        # Start a transaction
        with db.session.begin():
            # Delete room reservations
            room_reservations = RoomReservation.query.filter(
                RoomReservation.room_reservation_id.in_(reservation_ids)
            ).all()
            print("Room reservations to delete:", room_reservations)

            for reservation in room_reservations:
                db.session.delete(reservation)

            # Delete venue reservations
            venue_reservations = VenueReservation.query.filter(
                VenueReservation.venue_reservation_id.in_(reservation_ids)
            ).all()
            print("Venue reservations to delete:", venue_reservations)

            for reservation in venue_reservations:
                db.session.delete(reservation)

            # Delete receipts linked to the guest_id
            receipts = Receipt.query.filter_by(guest_id=guest_id).all()
            print(f"Receipts for guest ID {guest_id}:", receipts)

            for receipt in receipts:
                # Clear relationships before deletion
                receipt.discounts = []  # Clear discounts relationship
                receipt.additional_fees = []  # Clear additional fees relationship
                db.session.delete(receipt)

        # If we reach here, the transaction was successful
        print("Deletion successful")
        return jsonify({"message": "Successfully deleted specified reservations and receipts"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting reservations: {str(e)}")  # Log the full error
        return jsonify({"error": str(e)}), 500
