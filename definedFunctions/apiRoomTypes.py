from flask import Flask, request, jsonify, url_for
from model import RoomType, db
import base64

def get_room_types():
    room_types = RoomType.query.all()
    return jsonify([
        {
            **room_type.to_dict(),
            "room_type_img_url": url_for(
                "serve_image", item_id=room_type.room_type_id, type="room", _external=True
            ) if room_type.room_type_img else None
        } 
        for room_type in room_types
    ])

def add_room_type():
    data = request.json
    new_room_type = RoomType(
        room_type_name=data['room_type_name'],
        room_type_description=data.get('room_type_description'),
        room_type_price_internal=data['room_type_price_internal'],
        room_type_price_external=data['room_type_price_external'],
        room_type_capacity=data['room_type_capacity'],
        room_type_img=data.get('room_type_img', '').encode('utf-8') if data.get('room_type_img') else None
    )
    db.session.add(new_room_type)
    db.session.commit()
    return jsonify({
        **new_room_type.to_dict(),
        "room_type_img_url": url_for(
            "serve_image", item_id=new_room_type.room_type_id, type="room", _external=True
        ) if new_room_type.room_type_img else None
    }), 201

def update_room_type(id):
    room_type = RoomType.query.get_or_404(id)
    data = request.json
    
    room_type.room_type_name = data.get('room_type_name', room_type.room_type_name)
    room_type.room_type_description = data.get('room_type_description', room_type.room_type_description)
    room_type.room_type_price_internal = data.get('room_type_price_internal', room_type.room_type_price_internal)
    room_type.room_type_price_external = data.get('room_type_price_external', room_type.room_type_price_external)
    room_type.room_type_capacity = data.get('room_type_capacity', room_type.room_type_capacity)
    
    if 'room_type_img' in data:
        # Decode base64 string into binary data
        base64_image = data.get('room_type_img', '').split(",")[-1]  # Handle "data:image/...;base64," prefix
        room_type.room_type_img = base64.b64decode(base64_image) if base64_image else None
    
    db.session.commit()
    
    return jsonify({
        **room_type.to_dict(),
        "room_type_img_url": url_for(
            "serve_image", item_id=room_type.room_type_id, type="room_type", _external=True
        ) if room_type.room_type_img else None
    })

def delete_room_type(id):
    room_type = RoomType.query.get_or_404(id)
    db.session.delete(room_type)
    db.session.commit()
    return '', 204