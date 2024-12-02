from flask import jsonify, request
from model import AdditionalFees, db , GuestDetails, Account , AdditionalFees, Receipt# Make sure to import `db` for session handling
from sqlalchemy.exc import SQLAlchemyError
import logging

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
    
def delete_fee():
    try:
        # Parse incoming request data
        data = request.json
        logging.debug(f"Request data: {data}")

        # Extract required fields from the request
        receipt_id = data.get("receiptID")
        fee_id = data.get("feeId")

        # Validate the input
        if not receipt_id or not fee_id:
            logging.warning(f"Missing required fields: 'receiptID' or 'feeId'")
            return jsonify({"error": "Missing required fields: 'receiptID' or 'feeId'"}), 400

        # Retrieve the fee by ID
        fee = AdditionalFees.query.get(fee_id)
        if not fee:
            logging.warning(f"Fee not found for ID: {fee_id}")
            return jsonify({"error": "Fee not found"}), 404

        # Ensure the fee is associated with the correct receipt
        receipt = Receipt.query.get(receipt_id)
        if not receipt or fee not in receipt.additional_fees:
            logging.warning(f"Fee with ID {fee_id} is not associated with receipt ID: {receipt_id}")
            return jsonify({"error": "Fee not associated with the specified receipt"}), 400

        logging.debug(f"Fee found: {fee} | Associated receipt: {receipt}")

        # Attempt to delete the fee
        try:
            db.session.delete(fee)
            db.session.flush()  # Ensure deletion is staged before committing
            logging.debug(f"Fee with ID {fee_id} staged for deletion")

            # Update the receipt's total amount
            old_total = receipt.receipt_total_amount
            receipt.receipt_total_amount = old_total - fee.additional_fee_amount
            logging.debug(f"Updated receipt total amount: {old_total} -> {receipt.receipt_total_amount}")

            # Commit the transaction
            db.session.commit()
            logging.info(f"Successfully deleted fee with ID: {fee_id} and updated receipt total.")
            return jsonify({"message": "Fee deleted successfully"}), 200

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error during fee deletion: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400



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
    

    

def delete_guests(id):
    try:
        guest = GuestDetails.query.get(id)
        if not guest:
            return jsonify({"error": "Guest not found"}), 404
        
        db.session.delete(guest)
        db.session.commit()
        return jsonify({"message": "Guest deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def delete_account(id):
    try:
        account = Account.query.get(id)
        if not account:
            return jsonify({"error": "Account not found"}), 404
        
        db.session.delete(account)
        db.session.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
       
def insert_AdditionalFees():
    try:
        # Get data from the request
        data = request.json
        logging.debug(f"Request data: {data}")

        # Retrieve the necessary fields
        receipt_id = data.get("receiptID")
        addfee_name = data.get("name")
        addfee_amount = data.get("amount")

        # Validate input fields
        if not receipt_id or not addfee_name or not addfee_amount:
            logging.warning(f"Missing required fields: 'receipt_id', 'additional_fee_name', or 'additional_fee_amount'")
            return jsonify({"error": "Missing required fields: 'receipt_id', 'additional_fee_name', or 'additional_fee_amount'"}), 400

        # Check if receipt exists
        receipt = Receipt.query.get(receipt_id)
        if not receipt:
            logging.warning(f"Receipt not found for ID: {receipt_id}")
            return jsonify({"error": "Receipt not found"}), 404
        logging.debug(f"Found receipt: {receipt}")

        # Add the additional fee
        addfee = AdditionalFees(additional_fee_name=addfee_name, additional_fee_amount=addfee_amount)
        logging.debug(f"Creating additional fee: {addfee_name} - {addfee_amount}")

        try:
            # Add the additional fee to the database
            db.session.add(addfee)
            db.session.flush()  # Ensure the new fee gets an ID before association
            logging.debug(f"Added additional fee with ID: {addfee.additional_fee_id}")

            # Associate the additional fee with the receipt
            receipt.additional_fees.append(addfee)
            logging.debug(f"Associated fee with receipt ID: {receipt_id}")

            # Update the total receipt amount by adding the additional fee amount
            old_total = receipt.receipt_total_amount
            receipt.receipt_total_amount = old_total + addfee_amount
            logging.debug(f"Updated receipt total amount: {old_total} -> {receipt.receipt_total_amount}")

            # Commit the transaction
            db.session.commit()
            logging.info(f"Successfully added and associated fee with receipt ID: {receipt_id}. Updated total amount.")
            return jsonify({"message": "Additional fee added and associated with receipt successfully"}), 201

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error during fee insertion: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400



def test():
    data = request.json

    logging.info("Received data for processing additional fees.")
    try:
        # Retrieve the receipt_id from the request data
        receipt_id = data.get('receiptID')
        if not receipt_id:
            logging.error("Missing receipt_id in the request data.")
            return jsonify({'error': 'Missing receipt_id'}), 400
        logging.debug(f"Receipt ID retrieved: {receipt_id}")

        # Query the database for the existing receipt
        existing_receipt = db.session.query(Receipt).filter_by(receipt_id=receipt_id).first()
        if not existing_receipt:
            logging.error(f"Receipt with ID {receipt_id} not found in the database.")
            return jsonify({'error': 'Receipt not found'}), 404
        logging.debug(f"Found receipt: {existing_receipt}")

        # Process additional fees
        additional_fees = data.get('additional_fees', [])
        if not isinstance(additional_fees, list):
            logging.error("Invalid format for additional fees. Expected a list.")
            return jsonify({'error': 'Invalid format for additional fees'}), 400
        logging.debug(f"Processing {len(additional_fees)} additional fees.")

        for additional_fee in additional_fees:
            additional_fee_name = additional_fee.get("Name")
            additional_fee_amount = additional_fee.get("Amount")

            if not additional_fee_name or not isinstance(additional_fee_amount, (int, float)):
                logging.warning(f"Skipping invalid additional fee data: {additional_fee}")
                continue

            logging.debug(f"Processing additional fee: {additional_fee_name} - Amount: {additional_fee_amount}")

            # Check if the additional fee already exists
            existing_additional_fee = db.session.query(AdditionalFees).filter_by(additional_fee_name=additional_fee_name).first()
            if existing_additional_fee:
                logging.debug(f"Existing additional fee found: {existing_additional_fee}")
                existing_receipt.additional_fees.append(existing_additional_fee)
            else:
                # Create a new additional fee if it doesn't exist
                logging.debug(f"Creating new additional fee: {additional_fee_name}")
                new_additional_fee = AdditionalFees(
                    additional_fee_name=additional_fee_name,
                    additional_fee_amount=additional_fee_amount
                )
                db.session.add(new_additional_fee)
                existing_receipt.additional_fees.append(new_additional_fee)

        # Commit the changes
        db.session.commit()
        logging.info("Additional fees processed successfully.")
        return jsonify({'message': 'Additional fees processed successfully'}), 200

    except SQLAlchemyError as e:
        logging.error(f"SQLAlchemy error occurred: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error processing additional fees'}), 500

    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
