from model import Room, RoomType, Venue
import base64

# Load the image file and convert to base64
def load_image(image_path):
    with open(image_path, 'rb') as img_file:
        # Read the image file and return it as a binary object
        binary_image = img_file.read()
    return binary_image

doubleBed_img = load_image("DefaultAssets/RoomPictures/DoubleBed.webp")
tripleBed_img = load_image("DefaultAssets/RoomPictures/TripleBed.webp")
matrimonial_img = load_image("DefaultAssets/RoomPictures/Matrimonial.webp")
gazebo_img = load_image("DefaultAssets/VenuePictures/Gazebo.webp")
capizHall_img = load_image("DefaultAssets/VenuePictures/CapizHall.webp")
breezaHalll_img = load_image("DefaultAssets/VenuePictures/BreezaHall.webp")
oldTalisayBar_img = load_image("DefaultAssets/VenuePictures/OldTalisayBar.webp")

roomTypes = [
    RoomType(room_type_name="Double Bed", room_type_description="A room with two beds for double occupancy.", room_type_price="1300", room_type_capacity="2", room_type_img=doubleBed_img), 
    RoomType(room_type_name="Triple Bed", room_type_description="A spacious room with three beds for triple occupancy.", room_type_price="1500", room_type_capacity="3", room_type_img=tripleBed_img),
    RoomType(room_type_name="Matrimonial Bed", room_type_description="A cozy room with a matrimonial bed for couples.", room_type_price="1600", room_type_capacity="2", room_type_img=matrimonial_img)
]


rooms = [
    Room(room_id="Room102",room_type_id=1, room_name="Room 102", room_status="ready"),
    Room(room_id="Room104",room_type_id=1, room_name="Room 104", room_status="ready"),
    Room(room_id="Room106",room_type_id=1, room_name="Room 106", room_status="ready"),
    Room(room_id="Room108",room_type_id=1, room_name="Room 108", room_status="ready"),
    Room(room_id="Room110",room_type_id=1, room_name="Room 110", room_status="ready"),
    Room(room_id="Room112",room_type_id=1, room_name="Room 112", room_status="ready"),
    Room(room_id="Room114",room_type_id=1, room_name="Room 114", room_status="ready"),
    Room(room_id="Room116",room_type_id=3, room_name="Room 116", room_status="ready"),
    Room(room_id="Room118",room_type_id=1, room_name="Room 118", room_status="ready"),
    Room(room_id="Room120",room_type_id=1, room_name="Room 120", room_status="ready"),
    Room(room_id="Room201",room_type_id=2, room_name="Room 201", room_status="ready"),
    Room(room_id="Room202",room_type_id=1, room_name="Room 202", room_status="ready"),
    Room(room_id="Room203",room_type_id=2, room_name="Room 203", room_status="ready"),
    Room(room_id="Room204",room_type_id=1, room_name="Room 204", room_status="ready"),
    Room(room_id="Room205",room_type_id=2, room_name="Room 205", room_status="ready"),
    Room(room_id="Room206",room_type_id=1, room_name="Room 206", room_status="ready"),
    Room(room_id="Room207",room_type_id=2, room_name="Room 207", room_status="ready"),
    Room(room_id="Room208",room_type_id=1, room_name="Room 208", room_status="ready"),
    Room(room_id="Room209",room_type_id=2, room_name="Room 209", room_status="ready"),
    Room(room_id="Room210",room_type_id=1, room_name="Room 210", room_status="ready"),
    Room(room_id="Room211",room_type_id=2, room_name="Room 211", room_status="ready"),
    Room(room_id="Room212",room_type_id=1, room_name="Room 212", room_status="ready"),
    Room(room_id="Room213",room_type_id=2, room_name="Room 213", room_status="ready"),
    Room(room_id="Room214",room_type_id=1, room_name="Room 214", room_status="ready"),
    Room(room_id="Room215",room_type_id=2, room_name="Room 215", room_status="ready"),
    Room(room_id="Room216",room_type_id=1, room_name="Room 216", room_status="ready"),
    Room(room_id="Room217",room_type_id=2, room_name="Room 217", room_status="ready"),
    Room(room_id="Room218",room_type_id=1, room_name="Room 218", room_status="ready"),
    Room(room_id="Room219",room_type_id=2, room_name="Room 219", room_status="ready"),
    Room(room_id="Room220",room_type_id=1, room_name="Room 220", room_status="ready"),
    Room(room_id="Room221",room_type_id=2, room_name="Room 221", room_status="ready"),
    Room(room_id="Room222",room_type_id=1, room_name="Room 222", room_status="ready"),
    Room(room_id="Room223",room_type_id=2, room_name="Room 223", room_status="ready"),
    Room(room_id="Room224",room_type_id=1, room_name="Room 224", room_status="ready"),
    Room(room_id="Room225",room_type_id=2, room_name="Room 225", room_status="ready"),
    Room(room_id="Room226",room_type_id=1, room_name="Room 226", room_status="ready"),
    Room(room_id="Room227",room_type_id=2, room_name="Room 227", room_status="ready"),
    Room(room_id="Room228",room_type_id=1, room_name="Room 228", room_status="ready"),
    Room(room_id="Room229",room_type_id=2, room_name="Room 229", room_status="ready"),
    Room(room_id="Room230",room_type_id=1, room_name="Room 230", room_status="ready"),
    Room(room_id="Room231",room_type_id=2, room_name="Room 231", room_status="ready"),
    Room(room_id="Room232",room_type_id=1, room_name="Room 232", room_status="ready"),
    Room(room_id="Room233",room_type_id=2, room_name="Room 233", room_status="ready"),
    Room(room_id="Room234",room_type_id=1, room_name="Room 234", room_status="ready"),
    Room(room_id="Room235",room_type_id=2, room_name="Room 235", room_status="ready"),
    Room(room_id="Room236",room_type_id=3, room_name="Room 236", room_status="ready"),
    Room(room_id="Room236A", room_type_id=1,room_name="Room 236A", room_status="ready"),  # Slightly different naming
    Room(room_id="Room237",room_type_id=2, room_name="Room 237", room_status="ready")
]

venues = [
    Venue(venue_id="DiningHall", venue_name="Dinning Hall", venue_description="A spacious venue for hosting events.", venue_status="pending", venue_pricing="1000", venue_capacity="500", venue_img=capizHall_img),
    Venue(venue_id="Gazebo", venue_name="Gazebo / Sea area", venue_description="A spacious venue for hosting events.", venue_status="pending", venue_pricing="1000", venue_capacity="500", venue_img=gazebo_img),
    Venue(venue_id="BreezaHall", venue_name="Breeza Hall", venue_description="A spacious venue for hosting events.", venue_status="pending", venue_pricing="1000", venue_capacity="500", venue_img=breezaHalll_img),
    Venue(venue_id="CapizHall", venue_name="Capiz Hall", venue_description="A spacious venue for hosting events.", venue_status="pending", venue_pricing="1000", venue_capacity="500", venue_img=capizHall_img),
    Venue(venue_id="OldTalisayBar", venue_name="Old Talisay Bar", venue_description="A spacious venue for hosting events.", venue_status="pending", venue_pricing="1000", venue_capacity="500", venue_img=oldTalisayBar_img)
]




