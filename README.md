🚀 MessageFlow – Smart Customer Support Platform

MessageFlow is a Customer Support Messaging Web Application built using Flask, HTML, CSS, and JavaScript.
The project simulates a real-world support system where customers raise queries and support agents manage, prioritize, and resolve them efficiently through a professional dashboard.

This project was developed as part of an internship assignment to demonstrate full-stack development skills, system design, and user experience considerations.

✨ Key Features
👥 Role-Based Access

Customer and Support Agent roles

Separate dashboards and functionality for each role

Secure session-based access control

🧑‍💻 Customer Features

Interactive chat interface

Automated bot welcome message

Submit support queries

View conversation history

Friendly, modern UI

🧑‍💼 Support Agent Features

Centralized dashboard with customer inbox

View and respond to customer queries

Prioritize urgent messages

Mark conversations as open or resolved

Clean and professional chat interface

📂 CSV-Based Bulk Message Ingestion

Upload customer messages via CSV file

Uploaded messages automatically appear in the agent inbox

Enables agents to resolve queries one by one

Useful for bulk support ticket handling

📊 Analytics Dashboard

View total messages

Open vs resolved queries

Urgent vs normal messages

Basic insights for support operations

🎨 UI & UX

Consistent theme across all pages

Modern navigation bar

Inline UI-based feedback (no browser alerts)

Responsive and user-friendly design

🛠️ Tech Stack

Backend: Flask (Python)

Frontend: HTML, CSS, JavaScript

Database: SQLite

ORM: Flask-SQLAlchemy

Deployment: Render (Free Tier)

📁 Project Structure
Branch_intern/
├── app.py
├── requirements.txt
├── Procfile
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── registration.html
│   ├── customer.html
│   ├── dashboard.html
│   ├── agentchat.html
│   ├── analytics.html
│   ├── upload.html
│   └── settings.html
├── static/
└── instance/

▶️ How to Run Locally

Clone the repository:

git clone https://github.com/Om-Singh-45/MessageFlow---Smart-Customer-Support-Platform.git


Navigate to the project folder:

cd Branch_intern


Install dependencies:

pip install -r requirements.txt


Run the application:

python app.py
