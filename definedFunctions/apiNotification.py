from flask import Flask, jsonify, request
from model import Notification, db
from datetime import datetime, date, time
import json


def get_Notification():
    unread_notifications = Notification.query.filter_by(is_read=False).all()
    if unread_notifications:
        notificationList = []

        for notification in unread_notifications:
            notification_details = {
                "notification_id": notification.notification_id,
                "notification_type": notification.notification_type,
                "notification_description": notification.notification_description,
                "is_read": notification.is_read
            }
            notificationList.append(notification_details)

        return jsonify(notificationList), 200
    else:
        return jsonify({"error": "No notifications found"}), 404

def create_Notification():
    data = request.json

    new_notification = Notification(
        notification_type = data.get("notification_type"),
        notification_description=data.get('notification_description'),
        is_read=False  # Default to unread
    )
    print(type(new_notification)) 
    db.session.add(new_notification)
    db.session.commit()

    return jsonify({"message": "Notification created"})

def update_Notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True  # Mark as read
    db.session.commit()
    return jsonify(notification.to_dict())

def delete_Notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    return jsonify({"message": "Notification deleted"})

