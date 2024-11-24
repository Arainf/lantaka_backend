from flask import request, jsonify
from model import Discounts, db


def add_discount():
    data = request.json
    new_discount = Discounts(
        discount_name=data['discount_name'],
        discount_percentage=data['discount_percentage']
    )
    db.session.add(new_discount)
    db.session.commit()
    return jsonify({"message": "Discount added successfully"}), 201


def edit_discount():
    data = request.json
    discount = Discounts.query.get(data['id'])
    if discount:
        discount.discount_name = data['discount_name']
        discount.discount_percentage = data['discount_percentage']
        db.session.commit()
        return jsonify({"message": "Discount updated successfully"}), 200
    return jsonify({"message": "Discount not found"}), 404


def delete_discount():
    discount_id = request.args.get('id')
    discount = Discounts.query.get(discount_id)
    if discount:
        db.session.delete(discount)
        db.session.commit()
        return jsonify({"message": "Discount deleted successfully"}), 200
    return jsonify({"message": "Discount not found"}), 404