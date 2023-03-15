# Ecommerce-Api

this is the complete backend project for Ecommerce store.  It mimics the complete Ecommerce API behaviour.


## About

This eCommerce backend application is built using Dajngo and the Django Rest Framework framework. It provides a RESTful API for managing products, orders, and customers in an online store.

## Features

- User authentication and authorization using JSON Web Tokens (JWT)
- User registration and password reset functionality
- Email confirmation for password reset
- CRUD operations and more complex operations for managing products, orders, and customers
- File upload functionality for product images


## Technologies Used

- Django
- Django REST Framework
- MySql 


## Getting Started

To run this application, you will need to have Python and MySql installed on your machine. Once you have those installed, you can follow these steps:

1. Clone this repository
2. Create a virtual environment: `python -m venv env`
3. Activate the virtual environment: `source env/bin/activate` (on Windows: `.\env\Scripts\activate`)
4. Install dependencies: `pip install -r requirements.txt`
5. Create the database: `createdb ecommerce`
6. Run migrations: `python manage.py migrate`
7. Start the server: `python manage.py runserver`

## API Documentation

Documentation for the API endpoints can be found in this link [API DOCS](https://documenter.getpostman.com/view/24318609/2s93JwMghA) .

## Database Design

This eCommerce backend application uses a MySql database with the following tables.
