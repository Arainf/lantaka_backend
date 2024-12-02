from flask import Flask, request, jsonify, send_file, after_this_request, current_app
from fpdf import FPDF
import os
import traceback
import logging
from datetime import datetime, timedelta

# Assuming these imports are correct for your project structure
from model import db, GuestDetails, RoomReservation, VenueReservation, Receipt, Room, Venue, RoomType

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GuestFolioPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.logo_path = os.path.join(os.path.dirname(__file__), "DefaultAssets", "adzuseal.png")

    def set_logo(self, path):
        self.logo_path = path

    def header(self):
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 8, 20)  # Adjust position and size as needed
        
        self.set_font('Arial', 'B', 24)
        self.cell(0, 10, 'Lantaka Guest Folio', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_route():
    logger.info("Received request for /generate-pdf")
    try:
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        guest_id = data.get('guest_id')
        reservation_ids = data.get('reservation_ids')
        reservation_type = data.get('type')
        discounts_fees = data.get('adddiscounts', [])
        additional_fees = data.get('addFees', [])
        base_price = data.get('basePrice')

        if not reservation_ids:
            logger.error("No reservation IDs provided")
            return jsonify({"error": "No reservation IDs provided"}), 400
        if not guest_id:
            logger.error("No guest ID provided")
            return jsonify({"error": "No guest ID provided"}), 400

        with db.session.begin():
            guest = GuestDetails.query.get(guest_id)
            if not guest:
                logger.error(f"Guest not found for ID: {guest_id}")
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
                logger.error(f"No reservations found for guest ID: {guest_id}")
                return jsonify({"error": "No reservations found"}), 404

            receipt_ids = [r.receipt_id for r in all_reservations if r.receipt_id is not None]
            if not receipt_ids:
                logger.error(f"No receipt IDs found for reservations")
                return jsonify({"error": "No receipts found for reservations"}), 404

            receipt = Receipt.query.filter(Receipt.receipt_id.in_(receipt_ids)).first()
            if not receipt:
                logger.error(f"No receipt found for IDs: {receipt_ids}")
                return jsonify({"error": "Receipt not found"}), 404

            guest_data = {
                'client_name': guest.guest_client,
                'guest_name': f"{guest.guest_fName} {guest.guest_lName}",
                'guest_designation': guest.guest_designation,
                'guest_address': guest.guest_address,
                'payment_mode': "Bill to Finance",
                'rooms': [],
                'venues': [],
                'discounts_fees': discounts_fees,
                'additional_fees': additional_fees,
                'subtotal': receipt.receipt_initial_total,
                'total_balance': receipt.receipt_total_amount,
                'folio_number': f"{guest.guest_id:03d}",
                'folio_status': 'Active',
                'number_of_pax': 1,
                'check_in_date': '',
                'check_out_date': ''
            }

            room_total = 0
            venue_total = 0


            # Process room reservations
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
                        'reference_number': f'Room Fee ',
                        'description': 'Room Fee',
                        'base_charge': daily_rate,
                        'vat': 0,
                        'discount': 0,
                        'dr': daily_rate,
                        'cr': 0,
                        'balance': daily_rate * (i + 1)
                    }
                    room_charges.append(charge)
                    room_balance += daily_rate

                room_total += room_balance  # Accumulate room total

                guest_data['rooms'].append({
                    'number': room.room_name,
                    'charges': room_charges,
                    'balance': room_balance
                })

            # Process venue reservations
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
                        'reference_number': f'Venue Fee',
                        'description': 'Venue Fee',
                        'base_charge': daily_rate,
                        'vat': 0,
                        'discount': 0,
                        'dr': daily_rate,
                        'cr': 0,
                        'balance': daily_rate * (i + 1)
                    }
                    venue_charges.append(charge)
                    venue_balance += daily_rate

                venue_total += venue_balance  # Accumulate venue total

                guest_data['venues'].append({
                    'name': venue.venue_name,
                    'charges': venue_charges,
                    'balance': venue_balance
                })

            pdf = GuestFolioPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Guest Details
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Guest Details", 0, 1)
            pdf.set_font("Arial", "", 10)
            pdf.cell(95, 7, f"Client: {guest_data['client_name']}", 0, 0)
            pdf.cell(95, 7, f"Folio No.: {guest_data['folio_number']}", 0, 1)
            pdf.cell(95, 7, f"Guest Name: {guest_data['guest_name']}", 0, 0)
            pdf.cell(95, 7, f"Status: {guest_data['folio_status']}", 0, 1)
            pdf.cell(95, 7, f"Designation: {guest_data['guest_designation']}", 0, 0)
            pdf.cell(95, 7, f"No. of Pax: {guest_data['number_of_pax']}", 0, 1)
            pdf.cell(95, 7, f"Address: {guest_data['guest_address']}", 0, 0)
            pdf.cell(95, 7, f"Check-In: {guest_data['check_in_date']}", 0, 1)
            pdf.cell(95, 7, f"Mode of Payment: {guest_data['payment_mode']}", 0, 0)
            pdf.cell(95, 7, f"Check-Out: {guest_data['check_out_date']}", 0, 1)
            pdf.ln(10)

            # Room Charges
            for room in guest_data['rooms']:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"Account Title: Room Fee", 0, 1)
                pdf.cell(0, 10, f"{room['number']}", 0, 1)
                pdf.set_font("Arial", "", 10)

                # Table header
                headers = ['Date', 'Ref. No.', 'Description', 'Base Charge', 'VAT', 'Disc.', 'Dr.', 'Cr.', 'Bal.']
                col_widths = [20, 20, 30, 25, 15, 15, 15, 15, 20]
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
                pdf.ln()

                # Table content
                for charge in room['charges']:
                    pdf.cell(20, 7, charge['date'], 1)
                    pdf.cell(20, 7, charge['reference_number'], 1)
                    pdf.cell(30, 7, charge['description'], 1)
                    pdf.cell(25, 7, f"{charge['base_charge']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['vat']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['discount']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['dr']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['cr']:.2f}", 1)
                    pdf.cell(20, 7, f"{charge['balance']:.2f}", 1)
                    pdf.ln()

                pdf.set_font("Arial", "B", 10)
                pdf.cell(155, 7, "Ending Balance:", 1)
                pdf.cell(20, 7, f"{room['balance']:.2f}", 1)
                pdf.ln(15)

            # Venue Charges
            for venue in guest_data['venues']:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Account Title: Venue Fee", 0, 1)
                pdf.cell(0, 10, f"Venue: {venue['name']}", 0, 1)
                pdf.set_font("Arial", "", 10)

                # Table header
                headers = ['Date', 'Ref. No.', 'Description', 'Base Charge', 'VAT', 'Disc.', 'Dr.', 'Cr.', 'Bal.']
                col_widths = [20, 20, 30, 25, 15, 15, 15, 15, 20]
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
                pdf.ln()

                # Table content
                for charge in venue['charges']:
                    pdf.cell(20, 7, charge['date'], 1)
                    pdf.cell(20, 7, charge['reference_number'], 1)
                    pdf.cell(30, 7, charge['description'], 1)
                    pdf.cell(25, 7, f"{charge['base_charge']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['vat']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['discount']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['dr']:.2f}", 1)
                    pdf.cell(15, 7, f"{charge['cr']:.2f}", 1)
                    pdf.cell(20, 7, f"{charge['balance']:.2f}", 1)
                    pdf.ln()

                pdf.set_font("Arial", "B", 10)
                pdf.cell(155, 7, "Ending Balance:", 1)
                pdf.cell(20, 7, f"{venue['balance']:.2f}", 1)
                pdf.ln(15)

            # Discounts Section
            # Discounts Section
            if discounts_fees:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Discounts", 0, 1)
                pdf.set_font("Arial", "", 10)
                
                headers = ['Description', 'Percentage/Amount']
                widths = [150, 35]
                
                # Headers for Discount section
                for i, header in enumerate(headers):
                    pdf.cell(widths[i], 7, header, 1, 0, 'C')
                pdf.ln()

                total_discount = 0
                for discount in discounts_fees:
                    pdf.cell(150, 7, discount['discount_name'], 1)
                    
                    pdf.cell(35, 7, f"{discount['discount_percentage']}% /{discount['discount_percentage'] * base_price / 100}  ", 1, 0, 'C')
                    pdf.ln()
                    
                    # Calculate total discount
                    total_discount += discount['discount_percentage'] * base_price / 100
                

                pdf.ln(10)

            # Additional Fees Section
            if additional_fees:
                pdf.ln(10)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Additional Fees", 0, 1)
                pdf.set_font("Arial", "", 10)

                headers = ['Description', 'Amount']
                widths = [150, 35]

                # Headers for Additional Fees section
                for i, header in enumerate(headers):
                    pdf.cell(widths[i], 7, header, 1, 0, 'C')
                pdf.ln()

                total_additional_fees = 0
                for fee in additional_fees:
                    pdf.cell(150, 7, fee['additional_fee_name'], 1)

                    pdf.cell(35, 7, f"{fee['additional_fee_amount']:.2f}", 1, 0, 'C')
                    pdf.ln()

                    # Calculate total additional fees
                    total_additional_fees += fee['additional_fee_amount']

            # Total Balance Calculation
            total_discount = sum((discount['discount_percentage'] * base_price / 100) for discount in discounts_fees)
            total_additional_fees = sum(fee['additional_fee_amount'] for fee in additional_fees)

            # Print the calculated values for debugging
            print(f"Total Discount: {total_discount}")
            print(f"Total Additional Fees: {total_additional_fees}")

            final_total = guest_data['total_balance']  
            # Print the final total balance
            print(f"Final Total Balance: {final_total}")


            # Total Balance
            pdf.set_font("Arial", "B", 12)
            pdf.cell(165, 10, "Total Balance:", 0)
            pdf.cell(20, 10, f"{final_total:.2f}", 0)

            pdf_path = os.path.join(current_app.root_path, f"guest_folio_{guest_data['folio_number']}.pdf")
            pdf.output(pdf_path)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(pdf_path)
                    logger.info(f"Temporary PDF file removed: {pdf_path}")
                except Exception as error:
                    logger.error(f"Error removing temporary PDF file: {error}")
                return response

            logger.info(f"PDF generated successfully: {pdf_path}")
            return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500