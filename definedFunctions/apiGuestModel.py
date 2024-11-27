from flask import jsonify
from model import GuestDetails 

def get_guests():
    guests = GuestDetails.query.all()
    if guests:
        guestsHolder = []
        for guest in guests:
            guest_data = {
                "guest_id": guest.guest_id,
                "guest_client": guest.guest_client,
                "guest_type": guest.guest_type,
                "guest_fName": guest.guest_fName,
                "guest_lName": guest.guest_lName,
                "guest_phone": guest.guest_phone,
                "guest_email": guest.guest_email,
                "guest_gender": guest.guest_gender,
                "guest_messenger_account": guest.guest_messenger_account,
                "guest_poi":guest.guest_poi,
                "guest_designation":guest.guest_designation,
                "guest_address": guest.guest_address,
            }
            guestsHolder.append(guest_data)

        return jsonify(guestsHolder), 200
    else:
        return jsonify({"error": "No guests found"}), 404