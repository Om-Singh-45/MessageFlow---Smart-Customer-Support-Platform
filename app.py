from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-for-sessions'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///support.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)  # Now required and unique
    role = db.Column(db.String(20), nullable=False)  # 'customer' or 'agent'
    phone = db.Column(db.String(20))  # Optional field for customers
    department = db.Column(db.String(50))  # Optional field for agents
    account_type = db.Column(db.String(20))  # Optional field for customers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)  # User ID of customer
    message_text = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='Normal')  # 'Urgent' or 'Normal'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Open')  # 'Open' or 'Resolved'

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, nullable=False)  # ID of the original message
    agent_name = db.Column(db.String(100), nullable=False)  # Name of the agent who replied
    reply_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Urgency detection function
def detect_urgency(text):
    urgent_keywords = ["loan", "approval", "disbursement", "delay", "urgent", "help", "problem", "money","issue"]
    for word in urgent_keywords:
        if word.lower() in text.lower():
            return "Urgent"
    return "Normal"

# Page routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("registration.html")

@app.route("/customer")
def customer():
    # Check if user is logged in as customer
    if session.get('role') != 'customer':
        return redirect(url_for('login'))
    return render_template("customer.html")

@app.route("/dashboard")
def dashboard():
    # Check if user is logged in as agent
    if session.get('role') != 'agent':
        return redirect(url_for('login'))
    return render_template("dashboard.html")

@app.route("/agent/chat/<int:conversation_id>")
def agent_chat(conversation_id):
    # Check if user is logged in as agent
    if session.get('role') != 'agent':
        return redirect(url_for('login'))
    return render_template("agentchat.html", conversation_id=conversation_id)

@app.route("/agent/analytics")
def agent_analytics_page():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))
    return render_template("analytics.html")

@app.route("/agent/upload")
def agent_upload_page():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))
    return render_template("upload.html")

@app.route("/agent/settings")
def agent_settings_page():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))
    return render_template("settings.html")

# Authentication endpoints
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    email = data.get("email")  # Now using email for login
    name = data.get("name")
    role = data.get("role")  # 'customer' or 'agent'
    
    if not email or not role:
        return jsonify({"error": "Email and role are required"}), 400
    
    # Check if user exists in database with matching email and role
    user = User.query.filter_by(email=email, role=role).first()
    if not user:
        return jsonify({"error": "Invalid email or role"}), 401
    
    # Store user in session
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_email'] = user.email
    session['role'] = user.role
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    })

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    role = data.get("role")  # 'customer' or 'agent'
    phone = data.get("phone")  # For customers
    department = data.get("department")  # For agents
    account_type = data.get("account_type")  # For customers
    
    # Validate required fields
    if not name or not email or not role:
        return jsonify({"error": "Name, email, and role are required"}), 400
    
    # Validate role
    if role not in ["customer", "agent"]:
        return jsonify({"error": "Invalid role. Must be 'customer' or 'agent'"}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409
    
    # Create user in database
    user = User(
        name=name, 
        email=email, 
        role=role,
        phone=phone if role == 'customer' else None,
        department=department if role == 'agent' else None,
        account_type=account_type if role == 'customer' else None
    )
    db.session.add(user)
    db.session.commit()
    
    # Store user in session
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_email'] = user.email
    session['role'] = user.role
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "department": user.department,
            "account_type": user.account_type
        }
    })

# Customer chat functionality
@app.route("/api/customer/message", methods=["POST"])
def customer_send_message():
    if session.get('role') != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    message_text = data.get("message")
    
    if not message_text:
        return jsonify({"error": "Message text is required"}), 400
    
    # Find customer user
    customer = db.session.get(User, session.get('user_id'))
    if not customer or customer.role != 'customer':
        return jsonify({"error": "Customer not found"}), 404
    
    # Create message with urgency detection
    urgency = detect_urgency(message_text)
    message = Message(
        customer_id=customer.id,
        message_text=message_text,
        urgency=urgency
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": {
            "id": message.id,
            "message_text": message.message_text,
            "urgency": message.urgency,
            "timestamp": message.timestamp.isoformat()
        }
    })

@app.route("/api/customer/messages", methods=["GET"])
def customer_get_messages():
    if session.get('role') != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    
    # Find customer user
    customer = db.session.get(User, session.get('user_id'))
    if not customer or customer.role != 'customer':
        return jsonify({"error": "Customer not found"}), 404
    
    # Get all messages for this customer
    messages = Message.query.filter_by(customer_id=customer.id).order_by(Message.timestamp.desc()).all()
    
    result = []
    for msg in messages:
        # Get replies for this message
        replies = Reply.query.filter_by(message_id=msg.id).order_by(Reply.timestamp.asc()).all()
        
        message_data = {
            "id": msg.id,
            "message_text": msg.message_text,
            "urgency": msg.urgency,
            "timestamp": msg.timestamp.isoformat(),
            "status": msg.status,
            "replies": [
                {
                    "id": reply.id,
                    "agent_name": reply.agent_name,
                    "reply_text": reply.reply_text,
                    "timestamp": reply.timestamp.isoformat()
                }
                for reply in replies
            ]
        }
        result.append(message_data)
    
    return jsonify(result)

