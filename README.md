# Auto Repair Center Management System | Flask Web Application

![Auto Repair Center Management System](https://img.shields.io/badge/Project-Auto%20Repair%20Center-success)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)

## 🔧 Web-Based Auto Repair Center Management Solution

The Auto Repair Center Management System is a comprehensive web application that enables auto repair shop owners to organize their inventory and services efficiently. This application streamlines the process of managing auto repair centers, categorizing repair items, and tracking customer information.

## ✨ Key Features

- **Secure User Authentication** - Google OAuth integration for secure account management
- **Personalized Dashboard** - Create and manage your own auto repair centers
- **Category Organization** - Items categorized by Engine, Transmission, Tires, and Body
- **Responsive Design** - Mobile-friendly interface for on-the-go management
- **REST API Integration** - JSON endpoints for third-party application integration
- **CRUD Operations** - Full Create, Read, Update, Delete functionality for items and centers

## 🛠️ Technology Stack

This project demonstrates proficiency in multiple technologies:

- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 4
- **Backend**: Python, Flask Web Framework
- **Database**: SQLAlchemy ORM with SQLite
- **Authentication**: Google OAuth 2.0
- **API**: RESTful JSON API endpoints
- **Infrastructure**: Vagrant, Unix/Linux

## 📋 Installation & Setup

Follow these steps to set up and run the application:

### Prerequisites

- Python 3.7 or higher
- Git
- Vagrant (for development environment)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YourUsername/auto-repair-center.git
   cd auto-repair-center
   ```

2. **Set up virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   ```bash
   python database_setup.py
   ```

5. **Configure Google OAuth**:
   - Create a project in [Google Developer Console](https://console.developers.google.com/)
   - Enable Google+ API
   - Create OAuth credentials
   - Download the client_secrets.json file and place it in the project root

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the application**:
   Open your browser and navigate to [http://localhost:5000](http://localhost:5000)

## 🔒 Authentication & Authorization

The application implements a secure authentication system using Google OAuth 2.0:

- Users can register and login with their Google accounts
- Each auto repair center is associated with its creator
- Only authenticated owners can modify their own centers and items
- Anti-forgery state tokens prevent cross-site request forgery

## 📱 Application Features

### For Visitors
- View all auto repair centers
- Browse items categorized by type
- See details of repair services offered

### For Authenticated Users
- Create personal auto repair centers
- Add, edit, and delete items within your centers
- Organize items by category (Engine, Transmission, Tires, Body)
- Manage pricing and service descriptions

## 🌐 API Endpoints

The application provides RESTful JSON endpoints:

- **GET /api/autorepaircenters** - List all auto repair centers
- **GET /api/autorepaircenters/{id}** - Get a specific auto repair center
- **GET /api/autorepaircenters/{id}/container** - List all items in a center
- **GET /api/autorepaircenters/{id}/container/{item_id}** - Get a specific item

## 🚀 Development & Deployment

### Development Environment

For developers, we recommend using Vagrant to ensure consistent development environments:

```bash
vagrant up
vagrant ssh
cd /vagrant
python app.py
```

### Production Deployment

For production deployment, consider:

- Using a production-ready WSGI server like Gunicorn
- Configuring a reverse proxy with Nginx
- Using PostgreSQL instead of SQLite
- Setting up HTTPS with Let's Encrypt
- Implementing proper logging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open-source and available under the MIT License.

## 📧 Contact

**Aleksandr Kuzmin** - [GitHub Profile](https://github.com/AleksanderKuzmin)

---

*This Auto Repair Center Management System was created as part of the Udacity Full Stack Web Developer Nanodegree Program.*
