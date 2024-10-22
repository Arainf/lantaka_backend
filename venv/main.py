import base64
import bcrypt
from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, ValidationError
from flask_marshmallow import Marshmallow  # Correct import
from werkzeug.utils import secure_filename  # For secure image uploads
from flask_cors import CORS
from model import db, Account 
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration for MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/lantaka_accounts'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow
db.init_app(app)  # Initialize with app
ma = Marshmallow(app)  # Correct initialization

# Marshmallow schema for validation
class AccountSchema(Schema):
    account_role = fields.Str(required=True, validate=validate.OneOf(["Administrator", "Employee"]))
    fName = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    lName = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    phone = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    dob = fields.Date(required=True)
    gender = fields.Str(validate=validate.OneOf(["male", "female"]))
    profileImageFile = fields.Raw(required=False)

# Initialize schema objects
account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)

# Simple route to test the API
@app.route('/', methods=['GET'])
def get_account():
    return jsonify("Hello World")

# Route for account registration
@app.route('/register', methods=['POST'])
def register():
    try:
        # Validate the request form data
        data = account_schema.load(request.form)

        # Extract values after validation
        role = data['account_role']
        firstName = data['fName']
        lastName = data['lName']
        username = firstName.lower() + lastName.lower()
        email = data['email']
        password = data['password']
        phone = data['phone']
        dob = data['dob']
        gender = data['gender']

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Handle profile image upload securely
        image_file = request.files.get('profileImageFile')
        account_img = None
        if image_file:
            filename = secure_filename(image_file.filename)
            if filename.endswith(('png', 'jpg', 'jpeg')):
                account_img = image_file.read()
            else:
                return jsonify({"message": "Invalid image format"}), 400

        # Check if the account already exists
        existing_accounts = Account.query.filter_by(account_email=email).first()
        if existing_accounts:
            return jsonify({"message": "Email already exists"}), 400

        # Create a new account
        new_account = Account(
            account_role=role,
            account_fName=firstName,
            account_lName=lastName,
            account_img=account_img,
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


@app.route('/login', methods=['POST'])
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

        if user.account_img:
            image_blob = base64.b64encode(user.account_img).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_blob}"  # Assuming it's a JPEG, adjust if needed
        else:
            image_url = None  # Or a default image

        
        # Return relevant user data
        return jsonify({
            "message": "Login successful",
            "account_id": user.account_id,
            "imageUrl": image_url,
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


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    users = Account.query.all()
    if users:
        accounts = []
        for user in users:
            # Convert the blob (user.account_img) to a base64 string
            if user.account_img:
                image_blob = base64.b64encode(user.account_img).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{image_blob}"  # Assuming it's a JPEG, adjust if needed
            else:
                image_url = None  # Or a default image

            account_data = {
                "id": user.account_id,
                "email": user.account_email,
                "firstName": user.account_fName,
                "lastName": user.account_lName,
                "username": user.account_username,
                "imageUrl": image_url,  # Send the base64 string to the frontend
                "role": user.account_role,  # Include role in profile data
                "PhoneNumber": user.account_phone,
                "dob": user.account_dob.strftime('%Y-%m-%d'),  # Format date
                "gender": user.account_gender,
                "status": user.account_status,
                "created_at": user.account_created_at.strftime('%Y-%m-%d'), # Format
                "updated_at": user.account_updated_at.strftime('%Y-%m-%d'),
            }
            accounts.append(account_data)

        return jsonify(accounts), 200
    else:
        return jsonify({"error": "No accounts found"}), 404

# @app.route('/CustomerData', methods=['POST'])
# def customer_data():
#     data = request.get_json()
#     customer_id = data['customer_id']

# Ensure the application context is active before creating tables
if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()  # Creates the tables in the database
    app.run(host='0.0.0.0', debug=True, port=5000)
