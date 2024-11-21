from flask import jsonify, request
from model import Account, RoomReservation, VenueReservation, Receipt, GuestDetails, Room, RoomType, db
from datetime import datetime, timedelta

def get_Reservations():
    filter_by = request.args.get('filter_by')  # Options: 'month', 'week'
    date_param = request.args.get('date')  # Expected format: YYYY-MM-DD

    try:
        filter_date = datetime.strptime(date_param, "%Y-%m-%d") if date_param else datetime.now()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    
    
    if filter_by == "month":
        start_date = filter_date.replace(day=1)
        next_month = start_date.month % 12 + 1
        end_date = start_date.replace(month=next_month, day=1) - timedelta(days=1)
    elif filter_by == "week":
        start_date = filter_date - timedelta(days=filter_date.weekday())  # Monday of the current week
        end_date = start_date + timedelta(days=6)  # Sunday of the current week
    else:
        start_date = None
        end_date = None

    if start_date and end_date:
        room_reservations = RoomReservation.query.filter(
            RoomReservation.room_reservation_booking_date_start >= start_date,
            RoomReservation.room_reservation_booking_date_start <= end_date
        ).all()

        venue_reservations = VenueReservation.query.filter(
            VenueReservation.venue_reservation_booking_date_start >= start_date,
            VenueReservation.venue_reservation_booking_date_start <= end_date
        ).all()
    else:
        room_reservations = RoomReservation.query.all()
        venue_reservations = VenueReservation.query.all()

    if not room_reservations and not venue_reservations:
        return jsonify({"error": "No reservations found"}), 404
    
    reservations_holder = []

    # Define date and time format
    date_time_format = "%Y-%m-%d %H:%M:%S"

    # Process room reservations
    for reservation in room_reservations:
        check_in_datetime = datetime.combine(
            reservation.room_reservation_booking_date_start, reservation.room_reservation_check_in_time
        )
        check_out_datetime = datetime.combine(
            reservation.room_reservation_booking_date_end, reservation.room_reservation_check_out_time
        )

        # Fetch related data
        guest = GuestDetails.query.filter_by(guest_id=reservation.guest_id).first()
        account = Account.query.filter_by(account_id=reservation.account_id).first()
        receipt = Receipt.query.filter_by(receipt_id=reservation.receipt_id).first()
        room = Room.query.filter_by(room_id=reservation.room_id).first()
        room_type = RoomType.query.filter_by(room_type_id=room.room_type_id).first() if room else None

        if not (guest and account and receipt and room and room_type):
            continue  # Skip if essential data is missing

        receipt_with_discount_holder = [
            {
                "discount_id": discount.discount_id,
                "discount_name": discount.discount_name,
                "discount_percentage": discount.discount_percentage,
            }
            for discount in getattr(receipt, 'discounts', [])  # Safely handle relationship
        ]

        reservation_data = {
            "reservation_id": reservation.room_reservation_id,
            "room_type": room_type.room_type_name,
            "guest_id": guest.guest_id,
            "guest_type": guest.guest_type,
            "reservation": room.room_id,
            "guest_name": f"{guest.guest_fName} {guest.guest_lName}",
            "guest_email": guest.guest_email,
            "account_name": f"{account.account_fName} {account.account_lName}",
            "receipt_date": receipt.receipt_date.strftime(date_time_format) if receipt.receipt_date else None,
            "receipt_initial_total": receipt.receipt_initial_total,
            "receipt_total_amount": receipt.receipt_total_amount,
            "receipt_discounts": receipt_with_discount_holder,
            "check_in_date": check_in_datetime.strftime(date_time_format),
            "check_out_date": check_out_datetime.strftime(date_time_format),
            "status": reservation.room_reservation_status,
            "additional_notes": reservation.room_reservation_additional_notes,
            "reservation_type": reservation.reservation_type,
        }
        reservations_holder.append(reservation_data)

    # Process venue reservations
    for reservation in venue_reservations:
        check_in_datetime = datetime.combine(
            reservation.venue_reservation_booking_date_start, reservation.venue_reservation_check_in_time
        )
        check_out_datetime = datetime.combine(
            reservation.venue_reservation_booking_date_end, reservation.venue_reservation_check_out_time
        )

        # Fetch related data
        guest = GuestDetails.query.filter_by(guest_id=reservation.guest_id).first()
        account = Account.query.filter_by(account_id=reservation.account_id).first()
        receipt = Receipt.query.filter_by(receipt_id=reservation.receipt_id).first()

        if not (guest and account and receipt):
            continue  # Skip if essential data is missing

        receipt_with_discount_holder = [
            {
                "discount_id": discount.discount_id,
                "discount_name": discount.discount_name,
                "discount_percentage": discount.discount_percentage,
            }
            for discount in getattr(receipt, 'discounts', [])  # Safely handle relationship
        ]

        reservation_data = {
            "reservation_id": reservation.venue_reservation_id,
            "guest_id": guest.guest_id,
            "guest_type": guest.guest_type,
            "reservation": reservation.venue_id,
            "guest_name": f"{guest.guest_fName} {guest.guest_lName}",
            "guest_email": guest.guest_email,
            "account_name": f"{account.account_fName} {account.account_lName}",
            "receipt_date": receipt.receipt_date.strftime(date_time_format) if receipt.receipt_date else None,
            "receipt_initial_total": receipt.receipt_initial_total,
            "receipt_total_amount": receipt.receipt_total_amount,
            "receipt_discounts": receipt_with_discount_holder,
            "check_in_date": check_in_datetime.strftime(date_time_format),
            "check_out_date": check_out_datetime.strftime(date_time_format),
            "status": reservation.venue_reservation_status,
            "additional_notes": reservation.venue_reservation_additional_notes,
            "reservation_type": reservation.reservation_type,
        }
        reservations_holder.append(reservation_data)

    return jsonify(reservations_holder), 200
