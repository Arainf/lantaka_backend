from flask import Flask, jsonify, request
from model import Notification, Account, db
from datetime import datetime, date, time
import json
from sqlalchemy import desc


def get_Notification():
    notifications = Notification.query.filter_by(is_read=False).all()
    notificationList = []

    for notification in notifications:
        notification_details = {
            "notification_id": notification.notification_id,
            "notification_type": notification.notification_type,
            "notification_description": notification.notification_description,
            "is_read": notification.is_read,
            "notification_role": notification.notification_role
        }
        notificationList.append(notification_details)

    return jsonify(notificationList), 200

def create_Notification():
    data = request.json

    new_notification = Notification(
        notification_type = data.get("type"),
        notification_description = data.get('description'),
        is_read=False,  # Default to unread
        notification_role =  data.get("role")
    )
    print(type(new_notification)) 
    db.session.add(new_notification)
    db.session.commit()

    return jsonify({"message": "Notification created"})

def mark_Read_Notification():
    notifications = Notification.query.filter_by(is_read=False).all()
    for notification in notifications:
        notification.is_read = True  # Mark as read

    db.session.commit()
    return jsonify({"message": "Notifications are marked as read"})