from flask import jsonify
from model import Account  

# Define the get_accounts route in a separate file
def get_accounts():
    users = Account.query.all()
    if users:
        accounts = []
        for user in users:
            account_data = {
                "account_id": user.account_id,
                "account_email": user.account_email,
                "account_fName": user.account_fName,
                "account_lName": user.account_lName,
                "account_username": user.account_username,
                "account_role": user.account_role,  # Include role in profile data
                "account_phone": user.account_phone,
                "account_dob": user.account_dob.strftime('%Y-%m-%d'),  # Format date
                "account_gender": user.account_gender,
                "account_status": user.account_status,
                "account_created_at": user.account_created_at.strftime('%Y-%m-%d'), # Format
                "account_updated_at": user.account_updated_at.strftime('%Y-%m-%d'),
                "account_last_login": user.account_last_login
            }
            accounts.append(account_data)

        return jsonify(accounts), 200
    else:
        return jsonify({"error": "No accounts found"}), 404
