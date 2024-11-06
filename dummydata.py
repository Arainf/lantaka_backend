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
