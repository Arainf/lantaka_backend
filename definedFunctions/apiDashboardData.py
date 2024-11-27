from flask import Blueprint, jsonify, request, make_response
from datetime import datetime, timedelta, date
from sqlalchemy import cast, Date, func, and_, or_, extract
from model import db, RoomReservation, VenueReservation, Room, RoomType, Receipt, GuestDetails, Venue
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from calendar import monthrange
import logging
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

def get_month_range(date_obj):
    """Get the first and last day of a month."""
    first_day = date_obj.replace(day=1)
    _, last_day = monthrange(date_obj.year, date_obj.month)
    return first_day, date_obj.replace(day=last_day)

def format_currency(amount):
    """Format amount as PHP currency."""
    return f"₱{amount:,.2f}"

def calculate_percentage_change(current, previous):
    """Calculate percentage change with proper handling of edge cases."""
    try:
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / abs(previous)) * 100
    except (TypeError, ZeroDivisionError):
        return 0

def get_date_range_filter(start_date, end_date, date_column):
    """Create a date range filter for SQLAlchemy queries."""
    return and_(
        cast(date_column, Date) >= start_date,
        cast(date_column, Date) <= end_date
    )

def get_available_spaces(start_date, end_date):
    """Calculate available spaces considering ready status only."""
    total_rooms = db.session.query(func.count(Room.room_id))\
        .filter(Room.room_status == 'ready')\
        .scalar() or 0
    
    total_venues = db.session.query(func.count(Venue.venue_id))\
        .filter(Venue.venue_status == 'ready')\
        .scalar() or 0
    
    occupied_rooms = db.session.query(func.count(RoomReservation.room_id))\
        .join(Room)\
        .filter(
            and_(
                Room.room_status == 'ready',
                get_date_range_filter(start_date, end_date, RoomReservation.room_reservation_booking_date_start),
                RoomReservation.room_reservation_status == 'done'
            )
        ).scalar() or 0
    
    occupied_venues = db.session.query(func.count(VenueReservation.venue_id))\
        .join(Venue)\
        .filter(
            and_(
                Venue.venue_status == 'ready',
                get_date_range_filter(start_date, end_date, VenueReservation.venue_reservation_booking_date_start),
                VenueReservation.venue_reservation_status == 'done'
            )
        ).scalar() or 0
    
    return (total_rooms - occupied_rooms) + (total_venues - occupied_venues)

def reset_date_range(start_date, end_date, view_mode):
    """Reset date range based on view mode."""
    if view_mode == 'monthly':
        start_date = start_date.replace(day=1)
        _, last_day = monthrange(end_date.year, end_date.month)
        end_date = end_date.replace(day=last_day)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
    return start_date, end_date

