import logging
from model import db, RoomReservation, VenueReservation, Notification, Room, Venue

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def create_cleaning_done_notification(reservation_type, location_name):
    """Create a notification for when cleaning is completed."""
    logging.debug(f"Creating notification for {reservation_type} {location_name}.")
    notification = Notification(
        notification_type="Cleaning Complete",
        notification_description=f"Cleaning for {reservation_type} {location_name} has been completed",
        is_read=False,
        notification_role="Administrator"
    )
    db.session.add(notification)

def update_room_status(room_id):
    """Update room status to ready after cleaning."""
    room = Room.query.get(room_id)
    if room:
        logging.debug(f"Updating status for room ID {room_id} to 'ready'.")
        room.room_status = "ready"
    else:
        logging.warning(f"Room with ID {room_id} not found.")

def update_venue_status(venue_id):
    """Update venue status to ready after cleaning."""
    venue = Venue.query.get(venue_id)
    if venue:
        logging.debug(f"Updating status for venue ID {venue_id} to 'ready'.")
        venue.venue_status = "ready"
    else:
        logging.warning(f"Venue with ID {venue_id} not found.")

def update_cleaning_status():
    """
    Check and update reservations with 'onCleaning' status.
    This function should be called periodically (e.g., every 5 minutes).
    """
    logging.info("Starting update_cleaning_status process.")
    try:
        # Process room reservations
        room_reservations = RoomReservation.query.filter_by(room_reservation_status="onCleaning").all()
        logging.debug(f"Found {len(room_reservations)} room reservations with 'onCleaning' status.")
        for reservation in room_reservations:
            logging.info(f"Cleaning completed for room ID {reservation.room_id}.")
            
            # Update reservation status
            reservation.room_reservation_status = "done"
            
            # Update room status
            update_room_status(reservation.room_id)
            
            # Create notification
            create_cleaning_done_notification("Room", reservation.room.room_name)

        # Process venue reservations
        venue_reservations = VenueReservation.query.filter_by(venue_reservation_status="onCleaning").all()
        logging.debug(f"Found {len(venue_reservations)} venue reservations with 'onCleaning' status.")
        for reservation in venue_reservations:
            logging.info(f"Cleaning completed for venue ID {reservation.venue_id}.")
            
            # Update reservation status
            reservation.venue_reservation_status = "done"
            
            # Update venue status
            update_venue_status(reservation.venue_id)
            
            # Create notification
            create_cleaning_done_notification("Venue", reservation.venue.venue_name)

        # Commit all changes
        db.session.commit()
        logging.info("All updates committed successfully.")

    except Exception as e:
        logging.error(f"Error occurred during update_cleaning_status: {e}", exc_info=True)
        db.session.rollback()
