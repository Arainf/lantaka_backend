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


def get_additional_fees():
    try:
        fees = AdditionalFees.query.all()
        return jsonify([fee.to_dict() for fee in fees]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def add_fee():
    try:
        data = request.get_json()
        fee_name = data.get('additional_fee_name')
        fee_amount = data.get('additional_fee_amount')

        if not fee_name or fee_amount is None:
            return jsonify({"error": "Missing required fields"}), 400

        new_fee = AdditionalFees(additional_fee_name=fee_name, additional_fee_amount=fee_amount)
        db.session.add(new_fee)
        db.session.commit()
        return jsonify({"message": "Fee added successfully", "fee": new_fee.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_fee(id):
    try:
        fee = AdditionalFees.query.get(id)
        if not fee:
            return jsonify({"error": "Fee not found"}), 404

        if request.content_type == 'application/json':
            data = request.get_json()
            fee.additional_fee_name = data.get('additional_fee_name', fee.additional_fee_name)
            fee.additional_fee_amount = data.get('additional_fee_amount', fee.additional_fee_amount)
        else:
            return jsonify({"error": "Unsupported content type"}), 400

        db.session.commit()
        return jsonify({"message": "Fee updated successfully", "fee": fee.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def delete_fee(id):
    try:
        fee = AdditionalFees.query.get(id)
        if not fee:
            return jsonify({"error": "Fee not found"}), 404

        db.session.delete(fee)
        db.session.commit()
        return jsonify({"message": "Fee deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
       
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
