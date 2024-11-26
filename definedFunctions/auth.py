from flask import request, jsonify
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from model import db, Account
from schemas import account_schema
from datetime import datetime, time, date
import bcrypt


def register():
    try:
        # Validate the request form data
        data = account_schema.load(request.form)
        # Extract values after validation
        role = data['account_role']
        firstName = data['fName']
        lastName = data['lName']
        username = "LRS" + lastName.lower()
        email = data['email']
        password = data['password']
        phone = data['phone']
        dob = data['dob']
        gender = data['gender']
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Check if the account already exists
        existing_accounts = Account.query.filter_by(account_email=email).first()
        if existing_accounts:
            return jsonify({"message": "Email already exists"}), 400
        # Create a new account
        new_account = Account(
            account_role=role,
            account_fName=firstName,
            account_lName=lastName,
            account_username=username,
            account_email=email,
            account_password=hashed_password.decode('utf-8'),
            account_phone=phone,
            account_dob=dob,
            account_gender=gender,
            account_status="active",
            account_last_login=""
        )
        # Add and commit to the database
        db.session.add(new_account)
        db.session.commit()
        return jsonify({"message": "success"}), 201
    except ValidationError as err:
        # Return validation errors from Marshmallow
        return jsonify({"errors": err.messages}), 400

def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    # Find the user by username
    user = Account.query.filter_by(account_username=username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.account_password.encode('utf-8')):
        # Update last login time
        user.account_last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        # Return relevant user data
        return jsonify({
            "message": "Login successful",
            "account_id": user.account_id,
            "role": user.account_role,
            "first_name": user.account_fName,
            "last_name": user.account_lName,
            "email": user.account_email,
            "phone": user.account_phone,
            "dob": user.account_dob.strftime('%Y-%m-%d'),  # Format date
            "gender": user.account_gender,
            "status": user.account_status,
            "last_login": user.account_last_login
        }), 200 
    else:
        return jsonify({"message": "Invalid credentials"}), 401


