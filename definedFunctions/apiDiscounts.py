from flask import jsonify, request
from model import Discounts, db  # Make sure to import db for session handling
from sqlalchemy.exc import SQLAlchemyError

def get_discounts():
    discounts = Discounts.query.all()

    if discounts:
        discountsHolder = []
        for discount in discounts:
            discount_data = {
                "discount_id": discount.discount_id,
                "discount_name": discount.discount_name,
                "discount_percentage": discount.discount_percentage,
            }
            discountsHolder.append(discount_data)

        return jsonify(discountsHolder), 200
    else:
        return jsonify({"error": "No discounts found"}), 404
    
def insert_discounts():
    try:
        data = request.json
        discount_name = data.get("discount_name")
        discount_percentage = data.get("discount_percentage")

        # Validate if required fields are present
        if not discount_name or not discount_percentage:
            return jsonify({"error": "Missing required fields: 'discount_name' or 'discount_percentage'"}), 400
        
        # Add additional validation for percentage (e.g., ensuring it is a number between 0-100)
        try:
            discount_percentage = float(discount_percentage)
            if not (0 <= discount_percentage <= 100):
                return jsonify({"error": "Invalid discount percentage. It should be between 0 and 100."}), 400
        except ValueError:
            return jsonify({"error": "Invalid discount percentage. It should be a numeric value."}), 400
        
        # Create new discount record
        discount = Discounts(discount_name=discount_name,
                             discount_percentage=discount_percentage)
        
        try:
            db.session.add(discount)
            db.session.commit()
            return jsonify({"message": "Discount added successfully"}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