# Agent dashboard functionality
@app.route("/api/agent/messages", methods=["GET"])
def agent_get_messages():
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get all messages ordered by timestamp (newest first)
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    
    # Group by customer_id to create "conversations"
    conversations = {}
    
    for msg in messages:
        if msg.customer_id not in conversations:
            # Get customer info
            customer = db.session.get(User, msg.customer_id)
            if not customer:
                continue
                
            conversations[msg.customer_id] = {
                "id": msg.id, # Use latest message ID as conversation reference
                "customer_id": msg.customer_id,
                "customer_name": customer.name,
                "customer_email": customer.email,
                "customer_phone": customer.phone,
                "account_type": customer.account_type,
                "message_text": msg.message_text, # Latest message preview
                "urgency": msg.urgency, 
                "timestamp": msg.timestamp.isoformat(),
                "status": msg.status,
                "message_count": 0,
                "has_urgent": False
            }
        
        # Update conversation stats
        conversations[msg.customer_id]["message_count"] += 1
        if msg.urgency == "Urgent" and msg.status == "Open":
            conversations[msg.customer_id]["has_urgent"] = True
            conversations[msg.customer_id]["urgency"] = "Urgent" # Upgrade thread urgency if ANY open message is urgent
            
        # If ANY message is Open, the conversation is Open
        if msg.status == "Open":
            conversations[msg.customer_id]["status"] = "Open"

    # Convert to list
    result = list(conversations.values())
    
    # Custom sort: 
    # 1. Urgent AND Open (Most critical)
    # 2. Open (Pending)
    # 3. Timestamp (Recent first)
    result.sort(key=lambda x: (
        1 if x["has_urgent"] and x["status"] == "Open" else 0,
        1 if x["status"] == "Open" else 0,
        x["timestamp"]
    ), reverse=True)
    
    return jsonify(result)

@app.route("/api/agent/stats", methods=["GET"])
def agent_get_stats():
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    # 1. Total Messages
    total_vol = Message.query.count()
    
    # 2. Urgent Conversations (Open & Urgent)
    urgent_count = Message.query.filter_by(urgency='Urgent', status='Open').count()
    
    # 3. Pending Responses (Total Open)
    pending_count = Message.query.filter_by(status='Open').count()
    
    # 4. Avg Response Time (Mocked for internship level as logic is complex)
    response_time = "5m" 

    return jsonify({
        "total_messages": total_vol,
        "urgent_conversations": urgent_count,
        "pending_responses": pending_count,
        "avg_response_time": response_time
    })

@app.route("/api/agent/search", methods=["GET"])
def agent_search_messages():
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    query = request.args.get("query", "")
    
    if not query:
        return jsonify([])
    
    # Search in message text and customer names/emails
    messages = Message.query.join(User, Message.customer_id == User.id).filter(
        db.or_(
            Message.message_text.contains(query),
            User.name.contains(query),
            User.email.contains(query)
        )
    ).order_by(
        db.case((Message.urgency == 'Urgent', 1), else_=2),
        Message.timestamp.desc()
    ).all()
    
    result = []
    for msg in messages:
        # Get customer info
        customer = db.session.get(User, msg.customer_id)
        
        # Get replies for this message
        replies = Reply.query.filter_by(message_id=msg.id).order_by(Reply.timestamp.asc()).all()
        
        message_data = {
            "id": msg.id,
            "customer_id": msg.customer_id,
            "customer_name": customer.name if customer else "Unknown",
            "customer_email": customer.email if customer else None,
            "customer_phone": customer.phone if customer else None,
            "account_type": customer.account_type if customer else None,
            "message_text": msg.message_text,
            "urgency": msg.urgency,
            "timestamp": msg.timestamp.isoformat(),
            "status": msg.status,
            "replies": [
                {
                    "id": reply.id,
                    "agent_name": reply.agent_name,
                    "reply_text": reply.reply_text,
                    "timestamp": reply.timestamp.isoformat()
                }
                for reply in replies
            ]
        }
        result.append(message_data)
    
    return jsonify(result)

@app.route("/api/agent/message/<int:message_id>/status", methods=["PATCH"])
def agent_update_message_status(message_id):
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    status = data.get("status")
    
    if status not in ["Open", "Resolved"]:
        return jsonify({"error": "Invalid status"}), 400
    
    message = db.session.get(Message, message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404
    message.status = status
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": {
            "id": message.id,
            "status": message.status
        }
    })

