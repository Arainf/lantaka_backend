from flask import request, jsonify
from model import db, RoomReservation, VenueReservation, GuestDetails, Receipt, Discounts, Account
from datetime import datetime, time, date
from utils import parse_datetime_with_timezone, check_internet_connection
from definedFunctions.apiMailer import send_email_confirmation

def submit_reservation():
    try:
        data = request.json  # Get JSON data from the request

        reservation_time = datetime.now()
        reservation_type = data.get('reservationType')

        # Check if the account_id exists in the Account table
        account_id = data['accountId']
        account = db.session.query(Account).filter_by(account_id=account_id).first()
        if not account:
            return jsonify({'error': 'Invalid account ID'}), 400

        # Check if the guest already exists
        existing_guest = db.session.query(GuestDetails).filter_by(
            guest_email=data['email'],
            guest_fName=data['firstName'],
            guest_lName=data['lastName']
        ).first()

        if existing_guest:
            # Reuse the existing guest_id
            new_guest = existing_guest
        else:
            # Create a new GuestDetails entry
            new_guest = GuestDetails(
                guest_type=data['clientType'],
                guest_fName=data['firstName'],
                guest_lName=data['lastName'],
                guest_email=data['email'],
                guest_phone=data['phone'],
                guest_gender=data['gender'],
                guest_messenger_account=data['messengerAccount'],
                guest_designation=data['designation'],
                guest_address=data['address'],
                guest_client=data['clientAlias']
            )
            db.session.add(new_guest)
            db.session.flush()  # Ensure the guest_id is available

        # Parse room and venue dates using the utility function
        date_start_Room = parse_datetime_with_timezone(data['dateRangeRoom']['from']) if data.get('dateRangeRoom', {}).get('from') else None
        date_end_Room = parse_datetime_with_timezone(data['dateRangeRoom']['to']) if data.get('dateRangeRoom', {}).get('to') else None
        check_in_time = time(13, 0)
        date_start_Venue = parse_datetime_with_timezone(data['dateRangeVenue']['from']) if data.get('dateRangeVenue', {}).get('from') else None
        date_end_Venue = parse_datetime_with_timezone(data['dateRangeVenue']['to']) if data.get('dateRangeVenue', {}).get('to') else None
        check_out_time = time(12, 0)

        # Extract additional notes and prices for the receipt
        add_notes = data.get('addNotes', '')
        initial_total_price = data.get('initialTotalPrice', 0.0)
        total_price = data.get('totalPrice', 0.0)

        # Create the Receipt entry
        new_receipt = Receipt(
            guest_id=new_guest.guest_id,
            receipt_date=date.today(),
            receipt_initial_total=initial_total_price,
            receipt_total_amount=total_price
        )

        # Add discounts to the receipt
        discount_list = data.get('discount', [])
        for discount in discount_list:
            discount_name = discount.get("type")
            discount_amount = discount.get("Amount")
            existing_discount = db.session.query(Discounts).filter_by(discount_name=discount_name).first()

            if existing_discount:
                new_receipt.discounts.append(existing_discount)
            else:
                new_discount = Discounts(discount_name=discount_name, discount_percentage=discount_amount)
                db.session.add(new_discount)
                new_receipt.discounts.append(new_discount)

        db.session.add(new_receipt)
        db.session.flush()  # Ensure the receipt_id is available

        # Create RoomReservation entries if there are valid room dates
        if date_start_Room and date_end_Room and reservation_type in ['room', 'both']:
            for room_category in ['double', 'triple', 'matrimonial']:  # Add other categories as needed
                for room_id in data['selectedReservationRooms'].get(room_category, []):
                    new_reservation = RoomReservation(
                        room_id=room_id,
                        guest_id=new_guest.guest_id,
                        account_id=account_id,
                        receipt_id=new_receipt.receipt_id,
                        room_reservation_booking_date_start=date_start_Room.date(),
                        room_reservation_booking_date_end=date_end_Room.date(),
                        room_reservation_check_in_time=check_in_time,
                        room_reservation_check_out_time=check_out_time,
                        room_reservation_status="waiting",
                        room_reservation_additional_notes=add_notes,
                        room_reservation_pop=None,
                        reservation_type=reservation_type,
                        reservation_time=reservation_time
                    )
                    db.session.add(new_reservation)

        # Create VenueReservation entries if there are valid venue dates
        if date_start_Venue and date_end_Venue and reservation_type in ['venue', 'both']:
            for venue_id in data['selectedReservationVenues']:
                new_reservation = VenueReservation(
                    venue_id=venue_id,
                    guest_id=new_guest.guest_id,
                    account_id=account_id,
                    receipt_id=new_receipt.receipt_id,
                    venue_reservation_booking_date_start=date_start_Venue.date(),
                    venue_reservation_booking_date_end=date_end_Venue.date(),
                    venue_reservation_check_in_time=check_in_time,
                    venue_reservation_check_out_time=check_out_time,
                    venue_reservation_status="waiting",
                    venue_reservation_additional_notes=add_notes,
                    venue_reservation_pop=None,
                    reservation_type=reservation_type,
                    reservation_time=reservation_time
                )
                db.session.add(new_reservation)

        # Commit all changes to the database
        db.session.commit()

        reservation_details = {
            "room": {
                "start_date": date_start_Room.strftime("%Y-%m-%d") if date_start_Room else None,
                "end_date": date_end_Room.strftime("%Y-%m-%d") if date_end_Room else None,
                "rooms": []
            },
            "venue": {
                "start_date": data.get('dateRangeVenue', {}).get('from'),
                "end_date": data.get('dateRangeVenue', {}).get('to'),
                "name": data.get('selectedVenue', 'Not specified')
            }
        }

        for category in ['double', 'triple', 'matrimonial']:
            count = len(data.get('selectedReservationRooms', {}).get(category, []))
            if count > 0:
                reservation_details["room"]["rooms"].append({"category": category, "count": count})

        is_online = check_internet_connection()
        success, result = send_email_confirmation(new_guest, new_receipt.receipt_id, reservation_details, reservation_type, is_online)

        message = "Your reservation and receipt have been submitted successfully!"
        if success:
            message += " A confirmation email has been sent." if is_online else f" A confirmation PDF has been generated: {result}"
        else:
            message += f" However, there was an issue with the confirmation: {result}"

        return jsonify({
            'message': message,
            'receiptId': str(new_receipt.receipt_id),
            'isOnline': is_online,
            'pdfPath': result if not is_online and success else None
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def update_reservation_status(event_id):
    reservation_id = request.args.get('id')
    new_status = request.args.get('status')
    event_type = request.args.get('type', '').lower()

    if not all([reservation_id, new_status, event_type]):
        return jsonify({'error': 'Missing required fields: id, status, or type'}), 400

    try:
        if event_type == 'venue':
            reservation = VenueReservation.query.filter_by(venue_reservation_id=event_id).first()
            if reservation:
                reservation.venue_reservation_status = new_status
                db.session.commit()
                return jsonify({'message': 'Venue reservation status updated successfully'}), 200
            return jsonify({'error': 'Venue reservation not found'}), 404

        elif event_type == 'room':
            reservation = RoomReservation.query.filter_by(room_reservation_id=event_id).first()
            if reservation:
                reservation.room_reservation_status = new_status
                db.session.commit()
                return jsonify({'message': 'Room reservation status updated successfully'}), 200
            return jsonify({'error': 'Room reservation not found'}), 404

        return jsonify({'error': 'Invalid reservation type'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred while updating the reservation: {str(e)}'}), 500

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