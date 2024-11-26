from flask import jsonify
from model import RoomType, Venue

def get_Price(guestType):
    # Fetch capacities for room types
    DoubleCap = RoomType.query.filter(RoomType.room_type_id == 1).first().room_type_capacity
    TripleCap = RoomType.query.filter(RoomType.room_type_id == 2).first().room_type_capacity
    MatrimonialCap = RoomType.query.filter(RoomType.room_type_id == 3).first().room_type_capacity
    
    # Get all venue data
    venues = Venue.query.all()
    print(f"Total Venues: {len(venues)}")

    # Check guest type and fetch prices accordingly
    if guestType == "internal":
        DoublePrice = RoomType.query.filter(RoomType.room_type_id == 1).first().room_type_price_internal
        TriplePrice = RoomType.query.filter(RoomType.room_type_id == 2).first().room_type_price_internal
        MatrimonialPrice = RoomType.query.filter(RoomType.room_type_id == 3).first().room_type_price_internal
        venue_Holder = [{
            "venue_id": venue.venue_id,
            "venue_name": venue.venue_name,
            "venue_price_internal": venue.venue_pricing_internal,
            "venue_capacity": venue.venue_capacity
        } for venue in venues]

        # Return JSON response with internal prices
        return jsonify({
            "matrimonial_capacity": MatrimonialCap,
            "double_capacity": DoubleCap,
            "triple_capacity": TripleCap,
            "double_price": DoublePrice,
            "triple_price": TriplePrice,
            "matrimonial_price": MatrimonialPrice,
            "venue_Holder": venue_Holder
        })

    else:
        DoublePrice = RoomType.query.filter(RoomType.room_type_id == 1).first().room_type_price_external
        TriplePrice = RoomType.query.filter(RoomType.room_type_id == 2).first().room_type_price_external
        MatrimonialPrice = RoomType.query.filter(RoomType.room_type_id == 3).first().room_type_price_external
        venue_Holder = [{
            "venue_id": venue.venue_id,
            "venue_name": venue.venue_name,
            "venue_price_external": venue.venue_pricing_external,
            "venue_capacity": venue.venue_capacity
        } for venue in venues]

        # Return JSON response with external prices
        return jsonify({
            "matrimonial_capacity": MatrimonialCap,
            "double_capacity": DoubleCap,
            "triple_capacity": TripleCap,
            "double_price": DoublePrice,
            "triple_price": TriplePrice,
            "matrimonial_price": MatrimonialPrice,
            "venue_Holder": venue_Holder
        })
