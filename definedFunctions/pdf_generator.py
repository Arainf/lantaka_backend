from fpdf import FPDF
import textwrap

class GuestFolioPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.logo_path = "DefaultAssets/header.png"

    def set_logo(self, path):
        self.logo_path = path

    def header(self):
        if self.logo_path:
            # Add logo to the left
            self.image(self.logo_path, 10, 8, 33)  # Adjust position and size as needed
        
        # Move to the right for the title
        self.set_xy(50, 10)
        self.set_font('Arial', 'B', 24)
        self.cell(0, 10, 'Lantaka Guest Folio', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def create_table(self, headers, data, col_widths):
        self.set_font('Arial', 'B', 10)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 10)
        for row in data:
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 10, str(cell), 1, 0, 'L')
            self.ln()

def generate_pdf(guest_data, logo_path):
    pdf = GuestFolioPDF()
    pdf.set_logo(logo_path)
    pdf.add_page()

    # Guest Details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Guest Details', 0, 1)
    pdf.set_font('Arial', '', 10)
    details = [
        f"Client: {guest_data['client_name']}",
        f"Guest Name: {guest_data['guest_name']}",
        f"Designation: {guest_data['guest_designation']}",
        f"Address: {guest_data['guest_address']}",
        f"Mode of Payment: {guest_data['payment_mode']}",
        f"Folio No.: {guest_data['folio_number']}",
        f"Status: {guest_data['folio_status']}",
        f"No. of Pax: {guest_data['number_of_pax']}",
        f"Check-In: {guest_data['check_in_date']}",
        f"Check-Out: {guest_data['check_out_date']}"
    ]
    for detail in details:
        pdf.cell(0, 7, detail, 0, 1)
    pdf.ln(10)

    # Room Charges
    for room in guest_data['rooms']:
        pdf.chapter_title(f"Room: {room['number']}")
        pdf.chapter_body(f"Account Title: Room Fee ({room['number']})")

        headers = ['Date', 'Ref. No.', 'Description', 'Base Charge', 'VAT', 'Disc.', 'Misc. Charges', 'LT', 'ST', 'Dr.', 'Cr.', 'Bal.']
        col_widths = [20, 20, 30, 25, 15, 15, 25, 15, 15, 15, 15, 20]
        data = [[charge[key] for key in ['date', 'reference_number', 'description', 'base_charge', 'vat', 'discount', 'misc_charges', 'lt', 'st', 'dr', 'cr', 'balance']] for charge in room['charges']]
        pdf.create_table(headers, data, col_widths)

        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, f"Ending Balance: {room['balance']}", 0, 1, 'R')
        pdf.ln(10)

    # Venue Charges
    for venue in guest_data['venues']:
        pdf.chapter_title(f"Venue: {venue['name']}")
        pdf.chapter_body("Account Title: Venue Fee")

        headers = ['Date', 'Ref. No.', 'Description', 'Base Charge', 'VAT', 'Disc.', 'Misc. Charges', 'LT', 'ST', 'Dr.', 'Cr.', 'Bal.']
        col_widths = [20, 20, 30, 25, 15, 15, 25, 15, 15, 15, 15, 20]
        data = [[charge[key] for key in ['date', 'reference_number', 'description', 'base_charge', 'vat', 'discount', 'misc_charges', 'lt', 'st', 'dr', 'cr', 'balance']] for charge in venue['charges']]
        pdf.create_table(headers, data, col_widths)

        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, f"Ending Balance: {venue['balance']}", 0, 1, 'R')
        pdf.ln(10)

    # Total Balance
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Total Balance: {guest_data['total_balance']}", 0, 1, 'R')

    return pdf