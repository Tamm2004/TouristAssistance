# 🧭 AmritPath — Tourist Assistance Platform

**AmritPath** is a full-stack **Tourist Assistance Platform** built with **Python and Django** to provide tourists with a convenient, interactive, and personalized way to explore destinations, discover places, find food and accommodation, plan transportation, and access essential travel services.

The platform brings multiple tourism-related services together in one application, helping users make informed decisions and have a smoother travel experience.

---

## ✨ Features

### 🗺️ Explore Places

* Browse tourist attractions and destinations.
* View detailed information about places.
* Explore places based on categories.
* View ratings and reviews from other users.
* Add preferred places to a wishlist.

### 🍴 Food & Restaurants

* Discover food options available at the destination.
* Browse food details and categories.
* View user reviews and ratings.
* Save preferred food options to the wishlist.

### 🏨 Hotels & Accommodation

* Explore available hotels.
* View hotel information and images.
* Check ratings and reviews.
* Add hotels to the wishlist.

### 🛍️ Shops & Products

* Browse local shops and products.
* View product details and images.
* Discover shopping options available for tourists.
* Save interesting products and shops.

### ⭐ Reviews & Ratings

* Users can submit reviews for places, hotels, food, shops, and other services.
* Ratings help users make better travel decisions.
* User feedback contributes to the recommendation system.

### ❤️ Wishlist

* Save places, food, hotels, shops, and products.
* Access saved items from the user's wishlist.
* Wishlist data is also used to generate personalized recommendations.

### 🤖 Recommendation System

AmritPath includes a recommendation module that uses user preferences and wishlist activity to suggest relevant tourism options.

Recommendations can include:

* Tourist places
* Food
* Hotels
* Shops
* Products

The system also considers ratings and available data to improve the relevance of recommendations.

### 💬 Chatbot

* Provides assistance to users while navigating the platform.
* Helps users obtain tourism-related information.
* Designed to make interaction with the platform more convenient.

### 🌦️ Weather Information

* Provides weather-related information for destinations.
* Uses external weather services to retrieve current information.
* Helps tourists make better decisions while planning activities.

### 🚕 Transportation & Route Planning

The transportation module helps users determine suitable transportation based on distance.

The system integrates:

* **OpenStreetMap / Nominatim** for location and coordinate information.
* **OSRM** for route and distance calculation.

Transportation suggestions are based on distance:

| Distance        | Suggested Transportation |
| --------------- | ------------------------ |
| Short distance  | 🚶 Walking               |
| Medium distance | 🛺 Auto Rickshaw         |
| Longer distance | 🚕 Cab                   |

The system can also calculate estimated transportation fares.

### 💳 Cab Booking & Online Payment

* Users can book cabs through the platform.
* Cab booking information is stored in the database.
* **Razorpay** is integrated for online payment processing.
* Payment verification is performed through Razorpay's payment signature mechanism.

### 🔐 User Authentication

* User registration and login.
* Password reset functionality.
* OTP-based email verification.
* Django authentication mechanisms.
* Session-based user management.

### 🛠️ Admin & Vendor Management

The platform supports management of tourism-related content through administrative functionality, including:

* Places
* Hotels
* Food
* Shops
* Products
* Images
* Reviews
* FAQs
* User-related information
* Booking information

---

## 🧩 Modules

The application is organized into several major modules:

```text
AmritPath
│
├── User Management
│   ├── Registration
│   ├── Login
│   ├── OTP Verification
│   └── Password Reset
│
├── Tourism
│   ├── Places
│   ├── Food
│   ├── Hotels
│   ├── Shops
│   └── Products
│
├── User Interaction
│   ├── Reviews & Ratings
│   ├── Wishlist
│   └── Recommendations
│
├── Travel Assistance
│   ├── Weather
│   ├── Transportation
│   ├── Route Calculation
│   └── Chatbot
│
├── Booking
│   ├── Cab Booking
│   └── Online Payment
│
└── Administration
    ├── Content Management
    ├── Users
    ├── Reviews
    └── Bookings
```

---

## 🛠️ Tech Stack

### Backend

* **Python**
* **Django**
* **SQLite**

### Frontend

* **HTML5**
* **CSS3**
* **JavaScript**
* **Bootstrap**
* **Tailwind CSS**

### APIs & Integrations

* **OpenWeather API** — Weather information
* **OpenStreetMap / Nominatim** — Geocoding and location data
* **OSRM** — Route and distance calculation
* **Razorpay** — Online payment processing

### Development Tools

* Git
* GitHub
* Visual Studio Code

---

## 🗄️ Database Models

The application uses Django's ORM for database management.

Major models include:

