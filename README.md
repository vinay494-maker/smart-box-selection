# Smart Box Selection System

## Project Overview

The Smart Box Selection System is a Django-based web application that helps recommend a suitable shipping box for an ecommerce order. It uses product dimensions, product weight, box dimensions, weight capacity, and box cost to find a suitable option.

## Features

* Store product and shipping-box details.
* Create orders with products and quantities.
* Check product dimensions and weight against box limits.
* Recommend a suitable, lower-cost box.
* Display order results through a webpage.
* Run automated tests for the recommendation logic.

## Technologies Used

* Python
* Django
* Django REST Framework
* HTML and CSS
* JavaScript
* SQLite

## Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/vinay494-maker/smart-box-selection.git
cd smart-box-selection
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

On Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Start the development server

```bash
python manage.py runserver
```

Open the local address shown in the terminal to use the application.

## Testing

Run the automated tests with:

```bash
python manage.py test
```

## Current Limitation

The current recommendation logic checks whether each product individually fits the box and whether the order weight is within the box’s weight limit. It does not yet verify whether multiple products can physically fit together in one box.

## Project Structure

* `config/` — Django project configuration
* `packing/` — application code, recommendation logic, and tests
* `manage.py` — Django management utility
* `requirements.txt` — project dependencies

## Author

Vinay Kumar
