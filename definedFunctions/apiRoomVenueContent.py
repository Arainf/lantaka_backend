from flask import Flask, request, jsonify
from model import db, Room, Venue, RoomType
from sqlalchemy.exc import SQLAlchemyError
import base64


def load_image(image_path):
    with open(image_path, 'rb') as img_file:
        # Read the image file and return it as a binary object
        binary_image = img_file.read()
    return binary_image

def update_venue_room(item_id):
    data = request.json
    item_type = data.get('type')
    
    print(f"Debug: Received update request for item_id={item_id}, type={item_type}, data={data}")
    
    try:
        if item_type == 'Room':
            item = Room.query.get(item_id)
            if not item:
                print(f"Debug: Room with id {item_id} not found.")
                return jsonify({"error": "Room not found"}), 404
            
            item.room_name = data.get('name', item.room_name)
            item.room_status = data.get('status', item.room_status)
            
            # Update room type description if it exists
            if item.room_type and 'description' in data:
                item.room_type.room_type_description = data['description']


            if 'room_type_id' in data:
                item.room_type_id = data.get('room_type_id', item.room_type_id)
                
        
        elif item_type == 'Venue':
            item = Venue.query.get(item_id)
            if not item:
                print(f"Debug: Venue with id {item_id} not found.")
                return jsonify({"error": "Venue not found"}), 404
            
            item.venue_name = data.get('name', item.venue_name)
            item.venue_status = data.get('status', item.venue_status)
            

            if 'image_url' in data:
                # Decode base64 string into binary data
                base64_image = data.get('image_url', '').split(",")[-1]  # Handle "data:image/...;base64," prefix
                item.venue_img = base64.b64decode(base64_image)


            if 'description' in data:
                item.venue_description = data.get('description', item.venue_description)

            if 'capacity' in data:
                item.venue_capacity = data.get('capacity', item.venue_capacity)

            if 'pricing_internal' in data:
                item.venue_pricing_internal = data.get('pricing_internal', item.venue_pricing_internal)

            if 'pricing_external' in data:
                item.venue_pricing_external = data.get('pricing_external', item.venue_pricing_external)
            
           
                
              
        
        else:
            print(f"Debug: Invalid item type {item_type}.")
            return jsonify({"error": "Invalid item type"}), 400
        
        db.session.commit()
        print(f"Debug: Successfully updated item {item_type} with id {item_id}.")
        return jsonify({"message": "Item updated successfully", "id": item_id}), 200
    
    except SQLAlchemyError as e:
        print(f"Debug: Error occurred during update: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def delete_venue_room(item_id):
    print(f"Debug: Received delete request for item_id={item_id}")
    
    try:
        room = Room.query.get(item_id)
        if room:
            db.session.delete(room)
            db.session.commit()
            print(f"Debug: Deleted Room with id {item_id}")
            return jsonify({"message": "Room deleted successfully"}), 200
        
        venue = Venue.query.get(item_id)
        if venue:
            db.session.delete(venue)
            db.session.commit()
            print(f"Debug: Deleted Venue with id {item_id}")
            return jsonify({"message": "Venue deleted successfully"}), 200
        
        print(f"Debug: Item with id {item_id} not found.")
        return jsonify({"error": "Item not found"}), 404
    
    except SQLAlchemyError as e:
        print(f"Debug: Error occurred during delete: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def create_venue_room():
    data = request.json
    item_type = data.get('type')
    
    print(f"Debug: Received create request for type={item_type}, data={data}")
    
    try:
        if item_type == 'Room':
            room_id = data.get('id')
            room_type_id = data.get('room_type')
            room_name = data.get('name')
            room_status = data.get('status', 'ready')  # Default to 'ready' if not provided
            
            # Check if the room_type_id exists
            room_type = RoomType.query.get(room_type_id)
            if not room_type:
                print(f"Debug: Invalid room_type_id {room_type_id}.")
                return jsonify({"error": "Invalid room type"}), 400
            
            new_room = Room(room_id=room_id, room_type_id=room_type_id, room_name=room_name, room_status=room_status)
            db.session.add(new_room)
        
        elif item_type == 'Venue':
            venue_id = data.get('id')
            venue_name = data.get('name')
            venue_description = data.get('description', '')
            venue_status = data.get('status', 'ready')  # Default to 'ready' if not provided
            venue_pricing_internal = data.get('pricing_internal', 0.0)
            venue_pricing_external = data.get('pricing_external', 0.0)
            venue_capacity = data.get('capacity', 0)
            venue_img = data.get('image', '').encode() if data.get('image_url') else None
            
            new_venue = Venue(
                venue_id=venue_id,
                venue_name=venue_name,
                venue_description=venue_description,
                venue_status=venue_status,
                venue_pricing_internal=venue_pricing_internal,
                venue_pricing_external=venue_pricing_external,
                venue_capacity=venue_capacity,
                venue_img=venue_img
            )
            db.session.add(new_venue)
        
        else:
            print(f"Debug: Invalid item type {item_type}.")
            return jsonify({"error": "Invalid item type"}), 400
        
        db.session.commit()
        print(f"Debug: Successfully created {item_type} with id {data.get('id')}.")
        return jsonify({"message": f"{item_type} created successfully", "id": data.get('id')}), 201
    
    except SQLAlchemyError as e:
        print(f"Debug: Error occurred during create: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