@dashboard_bp.route('/api/dashboardData', methods=['GET'])
def get_dashboard_data():
    try:
        end_date_str = request.args.get('endDate')
        start_date_str = request.args.get('startDate')
        view_mode = request.args.get('viewMode', 'monthly')
        export_format = request.args.get('export')

        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else (end_date - timedelta(days=6))
        except ValueError as e:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        if start_date > end_date:
            return jsonify({"error": "Start date cannot be after end date"}), 400

        start_date, end_date = reset_date_range(start_date, end_date, view_mode)

        logger.info(f"Processing request - Start Date: {start_date}, End Date: {end_date}, View Mode: {view_mode}")

        room_reservations = RoomReservation.query.join(Room).filter(
            and_(
                Room.room_status == 'ready',
                get_date_range_filter(start_date, end_date, RoomReservation.room_reservation_booking_date_start),
                RoomReservation.room_reservation_status == 'done'
            )
        ).all()

        venue_reservations = VenueReservation.query.join(Venue).filter(
            and_(
                Venue.venue_status == 'ready',
                get_date_range_filter(start_date, end_date, VenueReservation.venue_reservation_booking_date_start),
                VenueReservation.venue_reservation_status == 'done'
            )
        ).all()

        current_bookings = len(room_reservations) + len(venue_reservations)
        current_revenue = db.session.query(
            func.sum(Receipt.receipt_total_amount)
        ).filter(
            Receipt.receipt_id.in_([r.receipt_id for r in room_reservations] + [v.receipt_id for v in venue_reservations])
        ).scalar() or 0

        current_available_spaces = get_available_spaces(start_date, end_date)

        period_length = (end_date - start_date).days + 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_length - 1)

        prev_room_reservations = RoomReservation.query.join(Room).filter(
            and_(
                Room.room_status == 'ready',
                get_date_range_filter(prev_start_date, prev_end_date, RoomReservation.room_reservation_booking_date_start),
                RoomReservation.room_reservation_status == 'done'
            )
        ).all()

        prev_venue_reservations = VenueReservation.query.join(Venue).filter(
            and_(
                Venue.venue_status == 'ready',
                get_date_range_filter(prev_start_date, prev_end_date, VenueReservation.venue_reservation_booking_date_start),
                VenueReservation.venue_reservation_status == 'done'
            )
        ).all()

        prev_bookings = len(prev_room_reservations) + len(prev_venue_reservations)
        prev_revenue = db.session.query(
            func.sum(Receipt.receipt_total_amount)
        ).filter(
            Receipt.receipt_id.in_([r.receipt_id for r in prev_room_reservations] + [v.receipt_id for v in prev_venue_reservations])
        ).scalar() or 0

        prev_available_spaces = get_available_spaces(prev_start_date, prev_end_date)

        dates = []
        if view_mode == 'monthly':
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date)
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
        else:
            dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        occupancy_data = []
        revenue_data = []

        for current_date in dates:
            if view_mode == 'monthly':
                month_start, month_end = get_month_range(current_date)
                
                occupied_count = db.session.query(func.count(RoomReservation.room_id))\
                    .join(Room)\
                    .filter(
                        and_(
                            Room.room_status == 'ready',
                            cast(RoomReservation.room_reservation_booking_date_start, Date) <= month_end,
                            cast(RoomReservation.room_reservation_booking_date_end, Date) >= month_start,
                            RoomReservation.room_reservation_status == 'done'
                        )
                    ).scalar() or 0

                monthly_revenue = db.session.query(
                    func.sum(Receipt.receipt_total_amount)
                ).join(RoomReservation).filter(
                    and_(
                        cast(RoomReservation.room_reservation_booking_date_start, Date) >= month_start,
                        cast(RoomReservation.room_reservation_booking_date_start, Date) <= month_end,
                        RoomReservation.room_reservation_status == 'done'
                    )
                ).scalar() or 0

                monthly_revenue += db.session.query(
                    func.sum(Receipt.receipt_total_amount)
                ).join(VenueReservation).filter(
                    and_(
                        cast(VenueReservation.venue_reservation_booking_date_start, Date) >= month_start,
                        cast(VenueReservation.venue_reservation_booking_date_start, Date) <= month_end,
                        VenueReservation.venue_reservation_status == 'done'
                    )
                ).scalar() or 0

                formatted_date = current_date.strftime('%Y-%m')
                
                occupancy_data.append({
                    "date": formatted_date,
                    "occupancy": occupied_count
                })
                
                revenue_data.append({
                    "date": formatted_date,
                    "revenue": float(monthly_revenue)
                })
            else:
                occupied_count = db.session.query(func.count(RoomReservation.room_id))\
                    .join(Room)\
                    .filter(
                        and_(
                            Room.room_status == 'ready',
                            cast(RoomReservation.room_reservation_booking_date_start, Date) <= current_date,
                            cast(RoomReservation.room_reservation_booking_date_end, Date) >= current_date,
                            RoomReservation.room_reservation_status == 'done'
                        )
                    ).scalar() or 0

                daily_revenue = db.session.query(
                    func.sum(Receipt.receipt_total_amount)
                ).join(RoomReservation).filter(
                    and_(
                        cast(RoomReservation.room_reservation_booking_date_start, Date) == current_date,
                        RoomReservation.room_reservation_status == 'done'
                    )
                ).scalar() or 0

                daily_revenue += db.session.query(
                    func.sum(Receipt.receipt_total_amount)
                ).join(VenueReservation).filter(
                    and_(
                        cast(VenueReservation.venue_reservation_booking_date_start, Date) == current_date,
                        VenueReservation.venue_reservation_status == 'done'
                    )
                ).scalar() or 0

                formatted_date = current_date.strftime('%Y-%m-%d')
                
                occupancy_data.append({
                    "date": formatted_date,
                    "occupancy": occupied_count
                })
                
                revenue_data.append({
                    "date": formatted_date,
                    "revenue": float(daily_revenue)
                })

        room_type_performance = db.session.query(
            RoomType.room_type_name,
            func.count(RoomReservation.room_reservation_id).label('bookings'),
            func.avg(
                func.datediff(
                    RoomReservation.room_reservation_booking_date_end,
                    RoomReservation.room_reservation_booking_date_start
                )
            ).label('avg_duration')
        ).join(
            Room, Room.room_type_id == RoomType.room_type_id
        ).join(
            RoomReservation, Room.room_id == RoomReservation.room_id
        ).filter(
            and_(
                Room.room_status == 'ready',
                get_date_range_filter(start_date, end_date, RoomReservation.room_reservation_booking_date_start),
                RoomReservation.room_reservation_status == 'done'
            )
        ).group_by(RoomType.room_type_name).all()

        room_type_data = [
            {
                "roomType": row.room_type_name,
                "bookingFrequency": row.bookings,
                "avgStayDuration": float(row.avg_duration or 0)
            }
            for row in room_type_performance
        ]

        visitor_data = [
            {
                "name": "Room Guests",
                "visitors": len(room_reservations)
            },
            {
                "name": "Venue Visitors",
                "visitors": len(venue_reservations)
            }
        ]

        total_visitors = len(room_reservations) + len(venue_reservations)
        prev_total_visitors = len(prev_room_reservations) + len(prev_venue_reservations)
        visitor_trending = calculate_percentage_change(total_visitors, prev_total_visitors)

        total_guests = db.session.query(
            func.count(func.distinct(GuestDetails.guest_id))
        ).filter(
            or_(
                GuestDetails.guest_id.in_([r.guest_id for r in room_reservations]),
                GuestDetails.guest_id.in_([v.guest_id for v in venue_reservations])
            )
        ).scalar() or 0

        prev_total_guests = db.session.query(
            func.count(func.distinct(GuestDetails.guest_id))
        ).filter(
            or_(
                GuestDetails.guest_id.in_([r.guest_id for r in prev_room_reservations]),
                GuestDetails.guest_id.in_([v.guest_id for v in prev_venue_reservations])
            )
        ).scalar() or 0

        dashboard_data = {
            "totalBookings": current_bookings,
            "totalBookingsChange": round(calculate_percentage_change(current_bookings, prev_bookings), 1),
            "totalBookingsPeriod": "month" if view_mode == 'monthly' else "week",
            "totalRevenue": float(current_revenue),
            "totalRevenueChange": round(calculate_percentage_change(current_revenue, prev_revenue), 1),
            "totalRevenuePeriod": "month" if view_mode == 'monthly' else "week",
            "occupancyData": occupancy_data,
            "revenueData": revenue_data,
            "roomTypePerformance": room_type_data,
            "visitorData": visitor_data,
            "visitorTrending": round(visitor_trending, 1),
            "availableSpaces": current_available_spaces,
            "availableSpacesChange": round(calculate_percentage_change(current_available_spaces, prev_available_spaces), 1),
            "totalGuests": total_guests,
            "totalGuestsChange": round(calculate_percentage_change(total_guests, prev_total_guests), 1)
        }

        if export_format:
            if export_format == 'excel':
                return export_excel(dashboard_data, occupancy_data, revenue_data, room_type_data, visitor_data)
            elif export_format == 'pdf':
                return export_pdf(dashboard_data)
            else:
                return jsonify({"error": "Unsupported export format"}), 400

        return jsonify(dashboard_data)

    except Exception as e:
        logger.error(f"Error in get_dashboard_data: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

def export_excel(dashboard_data, occupancy_data, revenue_data, room_type_data, visitor_data):
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book

            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4B5563',
                'font_color': 'white',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'border': 1
            })

            summary_df = pd.DataFrame({
                'Metric': [
                    'Total Bookings',
                    'Total Revenue',
                    'Available Spaces',
                    'Total Guests',
                    'Visitor Trend'
                ],
                'Current Value': [
                    dashboard_data['totalBookings'],
                    format_currency(dashboard_data['totalRevenue']),
                    dashboard_data['availableSpaces'],
                    dashboard_data['totalGuests'],
                    f"{dashboard_data['visitorTrending']}%"
                ],
                'Change': [
                    f"{dashboard_data['totalBookingsChange']}%",
                    f"{dashboard_data['totalRevenueChange']}%",
                    f"{dashboard_data['availableSpacesChange']}%",
                    f"{dashboard_data['totalGuestsChange']}%",
                    "N/A"
                ]
            })
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            summary_sheet = writer.sheets['Summary']
            for col_num, value in enumerate(summary_df.columns.values):
                summary_sheet.write(0, col_num, value, header_format)

            occupancy_df = pd.DataFrame(occupancy_data)
            occupancy_df.to_excel(writer, sheet_name='Occupancy', index=False)
            
            revenue_df = pd.DataFrame(revenue_data)
            revenue_df['revenue'] = revenue_df['revenue'].apply(lambda x: format_currency(x))
            revenue_df.to_excel(writer, sheet_name='Revenue', index=False)

            room_perf_df = pd.DataFrame(room_type_data)
            room_perf_df.columns = ['Room Type', 'Booking Frequency', 'Average Stay Duration (Days)']
            room_perf_df.to_excel(writer, sheet_name='Room Performance', index=False)

            visitors_df = pd.DataFrame(visitor_data)
            visitors_df.to_excel(writer, sheet_name='Visitors', index=False)

            for sheet in writer.sheets.values():
                sheet.autofit()

        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=dashboard-report-{datetime.now().strftime("%Y-%m-%d")}.xlsx'
        return response

    except Exception as e:
        logger.error(f"Error in export_excel: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to generate Excel report"}), 500

