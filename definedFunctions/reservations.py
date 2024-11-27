from flask import request, jsonify
import logging
from model import db, RoomReservation, VenueReservation, GuestDetails, Receipt, Discounts, Account
from datetime import datetime, time, date
from utils import parse_datetime_with_timezone, check_internet_connection
from definedFunctions.apiMailer import send_email_confirmation
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.DEBUG)

def submit_reservation():
    try:
        # Get JSON data from the request
        data = request.json
        if not data:
            logging.error("No data received in request")
            return jsonify({'error': 'No data received'}), 400

        logging.debug(f"Received data: {data}")

        # Validate required fields
        required_fields = ['accountId', 'reservationType', 'firstName', 'lastName', 'email']
        for field in required_fields:
            if field not in data:
                logging.error(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400

        account_id = data['accountId']
        reservation_type = data['reservationType']

        # Check if the account_id exists in the Account table
        try:
            account = db.session.query(Account).filter_by(account_id=account_id).first()
            if not account:
                logging.error(f"Invalid account ID: {account_id}")
                return jsonify({'error': 'Invalid account ID'}), 400
        except SQLAlchemyError as e:
            logging.error(f"Database error when querying Account: {str(e)}")
            return jsonify({'error': 'Database error occurred'}), 500

        # Process guest details
        try:
            existing_guest = db.session.query(GuestDetails).filter_by(
                guest_email=data['email'],
                guest_fName=data['firstName'],
                guest_lName=data['lastName']
            ).first()

            if existing_guest:
                new_guest = existing_guest
            else:
                new_guest = GuestDetails(
                    guest_type=data.get('clientType'),
                    guest_fName=data['firstName'],
                    guest_lName=data['lastName'],
                    guest_email=data['email'],
                    guest_phone=data.get('phone'),
                    guest_gender=data.get('gender'),
                    guest_messenger_account=data.get('messengerAccount'),
                    guest_designation=data.get('designation'),
                    guest_address=data.get('address'),
                    guest_client=data.get('clientAlias')
                )
                db.session.add(new_guest)
                db.session.flush()
            logging.debug(f"Guest processed: {new_guest.guest_id}")
        except SQLAlchemyError as e:
            logging.error(f"Error processing guest details: {str(e)}")
            return jsonify({'error': 'Error processing guest details'}), 500

        # Parse dates
        try:
            date_start_Room = None
            date_end_Room = None
            date_start_Venue = None
            date_end_Venue = None

            if isinstance(data.get('dateRangeRoom'), dict):
                date_start_Room = parse_datetime_with_timezone(data['dateRangeRoom'].get('from'))
                date_end_Room = parse_datetime_with_timezone(data['dateRangeRoom'].get('to'))
            
            if isinstance(data.get('dateRangeVenue'), dict):
                date_start_Venue = parse_datetime_with_timezone(data['dateRangeVenue'].get('from'))
                date_end_Venue = parse_datetime_with_timezone(data['dateRangeVenue'].get('to'))

            logging.debug(f"Room Dates: {date_start_Room} - {date_end_Room}")
            logging.debug(f"Venue Dates: {date_start_Venue} - {date_end_Venue}")
        except ValueError as e:
            logging.error(f"Error parsing dates: {str(e)}")
            return jsonify({'error': 'Invalid date format'}), 400

        # Create Receipt
        try:
            new_receipt = Receipt(
                guest_id=new_guest.guest_id,
                receipt_date=date.today(),
                receipt_initial_total=data.get('initialTotalPrice', 0.0),
                receipt_total_amount=data.get('totalPrice', 0.0)
            )
            db.session.add(new_receipt)
            db.session.flush()
            logging.debug(f"Receipt created: {new_receipt.receipt_id}")
        except SQLAlchemyError as e:
            logging.error(f"Error creating receipt: {str(e)}")
            return jsonify({'error': 'Error creating receipt'}), 500

        # Process discounts
        try:
            for discount in data.get('discount', []):
                discount_name = discount.get("type")
                discount_amount = discount.get("Amount")
                if not discount_name or not isinstance(discount_amount, (int, float)):
                    logging.warning(f"Invalid discount data: {discount}")
                    continue
                existing_discount = db.session.query(Discounts).filter_by(discount_name=discount_name).first()
                if existing_discount:
                    new_receipt.discounts.append(existing_discount)
                else:
                    new_discount = Discounts(discount_name=discount_name, discount_percentage=discount_amount)
                    db.session.add(new_discount)
                    new_receipt.discounts.append(new_discount)
            logging.debug("Discounts processed")
        except SQLAlchemyError as e:
            logging.error(f"Error processing discounts: {str(e)}")
            return jsonify({'error': 'Error processing discounts'}), 500

        # Process room reservations
        if date_start_Room and date_end_Room and reservation_type in ['room', 'both']:
            selected_rooms = data.get('selectedReservationRooms', {})
            logging.debug(f"Selected rooms: {selected_rooms}")
            for room_category, room_ids in selected_rooms.items():
                if not isinstance(room_ids, list):
                    logging.error(f"Invalid room data for category {room_category}: {room_ids}")
                    continue
                for room_id in room_ids:
                    try:
                        new_reservation = RoomReservation(
                            room_id=room_id,
                            guest_id=new_guest.guest_id,
                            account_id=account_id,
                            receipt_id=new_receipt.receipt_id,
                            room_reservation_booking_date_start=date_start_Room.date(),
                            room_reservation_booking_date_end=date_end_Room.date(),
                            room_reservation_check_in_time=time(13, 0),
                            room_reservation_check_out_time=time(12, 0),
                            room_reservation_status="waiting",
                            room_reservation_additional_notes=data.get('addNotes', ''),
                            room_reservation_pop=None,
                            reservation_type=reservation_type,
                            reservation_time=datetime.now()
                        )
                        db.session.add(new_reservation)
                        logging.debug(f"Room reservation created for room: {room_id}")
                    except SQLAlchemyError as e:
                        logging.error(f"Error creating room reservation for room {room_id}: {str(e)}")
                        return jsonify({'error': f'Error creating room reservation for room {room_id}'}), 500

        # Process venue reservations
        if date_start_Venue and date_end_Venue and reservation_type in ['venue', 'both']:
            for venue_id in data.get('selectedReservationVenues', []):
                try:
                    new_reservation = VenueReservation(
                        venue_id=venue_id,
                        guest_id=new_guest.guest_id,
                        account_id=account_id,
                        receipt_id=new_receipt.receipt_id,
                        venue_reservation_booking_date_start=date_start_Venue.date(),
                        venue_reservation_booking_date_end=date_end_Venue.date(),
                        venue_reservation_check_in_time=time(13, 0),
                        venue_reservation_check_out_time=time(12, 0),
                        venue_reservation_status="waiting",
                        venue_reservation_additional_notes=data.get('addNotes', ''),
                        venue_reservation_pop=None,
                        reservation_type=reservation_type,
                        reservation_time=datetime.now()
                    )
                    db.session.add(new_reservation)
                    logging.debug(f"Venue reservation created for venue: {venue_id}")
                except SQLAlchemyError as e:
                    logging.error(f"Error creating venue reservation for venue {venue_id}: {str(e)}")
                    return jsonify({'error': f'Error creating venue reservation for venue {venue_id}'}), 500

        # Commit all changes to the database
        try:
            db.session.commit()
            logging.info("Database commit successful")
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Error committing to database: {str(e)}")
            return jsonify({'error': 'Error saving reservation'}), 500

        # Prepare reservation details for email confirmation
        reservation_details = {
            'room': {},
            'venue': {}
        }

        if date_start_Room and date_end_Room and reservation_type in ['room', 'both']:
            reservation_details['room'] = {
                'start_date': date_start_Room.strftime("%Y-%m-%d"),
                'end_date': date_end_Room.strftime("%Y-%m-%d"),
                'rooms': []
            }
            for room_category, room_ids in data.get('selectedReservationRooms', {}).items():
                reservation_details['room']['rooms'].append({
                    'category': room_category,
                    'count': len(room_ids)
                })

        if date_start_Venue and date_end_Venue and reservation_type in ['venue', 'both']:
            reservation_details['venue'] = {
                'start_date': date_start_Venue.strftime("%Y-%m-%d"),
                'end_date': date_end_Venue.strftime("%Y-%m-%d"),
                'name': ', '.join(data.get('selectedReservationVenues', []))
            }

        # Send email confirmation
        try:
            is_online = check_internet_connection()
            success, result = send_email_confirmation(new_guest, new_receipt.receipt_id, reservation_details, reservation_type, is_online)
            message = "Your reservation and receipt have been submitted successfully!"
            if success:
                message += " A confirmation email has been sent." if is_online else f" A confirmation PDF has been generated: {result}"
            else:
                logging.warning(f"Email issue: {result}")
                message += f" However, there was an issue with the confirmation: {result}"
        except Exception as e:
            logging.error(f"Error in email confirmation: {str(e)}")
            message = "Reservation submitted successfully, but there was an issue sending the confirmation."

        return jsonify({'message': message, 'receiptId': str(new_receipt.receipt_id)}), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

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
    try:
        # Query reservations excluding those with "done" status
        venue_reservations = VenueReservation.query.filter(
            VenueReservation.venue_reservation_status.in_(
                ["waiting", "ready", "onUse", "cancelled", "onCleaning"]
            )
        ).all()

        
        room_reservations = RoomReservation.query.filter(
            RoomReservation.room_reservation_status.in_(
                ["waiting", "ready", "onUse", "cancelled", "onCleaning"]
            )
        ).all()

        if not venue_reservations and not room_reservations:
            return jsonify({"message": "No active reservations found"}), 404

        reservations = []
        
        # Process venue reservations
        for venue in venue_reservations:
            reservations.append({
                'reservationid': venue.venue_reservation_id,
                'id': venue.venue_id,
                'type': 'venue',
                'dateStart': venue.venue_reservation_booking_date_start.isoformat(),
                'dateEnd': venue.venue_reservation_booking_date_end.isoformat(),
                'status': venue.venue_reservation_status,
                'guests': f"{venue.guest.guest_fName} {venue.guest.guest_lName}",
                'employee': f"{venue.account.account_fName} {venue.account.account_lName}",
                'checkIn': venue.venue_reservation_check_in_time.isoformat(),
                'checkOut': venue.venue_reservation_check_out_time.isoformat(),
            })
        
        # Process room reservations
        for room in room_reservations:
            reservations.append({
                'reservationid': room.room_reservation_id,
                'id': room.room_id,
                'type': 'room',
                'dateStart': room.room_reservation_booking_date_start.isoformat(),
                'dateEnd': room.room_reservation_booking_date_end.isoformat(),
                'status': room.room_reservation_status,
                'guests': f"{room.guest.guest_fName} {room.guest.guest_lName}",
                'employee': f"{room.account.account_fName} {room.account.account_lName}",
                'checkIn': room.room_reservation_check_in_time.isoformat(),
                'checkOut': room.room_reservation_check_out_time.isoformat(),
            })

        return jsonify(reservations), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500