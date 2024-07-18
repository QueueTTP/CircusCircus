from flask import Blueprint, request, jsonify
from models import db, Message
from flask_login import current_user, login_required
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    new_message = Message(sender_id=current_user.id, receiver_id=data['receiver_id'], content=data['content'])
    db.session.add(new_message)
    db.session.commit()
    return jsonify({'message': 'Message sent successfully'}), 201

@messaging_bp.route('/get_messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    if current_user.id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.timestamp.desc()).all()
    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'content': msg.content,
        'timestamp': msg.timestamp,
        'status': msg.status
    } for msg in messages])

@messaging_bp.route('/mark_as_read', methods=['POST'])
@login_required
def mark_as_read():
    data = request.json
    message = Message.query.get(data['message_id'])
    if message and message.receiver_id == current_user.id:
        message.status = 'read'
        db.session.commit()
        return jsonify({'message': 'Message marked as read'})
    return jsonify({'error': 'Message not found or unauthorized access'}), 404