from datetime import datetime, time, date
from model import VenueReservation, Account, GuestDetails, RoomReservation

# Dummy Accounts
accounts = [
    Account(
        account_id = 1,
        account_role="Administrator",
        account_fName="John",
        account_lName="Doe",
        account_img=None,  # Assuming binary data will be added later
        account_username="johndoe",
        account_email="johndoe@example.com",
        account_password="hashed_password_1",  # Hash passwords in production
        account_phone="09123456789",
        account_dob=date(1990, 1, 1),
        account_gender="male",
        account_status="active",
        account_last_login=datetime(2024, 10, 1, 10, 0)  # Use datetime for consistency
    ),
    Account(
        account_id = 2,
        account_role="Employee",
        account_fName="Jane",
        account_lName="Smith",
        account_img=None,  # Assuming binary data will be added later
        account_username="janesmith",
        account_email="janesmith@example.com",
        account_password="hashed_password_2",  # Hash passwords in production
        account_phone="09876543210",
        account_dob=date(1995, 5, 15),
        account_gender="female",
        account_status="active",
        account_last_login=datetime(2024, 10, 10, 14, 30)  # Use datetime for consistency
    ),
    Account(
        account_id = 3,
        account_role="Employee",
        account_fName="Mike",
        account_lName="Johnson",
        account_img=None,  # Assuming binary data will be added later
        account_username="mikejohnson",
        account_email="mikejohnson@example.com",
        account_password="hashed_password_3",  # Hash passwords in production
        account_phone="09112233445",
        account_dob=date(1988, 8, 20),
        account_gender="male",
        account_status="inactive",
        account_last_login=datetime(2024, 9, 25, 9, 15)  # Use datetime for consistency
    )
]

# Dummy Guest Details
guests = [
    GuestDetails(
        guest_id=1,
        guest_fName="Emily",
        guest_lName="Williams",
        guest_pop=None,  # Assuming binary data for profile picture will be added later
        guest_email="emilywilliams@example.com",
        guest_phone="09123456789",
        guest_gender="female",
        guest_messenger_account="emily.williams.messenger",
        guest_poi=None,  # Assuming binary data for proof of identity will be added later
        guest_designation="Event Planner",
        guest_address="123 Main St, Zamboanga",
        guest_client="ABC Corp"
    ),
    GuestDetails(
        guest_id=2,
        guest_fName="Chris",
        guest_lName="Brown",
        guest_pop=None,  # Assuming binary data for profile picture will be added later
        guest_email="chrisbrown@example.com",
        guest_phone="09876543210",
        guest_gender="male",
        guest_messenger_account="chris.brown.messenger",
        guest_poi=None,  # Assuming binary data for proof of identity will be added later
        guest_designation="Manager",
        guest_address="456 Park Ave, Zamboanga",
        guest_client="XYZ Ltd"
    ),
    GuestDetails(
        guest_id=3,
        guest_fName="Sophia",
        guest_lName="Davis",
        guest_pop=None,  # Assuming binary data for profile picture will be added later
        guest_email="sophiadavis@example.com",
        guest_phone="09112233445",
        guest_gender="female",
        guest_messenger_account="sophia.davis.messenger",
        guest_poi=None,  # Assuming binary data for proof of identity will be added later
        guest_designation="Consultant",
        guest_address="789 Elm St, Zamboanga",
        guest_client="LMN Inc"
    )
]

# Dummy Venue Reservations with the same booking date
# Dummy reservations with the same booking date
venue_reservations = [
    VenueReservation(
        venue_reservation_id=1,
        venue_id="DiningHall", 
        guest_id=1, 
        account_id=1, 
        venue_reservation_booking_date_start=datetime(2024, 10, 25),
        venue_reservation_booking_date_end=datetime(2024,10,26),  # Ensure this matches your class definition
        venue_reservation_check_in_time=time(9, 0), 
        venue_reservation_check_out_time=time(12, 0), 
        venue_reservation_status="pending"
    ),
    VenueReservation(
        venue_reservation_id=2,
        venue_id="Gazebo", 
        guest_id=1, 
        account_id=1, 
        venue_reservation_booking_date_start=datetime(2024, 10, 25), 
        venue_reservation_booking_date_end=datetime(2024,10,26), 
        venue_reservation_check_in_time=time(10, 0), 
        venue_reservation_check_out_time=time(14, 0), 
        venue_reservation_status="completed"
    ),
    VenueReservation(
        venue_reservation_id=3,
        venue_id="BreezaHall", 
        guest_id=1, 
        account_id=1, 
        venue_reservation_booking_date_start=datetime(2024, 10, 25),  
        venue_reservation_booking_date_end=datetime(2024,10,26),
        venue_reservation_check_in_time=time(11, 0), 
        venue_reservation_check_out_time=time(15, 0), 
        venue_reservation_status="cancelled"
    ),
    VenueReservation(
        venue_reservation_id=4,
        venue_id="CapizHall", 
        guest_id=1, 
        account_id=1, 
        venue_reservation_booking_date_start=datetime(2024, 10, 25), 
        venue_reservation_booking_date_end=datetime(2024,10,26), 
        venue_reservation_check_in_time=time(12, 0), 
        venue_reservation_check_out_time=time(16, 0), 
        venue_reservation_status="pending"
    ),
    VenueReservation(
        venue_reservation_id=5,
        venue_id="OldTalisayBar", 
        guest_id=1, 
        account_id=1, 
        venue_reservation_booking_date_start=datetime(2024, 10, 25),
        venue_reservation_booking_date_end=datetime(2024,10,26), 
        venue_reservation_check_in_time=time(13, 0), 
        venue_reservation_check_out_time=time(17, 0), 
        venue_reservation_status="completed"
    )
]

room_reservations = [
    RoomReservation(
        room_reservation_id=1,
        room_id="Room102",
        guest_id=1,
        account_id=1,
        room_reservation_booking_date_start=datetime(2024, 10, 25),
        room_reservation_booking_date_end=datetime(2024, 10, 26),
        room_reservation_check_in_time=time(10, 0),
        room_reservation_check_out_time=time(12, 0),
        room_reservation_status="pending"
    ),
    RoomReservation(
        room_reservation_id=2,
        room_id="Room104",
        guest_id=1,
        account_id=1,
        room_reservation_booking_date_start=datetime(2024, 10, 25),
        room_reservation_booking_date_end=datetime(2024, 10, 26),
        room_reservation_check_in_time=time(10, 0),
        room_reservation_check_out_time=time(12, 0),
        room_reservation_status="pending"
    ),
    RoomReservation(
        room_reservation_id=3,
        room_id="Room106",
        guest_id=1,
        account_id=1,
        room_reservation_booking_date_start=datetime(2024, 10, 25),
        room_reservation_booking_date_end=datetime(2024, 10, 26),
        room_reservation_check_in_time=time(10, 0),
        room_reservation_check_out_time=time(12, 0),
        room_reservation_status="pending"
    ),
    RoomReservation(
        room_reservation_id=4,
        room_id="Room108",
        guest_id=1,
        account_id=1,
        room_reservation_booking_date_start=datetime(2024, 10, 25),
        room_reservation_booking_date_end=datetime(2024, 10, 26),
        room_reservation_check_in_time=time(10, 0),
        room_reservation_check_out_time=time(12, 0),
        room_reservation_status="pending"
    )
]

