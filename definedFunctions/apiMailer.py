from flask import current_app
from flask_mail import Message
from fpdf import FPDF
from datetime import datetime
import os

def configure_mail(app):
    global mail
    mail = app.mail

def send_email_confirmation(guest, receipt_id, reservation_details, reservation_type, is_online=True):
    subject = "Reservation Confirmation"
    
    def format_date(date_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%B %d, %Y")
        except ValueError:
            return date_str  # Return the original string if parsing fails

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Untitled%20(1080%20x%201920%20px)-J7cpQGEuCaH3LdLeDAKF8FI7KG8QI7.png" 
             alt="Lantaka Reservation System" 
             style="max-width: 100%; height: auto;">
        <div style="padding: 20px; background-color: #ffffff;">
            <h2 style="color: #1a237e;">Reservation Confirmation</h2>
            <p>Dear {guest.guest_fName} {guest.guest_lName},</p>
            <p>Thank you for choosing Lantaka Reservation System. Your reservation has been successfully submitted.</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #1a237e; margin-top: 0;">Reservation Details:</h3>
                <ul style="list-style: none; padding-left: 0;">
                    <li>👤 Guest Name: {guest.guest_fName} {guest.guest_lName}</li>
                    <li>📧 Email: {guest.guest_email}</li>
                    <li>📱 Phone: {guest.guest_phone}</li>
                </ul>
            </div>
    """

    if reservation_type in ['room', 'both'] and 'room' in reservation_details:
        room_details = reservation_details['room']
        body += f"""
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #2e7d32; margin-top: 0;">Room Reservation</h3>
                <ul style="list-style: none; padding-left: 0;">
                    <li>📅 Check-in: {format_date(room_details.get('start_date', 'N/A'))}</li>
                    <li>📅 Check-out: {format_date(room_details.get('end_date', 'N/A'))}</li>
                    <li>🏠 Rooms:</li>
        """
        for room in room_details.get('rooms', []):
            body += f'<li style="margin-left: 20px;">- {room.get("category", "").capitalize()}: {room.get("count", 0)} room(s)</li>'
        body += """
                </ul>
            </div>
        """

    if reservation_type in ['venue', 'both'] and 'venue' in reservation_details:
        venue_details = reservation_details['venue']
        body += f"""
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #e65100; margin-top: 0;">Venue Reservation</h3>
                <ul style="list-style: none; padding-left: 0;">
                    <li>📅 Start Date: {format_date(venue_details.get('start_date', 'N/A'))}</li>
                    <li>📅 End Date: {format_date(venue_details.get('end_date', 'N/A'))}</li>
                    <li>🏛 Venue: {venue_details.get('name', 'N/A')}</li>
                </ul>
            </div>
        """

    if guest.guest_type == 'external':
        body += """
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #e65100; margin-top: 0;">Payment Information</h3>
                <p>To secure your reservation, please pay the reservation fee of <strong>200 pesos</strong>.</p>
                <p>Payment can be made at our front desk during office hours.</p>
            </div>
        """

    body += """
            <p>If you have any questions or need to make changes to your reservation, please don't hesitate to contact us. We're here to ensure you have a comfortable and enjoyable stay.</p>
            <p style="margin-top: 30px;">
                Best regards,<br> 
                Lantaka Reservation Team
            </p>
        </div>
        <div style="background-color: #1a237e; color: white; padding: 20px; text-align: center; font-size: 12px;">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>© 2023 Lantaka Reservation System. All rights reserved.</p>
        </div>
    </div>
    """

    if is_online:
        try:
            msg = Message(subject=subject, recipients=[guest.guest_email])
            msg.html = body
            mail.send(msg)
            print(f"Confirmation email sent to {guest.guest_email}")
            return True, None
        except Exception as e:
            print(f"Failed to send confirmation email to {guest.guest_email}: {str(e)}")
            return False, str(e)
    else:
        try:
            pdf_path = generate_pdf_confirmation(guest, receipt_id, reservation_details, reservation_type)
            print(f"PDF confirmation generated: {pdf_path}")
            return True, pdf_path
        except Exception as e:
            print(f"Failed to generate PDF confirmation: {str(e)}")
            return False, str(e)

def generate_pdf_confirmation(guest, receipt_id, reservation_details, reservation_type):
    class PDF(FPDF):
        def header(self):
            self.image('DefaultAssets\header.png', 10, 8, 33)  # Add your logo
            self.set_font('Arial', 'B', 15)
            self.set_text_color(0, 51, 102)
            self.cell(0, 10, 'Lantaka Reservation System', 0, 0, 'R')
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Colors
    blue = (0, 51, 102)
    light_blue = (230, 240, 250)
    gray = (128, 128, 128)

    def add_section(title, content):
        pdf.set_draw_color(*blue)
        pdf.set_fill_color(*light_blue)
        pdf.set_text_color(*blue)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, title, 1, 1, 'L', 1)
        pdf.set_text_color(*gray)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, content, 'LR', 'L')
        pdf.cell(0, 1, '', 'LRB', 1, 'L')
        pdf.ln(5)

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*blue)
    pdf.cell(0, 10, "Reservation Confirmation", 0, 1, 'C')
    pdf.ln(5)

    # Guest Details
    guest_details = f"""
Name: {guest.guest_fName} {guest.guest_lName}
Email: {guest.guest_email}
Phone: {guest.guest_phone}
Receipt ID: {receipt_id}
    """
    add_section("Guest Details", guest_details.strip())

    # Room Reservation
    if reservation_type in ['room', 'both']:
        room_details = f"""
Check-in: {reservation_details['room']['start_date']}
Check-out: {reservation_details['room']['end_date']}

Rooms:
"""
        for room in reservation_details['room']['rooms']:
            room_details += f"- {room['category'].capitalize()}: {room['count']} room(s)\n"
        add_section("Room Reservation", room_details.strip())

    # Venue Reservation
    if reservation_type in ['venue', 'both']:
        venue_details = f"""
Start Date: {reservation_details['venue']['start_date']}
End Date: {reservation_details['venue']['end_date']}
Venue: {reservation_details['venue']['name']}
        """
        add_section("Venue Reservation", venue_details.strip())

    # Payment Information
    if guest.guest_type == 'external':
        payment_info = """
To secure your reservation, please pay the reservation fee of 200 pesos.
Payment can be made at our front desk during office hours.
        """
        add_section("Payment Information", payment_info.strip())

    # Terms and Conditions
    terms = """
1. Check-in time is 2:00 PM and check-out time is 12:00 PM.
2. Cancellations must be made at least 48 hours before the check-in date for a full refund.
3. Pets are not allowed in the premises.
4. Smoking is prohibited in all indoor areas.
5. The guest is liable for any damage to the property during their stay.
    """
    add_section("Terms and Conditions", terms.strip())

    pdf_dir = "offline_confirmations"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"confirmation_{receipt_id}.pdf")
    pdf.output(pdf_path)

    return pdf_path

