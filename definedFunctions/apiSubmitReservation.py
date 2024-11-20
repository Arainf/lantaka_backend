from flask import jsonify, request
from model import Account, RoomReservation, VenueReservation, Receipt, Discounts, AdditionalFees, GuestDetails, db
from datetime import datetime, date, time
import json

def submit_reservation():
    try:
        data = request.json  # Get JSON data from the request

        # Check if the account_id exists in the Account table
        account_id = data['accountId']
        account = db.session.query(Account).filter_by(account_id=account_id).first()
        if not account:
            return jsonify({'error': 'Invalid account ID'}), 400
        
        reservationType = data['reservationType']

        # Check if the guest already exists
        existing_guest = db.session.query(GuestDetails).filter_by(
            guest_email=data['email'],
            guest_type=data['clientType']
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

        # Parse room and venue dates
        date_start_Room = datetime.fromisoformat(data['dateRangeRoom']['from'].replace('Z', '')) if data.get('dateRangeRoom', {}).get('from') else None
        date_end_Room = datetime.fromisoformat(data['dateRangeRoom']['to'].replace('Z', '')) if data.get('dateRangeRoom', {}).get('to') else None
        check_in_time = time(13, 0)
        date_start_Venue = datetime.fromisoformat(data.get('dateRangeVenue', {}).get('from', '').replace('Z', '')) if data.get('dateRangeVenue', {}).get('from') else None
        date_end_Venue = datetime.fromisoformat(data.get('dateRangeVenue', {}).get('to', '').replace('Z', '')) if data.get('dateRangeVenue', {}).get('to') else None
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
        
        if reservationType == "room" or reservationType == "both" :
            if date_start_Room and date_end_Room:
                for room_category in ['double', 'triple', 'matrimonial']:  # Add other categories as needed
                    for room_id in data['selectedReservationRooms'].get(room_category, []):
                        new_reservation = RoomReservation(
                            room_id=room_id,
                            guest_id=new_guest.guest_id,  # Use the guest_id from the existing or newly created guest
                            account_id=account_id,
                            receipt_id=new_receipt.receipt_id,  # Link to the Receipt
                            room_reservation_booking_date_start=date_start_Room.date(),
                            room_reservation_booking_date_end=date_end_Room.date(),
                            room_reservation_check_in_time=check_in_time,
                            room_reservation_check_out_time=check_out_time,
                            room_reservation_status="waiting",
                            room_reservation_additional_notes=add_notes,
                            room_reservation_pop=None,
                            reservation_type=reservationType
                        )
                        db.session.add(new_reservation)

        # Create VenueReservation entries if there are valid venue dates
        if reservationType == "venue" or reservationType == "both" :
            if date_start_Venue and date_end_Venue:
                for venue_id in data['selectedReservationVenues']:
                    new_reservation = VenueReservation(
                        venue_id=venue_id,
                        guest_id=new_guest.guest_id,  # Use the guest_id from the existing or newly created guest
                        account_id=account_id,
                        receipt_id=new_receipt.receipt_id,  # Link to the Receipt
                        venue_reservation_booking_date_start=date_start_Venue.date(),
                        venue_reservation_booking_date_end=date_end_Venue.date(),
                        venue_reservation_check_in_time=check_in_time,
                        venue_reservation_check_out_time=check_out_time,
                        venue_reservation_status="waiting",
                        venue_reservation_additional_notes=add_notes,
                        venue_reservation_pop=None,
                        reservation_type=reservationType
                    )
                    db.session.add(new_reservation)

        # Commit all changes to the database
        db.session.commit()

        return jsonify({'message': 'Reservation and receipt submitted successfully!', 'receipt_id': new_receipt.receipt_id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