@app.route("/api/agent/conversation/<int:customer_id>/status", methods=["PATCH"])
def agent_update_conversation_status(customer_id):
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    status = data.get("status")
    
    if status not in ["Open", "Resolved"]:
        return jsonify({"error": "Invalid status"}), 400
    
    # Update all messages for this customer
    messages = Message.query.filter_by(customer_id=customer_id).all()
    count = 0
    for message in messages:
        message.status = status
        count += 1
        
    db.session.commit()
    
    return jsonify({
        "success": True,
        "updated_count": count,
        "status": status
    })

# Agent chat functionality
@app.route("/api/agent/chat/<int:customer_id>", methods=["GET"])
def agent_get_conversation(customer_id):
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get customer info
    customer = db.session.get(User, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
        
    # Get all messages for this customer
    messages_db = Message.query.filter_by(customer_id=customer_id).order_by(Message.timestamp.asc()).all()
    
    message_list = []
    for msg in messages_db:
        # Get replies for this message
        replies = Reply.query.filter_by(message_id=msg.id).order_by(Reply.timestamp.asc()).all()
        
        message_data = {
            "id": msg.id,
            "message_text": msg.message_text,
            "urgency": msg.urgency,
            "timestamp": msg.timestamp.isoformat(),
            "status": msg.status,
            "replies": [
                {
                    "id": reply.id,
                    "agent_name": reply.agent_name,
                    "reply_text": reply.reply_text,
                    "timestamp": reply.timestamp.isoformat()
                }
                for reply in replies
            ]
        }
        message_list.append(message_data)
    
    # Construct response
    response_data = {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "account_type": customer.account_type or "Standard",
            "department": customer.department 
        },
        "messages": message_list
    }
    
    return jsonify(response_data)

@app.route("/api/agent/reply", methods=["POST"])
def agent_send_reply():
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    message_id = data.get("message_id")
    reply_text = data.get("reply_text")
    agent_name = session.get('user_name')  # Use the agent's name from session
    
    if not message_id or not reply_text or not agent_name:
        return jsonify({"error": "Message ID, reply text, and agent name are required"}), 400
    
    # Verify that the message exists
    message = db.session.get(Message, message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404
    
    # Create reply
    reply = Reply(
        message_id=message_id,
        agent_name=agent_name,
        reply_text=reply_text
    )
    
    db.session.add(reply)
    db.session.commit()
    
    # Also update message status to resolved
    message.status = "Resolved"
    db.session.commit()
    
    return jsonify({
        "success": True,
        "reply": {
            "id": reply.id,
            "message_id": reply.message_id,
            "agent_name": reply.agent_name,
            "reply_text": reply.reply_text,
            "timestamp": reply.timestamp.isoformat()
        }
    })

@app.route("/api/agent/upload-messages", methods=["POST"])
def agent_upload_messages():
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        # Parse CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        # Skip header if present (heuristic: check first row)
        # Assuming format: name, email, message, urgency
        rows = list(csv_input)
        if not rows:
            return jsonify({"error": "Empty CSV"}), 400
            
        count = 0
        
        for row in rows:
            if len(row) < 3: 
                continue # Skip invalid rows
                
            name = row[0].strip()
            email = row[1].strip()
            message_text = row[2].strip()
            
            # Smart Urgency Detection
            raw_urgency = row[3].strip() if len(row) > 3 else ""
            if raw_urgency.lower() in ['urgent', 'normal']:
                urgency = raw_urgency.capitalize()
            else:
                # Auto-detect if not explicitly specified or invalid
                urgency = detect_urgency(message_text)
            
            # Find or Create Customer
            customer = User.query.filter_by(email=email).first()
            if not customer:
                customer = User(
                    name=name,
                    email=email,
                    role='customer',
                    account_type='Standard'
                )
                db.session.add(customer)
                db.session.commit() # Commit to get ID
            
            # Create Message
            msg = Message(
                customer_id=customer.id,
                message_text=message_text,
                urgency=urgency,
                status='Open',
                timestamp=datetime.utcnow()
            )
            db.session.add(msg)
            count += 1
            
        db.session.commit()
        
        return jsonify({"success": True, "count": count})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/agent/analytics", methods=["GET"])
def agent_analytics_api():
    if session.get('role') != 'agent':
        return jsonify({"error": "Unauthorized"}), 401
    
    total = Message.query.count()
    open_msgs = Message.query.filter_by(status='Open').count()
    urgent = Message.query.filter_by(urgency='Urgent').count() # All urgent messages
    resolved = Message.query.filter_by(status='Resolved').count()
    
    return jsonify({
        "total": total,
        "open": open_msgs,
        "urgent": urgent,
        "resolved": resolved
    })

@app.route('/api/session')
def get_session():
    if session.get('user_id') and session.get('role'):
        user = db.session.get(User, session.get('user_id'))
        if user:
            return jsonify({
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role
                }
            })
    return jsonify({'user': None}), 401

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('role', None)
    return redirect(url_for('index'))

# For development/testing purposes
if __name__ == "__main__":
    # Create a new database file to ensure schema is updated
    # if os.path.exists('support.db'):
    #     os.remove('support.db')
    
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')