from flask import jsonify, request
from model import AdditionalFees, db  # Make sure to import `db` for session handling
from sqlalchemy.exc import SQLAlchemyError

def get_AdditionalFees():
    addfees = AdditionalFees.query.all()

    if addfees:
        addfeesHolder = []
        for addfee in addfees:
            addfee_data = {
                "additional_fee_id": addfee.additional_fee_id,
                "additional_fee_name": addfee.additional_fee_name,
                "additional_fee_amount": addfee.additional_fee_amount,
            }
            addfeesHolder.append(addfee_data)

        return jsonify(addfeesHolder), 200
    else:
        return jsonify({"error": "No additional fees found"}), 404
    
def insert_AdditionalFees():
    try:
        data = request.json
        addfee_name = data.get("additional_fee_name")
        addfee_amount = data.get("additional_fee_amount")

        if not addfee_name or not addfee_amount:
            return jsonify({"error": "Missing required fields: 'additional_fee_name' or 'additional_fee_amount'"}), 400
        
        # Add additional validation logic if needed (e.g., check if the amount is numeric)
        addfee = AdditionalFees(additional_fee_name=addfee_name, additional_fee_amount=addfee_amount)
        
        try:
            db.session.add(addfee)
            db.session.commit()
            return jsonify({"message": "Additional fee added successfully"}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