* `Place`
* `PlaceImage`
* `Category`
* `Food`
* `Hotel`
* `HotelImage`
* `Shop`
* `ShopImage`
* `Product`
* `ProductImage`
* `Userregister`
* `Review`
* `Wishlist`
* `Contact`
* `FAQ`
* `Recommendation`
* `WeatherData`
* `CabBooking`

These models allow the application to manage tourism content, user interactions, recommendations, weather information, and transportation bookings.

---

## 🔄 How the Recommendation System Works

The recommendation module uses information from the user's wishlist and existing tourism data.

A simplified flow is:

```text
User Activity
     │
     ▼
Wishlist Data
     │
     ▼
Identify User Preferences
     │
     ▼
Retrieve Relevant Categories
     │
     ▼
Consider Ratings & Available Data
     │
     ▼
Generate Recommendations
     │
     ▼
Display Personalized Results
```

This allows AmritPath to provide recommendations based on the user's interests instead of displaying only generic tourism content.

---

## 🚕 Transportation Flow

```text
User selects destination
          │
          ▼
Convert location → Coordinates
          │
          ▼
OpenStreetMap / Nominatim
          │
          ▼
Calculate route & distance
          │
          ▼
OSRM Routing Service
          │
          ▼
Determine suitable transport
          │
          ▼
Calculate estimated fare
          │
          ▼
Cab Booking
          │
          ▼
Razorpay Payment
```

---

## 📁 Project Structure

```text
TouristAssistance/
│
├── TouristAssistance/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── guide/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── templates/
│   └── ...
│
├── statics/
│   └── ...
│
├── media/
│   └── ...
│
├── manage.py
├── db.sqlite3
├── .env
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Tamm2004/TouristAssistance.git
```

### 2. Navigate to the Project

```bash
cd TouristAssistance
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

If the project contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise, install the required Django and API dependencies used by the project.

### 5. Configure Environment Variables

Create a `.env` file and add the required credentials and API keys.

Example:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

OPENWEATHER_API_KEY=your_openweather_api_key

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_password
```

> ⚠️ **Security:** Never commit real API keys, payment credentials, email passwords, or Django secret keys to GitHub. Use environment variables and keep `.env` in `.gitignore.

### 6. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create an Admin Account

```bash
python manage.py createsuperuser
```

Follow the prompts to create your administrator account.

### 8. Run the Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## 🔑 External Services

The project uses several external services:

| Service                   | Purpose                            |
| ------------------------- | ---------------------------------- |
| OpenWeather               | Weather information                |
| OpenStreetMap / Nominatim | Geocoding and location coordinates |
| OSRM                      | Distance and route calculation     |
| Razorpay                  | Cab booking payments               |

You may need to create accounts and obtain API credentials for services that require authentication.

---

## 🔒 Security Considerations

Before deploying this project to production:

* Set `DEBUG=False`.
* Move all secrets to environment variables.
* Use a strong Django `SECRET_KEY`.
* Configure `ALLOWED_HOSTS`.
* Do not expose API keys or payment credentials.
* Configure HTTPS.
* Use a production-ready database.
* Properly configure static and media file handling.
* Review CSRF and authentication settings.
* Never commit `.env` files containing real credentials.

---

## 🎯 Project Objectives

The primary objectives of AmritPath are:

* Provide tourists with a centralized tourism platform.
* Simplify destination discovery.
* Help users find food, hotels, shops, and tourist attractions.
* Provide personalized recommendations.
* Assist users with transportation and route planning.
* Provide weather information.
* Enable online cab booking and payment.
* Improve the overall travel planning experience.

---

## 🔮 Future Enhancements

Possible future improvements include:

* 📱 Mobile application for Android and iOS
* 🗺️ Interactive map-based destination exploration
* 🧠 More advanced machine-learning-based recommendations
* 🌐 Multi-language support
* 💬 Improved AI-powered tourism chatbot
* 📅 Automated itinerary generation
* 🏨 Hotel and travel booking integrations
* 🚨 Emergency assistance and SOS functionality
* 📍 Real-time location tracking
* 🔔 Personalized travel notifications
* ☁️ Cloud deployment and scalable infrastructure

---

## 💡 What I Learned

Developing AmritPath provided hands-on experience in:

* Full-stack web application development
* Django architecture and ORM
* Database design and relationships
* REST API integration
* Third-party API integration
* Authentication and OTP workflows
* Payment gateway integration
* Geocoding and route calculation
* Recommendation system development
* User reviews and rating systems
* Responsive frontend development
* Git and GitHub-based project management

---

**AmritPath — Making travel planning simpler, smarter, and more convenient.** 🧭✨
