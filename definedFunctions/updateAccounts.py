from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from model import Account, db

# Initialize Flask app and other necessary components

def update_account():
    data = request.get_json()
    
    # Debugging: Log the raw incoming data
    print("Received data:", data)
    
    if not data:
        print("Error: No data received in request")
        return jsonify({'error': 'No data provided in request'}), 400

    account_id = data.get('id')
    
    if not account_id:
        print("Error: Missing 'id' in request data")
        return jsonify({'error': 'Account ID is required'}), 400

    print(f"Looking for account with ID: {account_id}")

    # Retrieve the account from the database
    account = Account.query.get(account_id)
    
    if not account:
        print(f"Error: Account with ID {account_id} not found")
        return jsonify({'error': 'Account not found'}), 404

    # Debugging: Print account details before updating
    print("Account details before update:", {
        'id': account.account_id,
        'first_name': account.account_fName,
        'last_name': account.account_lName,
        'email': account.account_email,
        'phone': account.account_phone,
        'dob': account.account_dob,
        'gender': account.account_gender,
    })

    # Update fields with provided data
    account.account_fName = data.get('first_name', account.account_fName)
    account.account_lName = data.get('last_name', account.account_lName)
    account.account_email = data.get('email', account.account_email)
    account.account_phone = data.get('phone', account.account_phone)

    # Check and update date of birth if provided
    dob = data.get('dob')
    if dob:
        try:
            account.account_dob = datetime.strptime(dob, '%Y-%m-%d').date()  # Convert to Date
            print(f"Updated DOB: {account.account_dob}")
        except ValueError as e:
            print(f"Error: Invalid date format for dob: {dob}")
            return jsonify({'error': f'Invalid date format for dob: {str(e)}'}), 400

    account.account_gender = data.get('gender', account.account_gender)
    
    # Debugging: Print updated account details
    print("Updated account details:", {
        'id': account.account_id,
        'first_name': account.account_fName,
        'last_name': account.account_lName,
        'email': account.account_email,
        'phone': account.account_phone,
        'dob': account.account_dob,
        'gender': account.account_gender,
    })

    # Attempt to commit changes to the database
    try:
        print("Committing changes to the database...")
        db.session.commit()
        
        # Debugging: Success message
        print(f"Account with ID {account.account_id} updated successfully.")

        # Respond with success and updated account details
        return jsonify({
            'message': 'Account updated successfully',
            'account': {
                'id': account.account_id,
                'first_name': account.account_fName,
                'last_name': account.account_lName,
                'email': account.account_email,
                'phone': account.account_phone,
                'dob': account.account_dob.strftime('%Y-%m-%d'),
                'gender': account.account_gender,
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error during commit: {str(e)}")  # Debugging error message
        return jsonify({'error': str(e)}), 500