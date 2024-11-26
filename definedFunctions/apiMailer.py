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
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")

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
            {'<div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">' +
             '<h3 style="color: #2e7d32; margin-top: 0;">Room Reservation</h3>' +
             '<ul style="list-style: none; padding-left: 0;">' +
             f'<li>📅 Check-in: {format_date(reservation_details["room"]["start_date"])}</li>' +
             f'<li>📅 Check-out: {format_date(reservation_details["room"]["end_date"])}</li>' +
             '<li>🏠 Rooms:</li>' +
             ''.join([f'<li style="margin-left: 20px;">- {room["category"].capitalize()}: {room["count"]} room(s)</li>' for room in reservation_details["room"]["rooms"]]) +
             '</ul>' +
             '</div>' if reservation_type in ['room', 'both'] else ''}
            {'<div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">' +
             '<h3 style="color: #e65100; margin-top: 0;">Venue Reservation</h3>' +
             '<ul style="list-style: none; padding-left: 0;">' +
             f'<li>📅 Start Date: {format_date(reservation_details["venue"]["start_date"])}</li>' +
             f'<li>📅 End Date: {format_date(reservation_details["venue"]["end_date"])}</li>' +
             f'<li>🏛 Venue: {reservation_details["venue"]["name"]}</li>' +
             '</ul>' +
             '</div>' if reservation_type in ['venue', 'both'] else ''}
            {'<div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">' + 
             '<h3 style="color: #e65100; margin-top: 0;">Payment Information</h3>' +
             '<p>To secure your reservation, please pay the reservation fee of <strong>200 pesos</strong>.</p>' +
             '<p>Payment can be made at our front desk during office hours.</p>' +
             '</div>' if guest.guest_type == 'external' else ''}
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
            self.set_font('Arial', 'B', 20)
            self.cell(0, 10, 'Lantaka Reservation System', 0, 1, 'C')
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_draw_color(0, 51, 102)
    pdf.set_fill_color(230, 230, 250)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Reservation Confirmation", 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Guest Details", 1, 1, 'L', 1)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"""
Name: {guest.guest_fName} {guest.guest_lName}
Email: {guest.guest_email}
Phone: {guest.guest_phone}
Receipt ID: {receipt_id}
    """, 1, 'L')
    pdf.ln(5)

    if reservation_type in ['room', 'both']:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Room Reservation", 1, 1, 'L', 1)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, f"""
Check-in: {reservation_details['room']['start_date']}
Check-out: {reservation_details['room']['end_date']}
        """, 1, 'L')
        pdf.cell(0, 8, "Rooms:", 1, 1, 'L')
        for room in reservation_details['room']['rooms']:
            pdf.cell(0, 8, f"- {room['category'].capitalize()}: {room['count']} room(s)", 1, 1, 'L')
        pdf.ln(5)

    if reservation_type in ['venue', 'both']:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Venue Reservation", 1, 1, 'L', 1)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, f"""
Start Date: {reservation_details['venue']['start_date']}
End Date: {reservation_details['venue']['end_date']}
Venue: {reservation_details['venue']['name']}
        """, 1, 'L')
        pdf.ln(5)

    if guest.guest_type == 'external':
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Payment Information", 1, 1, 'L', 1)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, """
To secure your reservation, please pay the reservation fee of 200 pesos.
Payment can be made at our front desk during office hours.
        """, 1, 'L')
        pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Terms and Conditions", 1, 1, 'L', 1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, """
1. Check-in time is 2:00 PM and check-out time is 12:00 PM.
2. Cancellations must be made at least 48 hours before the check-in date for a full refund.
3. Pets are not allowed in the premises.
4. Smoking is prohibited in all indoor areas.
5. The guest is liable for any damage to the property during their stay.
    """, 1, 'L')

    pdf_dir = "offline_confirmations"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"confirmation_{receipt_id}.pdf")
    pdf.output(pdf_path)

    return pdf_path

