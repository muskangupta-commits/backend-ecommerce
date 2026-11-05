# Cartify Backend API

Backend REST API for the Cartify e-commerce platform built with Python FastAPI and MongoDB.

## Features
- Mobile and email OTP authentication with AES-256-CBC encrypted tokens
- Product catalog with search, category filtering, and sorting
- Shopping cart management with persistent database storage
- Order placement with Cash on Delivery (COD) and order tracking
- Admin dashboard APIs for product inventory and order status management

## Requirements
- Python 3.10+
- MongoDB

## Setup and Installation

1. Create and activate a Python virtual environment:

python3 -m venv venv
source venv/bin/activate


2. Install dependencies:

pip install -r requirements.txt


3. Configure environment variables in `.env`:

APP_NAME=Cartify E-Commerce API
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
MONGODB_URI=mongodb://localhost:27017/ecommerce_db
MONGODB_DATABASE=ecommerce_db
ENCRYPTION_ALGORITHM=aes-256-cbc
ENCRYPTION_FIXED_KEY=0123456789abcdef0123456789abcdef
ENCRYPTION_FIXED_IV=abcdef9876543210
TOKEN_EXPIRE_DAYS=7


4. Run the development server:

uvicorn main:app --host 0.0.0.0 --port 8000 --reload


The API will be accessible at:
- API Base: `http://localhost:8000/api/v1`
- Swagger Documentation: `http://localhost:8000/docs`

## API Endpoints
- `POST /api/v1/auth/send-otp` - Request login verification code
- `POST /api/v1/auth/verify-otp` - Verify code and receive auth token
- `GET /api/v1/auth/me` - Get current user profile
- `GET /api/v1/products` - List products with search and filters
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/cart` - View shopping cart
- `POST /api/v1/cart` - Add item to cart
- `POST /api/v1/orders` - Place order
- `GET /api/v1/orders/my-orders` - Customer order history
- `GET /api/v1/admin/dashboard` - Admin dashboard metrics
