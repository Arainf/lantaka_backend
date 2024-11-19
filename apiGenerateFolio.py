from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from model import db, GuestDetails, RoomReservation, VenueReservation, Receipt, Room, Venue, RoomType
from datetime import datetime, timedelta
import jinja2
import pdfkit
import os
import traceback

# Configure PDFKit
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

def render_template(data):
    print("Rendering template...")
    template_loader = jinja2.FileSystemLoader(searchpath="./guestFolio/")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("guestFolioTemp.html")
    return template.render(data)

def generate_pdf(guest_data, output_dir="./output"):
    print("Generating PDF...")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"guest_folio_{guest_data['folio_number']}.pdf")
    html_content = render_template(guest_data)
    pdfkit.from_string(html_content, output_file, configuration=config)
    print(f"PDF generated at: {output_file}")
    return output_file

def generate_pdf_route():
    print("Received request for /generate-pdf")
    try:
        data = request.get_json()
        print("Request data:", data)
        
        guest_id = data.get('guest_id')
        reservation_ids = data.get('reservation_ids')
        reservation_type = data.get('type')

        if not reservation_ids:
            return jsonify({"error": "No reservation IDs provided"}), 400
        if not guest_id:
            return jsonify({"error": "No guest ID provided"}), 400

        with db.session.begin():
            guest = GuestDetails.query.get(guest_id)
            if not guest:
                return jsonify({"error": "Guest not found"}), 404

            room_reservations = []
            venue_reservations = []

            if reservation_type in ["room", "both"]:
                room_reservations = RoomReservation.query.filter(
                    RoomReservation.room_reservation_id.in_(reservation_ids),
                    RoomReservation.guest_id == guest_id
                ).all()

            if reservation_type in ["venue", "both"]:
                venue_reservations = VenueReservation.query.filter(
                    VenueReservation.venue_reservation_id.in_(reservation_ids),
                    VenueReservation.guest_id == guest_id
                ).all()

            all_reservations = room_reservations + venue_reservations
            if not all_reservations:
                return jsonify({"error": "No reservations found"}), 404

            receipt = Receipt.query.filter(
                Receipt.receipt_id.in_([r.receipt_id for r in all_reservations])
            ).first()

            if not receipt:
                return jsonify({"error": "Receipt not found"}), 404

            guest_data = {
                'client_name': guest.guest_client,
                'guest_name': f"{guest.guest_fName} {guest.guest_lName}",
                'guest_designation': guest.guest_designation,
                'guest_address': guest.guest_address,
                'payment_mode': "Bill to Finance",
                'rooms': [],
                'venues': [],
                'total_balance': receipt.receipt_total_amount,
                'folio_number': f"{guest.guest_id:03d}",
                'folio_status': 'Active',
                'number_of_pax': 1,
                'check_in_date': '',
                'check_out_date': ''
            }

            for room_res in room_reservations:
                room = Room.query.get(room_res.room_id)
                room_type = RoomType.query.get(room.room_type_id)
                
                if not guest_data['check_in_date']:
                    guest_data['check_in_date'] = room_res.room_reservation_booking_date_start.strftime('%m.%d.%y')
                    guest_data['check_out_date'] = room_res.room_reservation_booking_date_end.strftime('%m.%d.%y')

                days = (room_res.room_reservation_booking_date_end - room_res.room_reservation_booking_date_start).days
                daily_rate = room_type.room_type_price_internal if guest.guest_type == 'internal' else room_type.room_type_price_external

                room_charges = []
                room_balance = 0
                for i in range(days):
                    date = room_res.room_reservation_booking_date_start + timedelta(days=i)
                    charge = {
                        'date': date.strftime('%m.%d.%y'),
                        'reference_number': f'Room Fee {i+1}',
                        'description': 'Room Fee',
                        'base_charge': daily_rate,
                        'vat': 0,  # Add VAT calculation if needed
                        'discount': 0,  # Add discount calculation if needed
                        'misc_charges': 0,  # Add miscellaneous charges if needed
                        'lt': 0,  # Add LT calculation if needed
                        'st': 0,  # Add ST calculation if needed
                        'dr': daily_rate,
                        'cr': 0,
                        'balance': daily_rate * (i + 1)
                    }
                    room_charges.append(charge)
                    room_balance += daily_rate

                guest_data['rooms'].append({
                    'number': room.room_name,
                    'charges': room_charges,
                    'balance': room_balance
                })

            for venue_res in venue_reservations:
                venue = Venue.query.get(venue_res.venue_id)
                
                if not guest_data['check_in_date']:
                    guest_data['check_in_date'] = venue_res.venue_reservation_booking_date_start.strftime('%m.%d.%y')
                    guest_data['check_out_date'] = venue_res.venue_reservation_booking_date_end.strftime('%m.%d.%y')

                days = (venue_res.venue_reservation_booking_date_end - venue_res.venue_reservation_booking_date_start).days
                daily_rate = venue.venue_pricing_internal if guest.guest_type == 'internal' else venue.venue_pricing_external

                venue_charges = []
                venue_balance = 0
                for i in range(days):
                    date = venue_res.venue_reservation_booking_date_start + timedelta(days=i)
                    charge = {
                        'date': date.strftime('%m.%d.%y'),
                        'reference_number': f'Venue Fee {i+1}',
                        'description': 'Venue Fee',
                        'base_charge': daily_rate,
                        'vat': 0,  # Add VAT calculation if needed
                        'discount': 0,  # Add discount calculation if needed
                        'misc_charges': 0,  # Add miscellaneous charges if needed
                        'lt': 0,  # Add LT calculation if needed
                        'st': 0,  # Add ST calculation if needed
                        'dr': daily_rate,
                        'cr': 0,
                        'balance': daily_rate * (i + 1)
                    }
                    venue_charges.append(charge)
                    venue_balance += daily_rate

                guest_data['venues'].append({
                    'name': venue.venue_name,
                    'charges': venue_charges,
                    'balance': venue_balance
                })

            guest_data['total_balance'] = sum(room['balance'] for room in guest_data['rooms']) + sum(venue['balance'] for venue in guest_data['venues'])

            pdf_path = generate_pdf(guest_data)

            # Serve the file and delete it after serving
            response = send_file(pdf_path, as_attachment=True, mimetype='application/pdf')
            return response

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500