def export_pdf(dashboard_data):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a365d'),
            alignment=1  # Center alignment
        )
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2c5282')
        )
        subheader_style = ParagraphStyle(
            'CustomSubHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#4a5568')
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=12,
            textColor=colors.HexColor('#4a5568')
        )

        elements.append(Paragraph("Hotel Performance Dashboard Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subheader_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Executive Summary", header_style))
        summary_text = f"""
        This report provides a comprehensive analysis of the hotel's performance metrics. 
        The data shows that the hotel has achieved a total revenue of {format_currency(dashboard_data['totalRevenue'])}, 
        representing a {dashboard_data['totalRevenueChange']}% change from the previous period. 
        The total number of bookings stands at {dashboard_data['totalBookings']}, with a 
        {dashboard_data['totalBookingsChange']}% change in booking volume.
        """
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Key Performance Metrics", header_style))
        metrics_text = f"""
        The following metrics highlight the hotel's current performance status:
        • Total Revenue: {format_currency(dashboard_data['totalRevenue'])} ({dashboard_data['totalRevenueChange']}% change)
        • Total Bookings: {dashboard_data['totalBookings']} ({dashboard_data['totalBookingsChange']}% change)
        • Available Spaces: {dashboard_data['availableSpaces']} ({dashboard_data['availableSpacesChange']}% change)
        • Total Guests: {dashboard_data['totalGuests']} ({dashboard_data['totalGuestsChange']}% change)
        """
        elements.append(Paragraph(metrics_text, body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Detailed Performance Analysis", header_style))
        summary_data = [
            ['Metric', 'Current Value', 'Change'],
            ['Total Bookings', str(dashboard_data['totalBookings']), f"{dashboard_data['totalBookingsChange']}%"],
            ['Total Revenue', format_currency(dashboard_data['totalRevenue']), f"{dashboard_data['totalRevenueChange']}%"],
            ['Available Spaces', str(dashboard_data['availableSpaces']), f"{dashboard_data['availableSpacesChange']}%"],
            ['Total Guests', str(dashboard_data['totalGuests']), f"{dashboard_data['totalGuestsChange']}%"]
        ]

        summary_table = Table(summary_data, colWidths=[200, 150, 100])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("Visitor Distribution Analysis", header_style))
        
        plt.figure(figsize=(6, 6))
        plt.clf()
        room_visitors = next(item['visitors'] for item in dashboard_data['visitorData'] if item['name'] == 'Room Guests')
        venue_visitors = next(item['visitors'] for item in dashboard_data['visitorData'] if item['name'] == 'Venue Visitors')
        
        plt.pie([room_visitors, venue_visitors], 
                labels=['Room Guests', 'Venue Visitors'],
                colors=['#60A5FA', '#3B82F6'],
                autopct='%1.1f%%',
                startangle=90)
        plt.title('Visitor Distribution (Room vs Venue)')
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        
        visitor_chart = Image(img_buffer, width=4*inch, height=4*inch)
        elements.append(visitor_chart)
        
        visitor_analysis = f"""
        The visitor distribution shows that {room_visitors/(room_visitors + venue_visitors)*100:.1f}% of our guests 
        are room guests, while {venue_visitors/(room_visitors + venue_visitors)*100:.1f}% are venue visitors. 
        The total visitor trend is showing a {dashboard_data['visitorTrending']}% change compared to the previous period.
        """
        elements.append(Paragraph(visitor_analysis, body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Room Type Performance", header_style))
        
        plt.figure(figsize=(8, 4))
        plt.clf()
        
        room_types = [data['roomType'] for data in dashboard_data['roomTypePerformance']]
        bookings = [data['bookingFrequency'] for data in dashboard_data['roomTypePerformance']]
        avg_duration = [data['avgStayDuration'] for data in dashboard_data['roomTypePerformance']]
        
        x = range(len(room_types))
        width = 0.35
        
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax2 = ax1.twinx()
        
        bars1 = ax1.bar([i - width/2 for i in x], bookings, width, label='Bookings', color='#60A5FA')
        bars2 = ax2.bar([i + width/2 for i in x], avg_duration, width, label='Avg Duration', color='#3B82F6')
        
        ax1.set_ylabel('Booking Frequency')
        ax2.set_ylabel('Average Stay Duration (Days)')
        plt.title('Room Type Performance')
        ax1.set_xticks(x)
        ax1.set_xticklabels(room_types, rotation=45)
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        
        room_type_chart = Image(img_buffer, width=6*inch, height=3*inch)
        elements.append(room_type_chart)
        
        room_type_analysis = """
        The room type performance analysis reveals the booking patterns and average stay duration for different room types. 
        This data helps in understanding customer preferences and optimizing room allocation strategies.
        """
        elements.append(Paragraph(room_type_analysis, body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Occupancy Trend Analysis", header_style))
        
        plt.figure(figsize=(8, 4))
        plt.clf()
        
        dates = [data['date'] for data in dashboard_data['occupancyData']]
        occupancy = [data['occupancy'] for data in dashboard_data['occupancyData']]
        
        plt.plot(dates, occupancy, marker='o', color='#3B82F6', linewidth=2)
        plt.title('Occupancy Trend')
        plt.xlabel('Date')
        plt.ylabel('Occupancy Count')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        
        occupancy_chart = Image(img_buffer, width=6*inch, height=3*inch)
        elements.append(occupancy_chart)
        
        occupancy_analysis = """
        The occupancy trend shows the pattern of room utilization over time. This helps in identifying peak periods 
        and seasonal trends, enabling better resource allocation and pricing strategies.
        """
        elements.append(Paragraph(occupancy_analysis, body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Revenue Analysis", header_style))
        
        plt.figure(figsize=(8, 4))
        plt.clf()
        
        dates = [data['date'] for data in dashboard_data['revenueData']]
        revenue = [data['revenue'] for data in dashboard_data['revenueData']]
        
        plt.fill_between(dates, revenue, color='#60A5FA', alpha=0.3)
        plt.plot(dates, revenue, color='#3B82F6', linewidth=2)
        plt.title('Revenue Trend')
        plt.xlabel('Date')
        plt.ylabel('Revenue (PHP)')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)

        max_revenue = max(revenue) if revenue else 30000  # Use 30000 as default max if no data
        plt.ylim(0, max_revenue * 1.2)  # Add 20% padding to the top
        ax = plt.gca()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
        ax.yaxis.set_major_locator(plt.MaxNLocator(5))  # Show 5 ticks on y-axis

        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        
        revenue_chart = Image(img_buffer, width=6*inch, height=3*inch)
        elements.append(revenue_chart)
        
        revenue_analysis = f"""
        The revenue analysis shows a total revenue of {format_currency(dashboard_data['totalRevenue'])} for the period, 
        with a {dashboard_data['totalRevenueChange']}% change from the previous period. The trend line indicates 
        the revenue pattern over time, helping identify growth periods and areas for improvement.
        """
        elements.append(Paragraph(revenue_analysis, body_style))

        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Conclusion", header_style))
        conclusion_text = f"""
        This comprehensive analysis demonstrates the hotel's performance across various metrics. 
        With a total of {dashboard_data['totalBookings']} bookings and {dashboard_data['totalGuests']} guests, 
        the hotel has maintained a strong market presence. The {dashboard_data['totalRevenueChange']}% change in revenue 
        indicates {['a declining', 'a stable', 'a growing'][1 if abs(dashboard_data['totalRevenueChange']) < 5 else 2 if dashboard_data['totalRevenueChange'] > 0 else 0]} 
        business trajectory. Future strategies should focus on maintaining these performance levels while identifying 
        opportunities for growth and optimization.
        """
        elements.append(Paragraph(conclusion_text, body_style))

        doc.build(elements)
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=dashboard-report-{datetime.now().strftime("%Y-%m-%d")}.pdf'
        return response

    except Exception as e:
        logger.error(f"Error in export_pdf: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to generate PDF report"}), 500

