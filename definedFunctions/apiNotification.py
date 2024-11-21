from flask import Flask, jsonify, request
from model import Notification, Account, db
from datetime import datetime, date, time
import json
from sqlalchemy import desc

def get_Notification():
    notifications = Notification.query.filter_by(is_read=False).all()
    if notifications:
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
    else:
        return jsonify({"error": "No notifications found"}), 404

def create_Notification():
    data = request.json

    most_recent_account = Account.query.order_by(desc(Account.account_id)).first()

    if most_recent_account:
        account_assigned = most_recent_account.account_role

    new_notification = Notification(
        notification_type = data.get("notification_type"),
        notification_description = data.get('notification_description'),
        is_read=False,  # Default to unread
        notification_role = account_assigned
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