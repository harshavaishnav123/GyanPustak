# GyanPustak: Library & Bookstore Management System

## Overview

**Gyan Pustak** is a full-stack **library + bookstore management system** that connects university courses with book inventory.

It allows students to:

* Discover course-related books
* Purchase books via a structured workflow
* Manage orders and reviews
* Raise support tickets

The system also supports **multi-role access control** including Admin, Superadmin, and Customer Support.

---

## Flow Diagram

                                        Login
                                          │
    ┌───────────────────────┬──────────────────────┬───────────────────────┐
    │                       │                      │                       │
 Student                  Admin               Super Admin           Customer Support
    │                       │                      │                       │
    ├──── Book Search       ├──── Inventory        ├──── Employees         ├──── Tickets
    │       │               │       │              │      │                │      │
    │       ├─ Category     │       ├─ Add Book    │      ├─ Add Admin     │      ├─ View
    │       ├─ Keyword      │       ├─ Delete      │      ├─ Add Support   │      ├─ Assign
    │       ├─ Author       │       ├─ Update Qty  │      ├─ View Staff    │      └─ Create
    │       ├─ Title        │       └─ View Books  │      └─ Delete Staff  │
    │       └─ Course       │                      │                       ├──── CAN Orders
    │                       ├──── Academic         ├──── Dashboard         │      │
    ├──── Cart              │       │              │                       │      ├─ View
    │       ├─ Add          │       ├─ University  │                       │      └─ Restock
    │       ├─ Remove       │       ├─ Department  │                       |
    │       └─ Checkout     │       ├─ Course      |                       └──── Profile
    │                       │       ├─ Instructor  └──── Profile
    ├──── Orders            │       └─ Mapping     
    │       ├─ History      │
    │       ├─ Cancel       ├──── Tickets
    │       └─ Review       │       ├─ Accept
    │                       │       └─ Complete
    ├──── Help Center       |
    │       ├─ Create Ticket└──── Profile
    │       └─ View Tickets 
    │
    └──── Profile

## Tech Stack

* **Frontend:** HTML, CSS, JavaScript (Templates)
* **Backend:** Python (Flask)
* **Database:** MySQL
* **Connector:** MySQL Connector
* **Architecture:** MVC-like (Flask + SQL layer)

---

## Key Features

### Student Features

* Search books using:
  * Title, Author, Keywords
  * Category & Sub-category
* Explore books by:
  * University → Department → Course
* Add to cart & checkout system
* Order history tracking
* **120-second cancellation window**
* Anonymous reviews & ratings
* Raise trouble tickets

---

### Admin Features

* Add / update / delete books
* Manage inventory
* Create:
  * Universities
  * Departments
  * Courses
  * Instructors
* Map books to courses
* Manage student tickets

---

### Superadmin Features

* Add/remove employees (Admins & Support staff)
* View all employees
* Full system access

---

### Customer Support Features

* View & manage tickets
* Assign tickets
* Restock cancelled orders
* Create support tickets

---

## System Highlights

* **Session-based authentication**
* **Cart + Order workflow system**
* **Time-bound cancellation logic (120 seconds)**
* **Anonymous review system**
* **Ticketing system with status tracking**
* **Inventory auto-update on order/cancellation**

---

## Database Design

The system uses a **normalized relational database** (up to BCNF level).

### Core Tables:

* Users: `student_users`, `administrators`, `customer_support_users`
* Academic: `universities`, `departments`, `courses`
* Inventory: `books`, `book_author`, `book_keywords`
* Transactions: `cart`, `orders`, `cancelled_orders`
* Feedback: `reviews`
* Support: `trouble_tickets`

 The *ER diagram on page 3* shows relationships between users, courses, books, and orders. 

---

## API Overview

### Authentication

* `/login` – User authentication
* `/logout` – Session termination

### Book & Search

* `/api/search` – Search books
* `/book_details/<id>` – View details

### Cart & Orders

* `/api/add-to-cart`
* `/api/checkout`
* `/api/orders`
* `/api/cancel-order/<id>`

### Reviews

* `/api/add-review`

### Tickets

* `/tickets/create-ticket`
* `/support/tickets`

### Admin APIs

* `/admin/books/add`
* `/admin/universities/add`
* `/admin/courses/add`

---

## Project Structure

```bash
├── app.py              # Flask backend
├── queries.py          # Database queries
├── db_config.py        # DB connection
├── templates/          # Frontend HTML pages
├── database.txt        # database used in testing
├── ER_Diagram.pdf      # ER diagram of the project
├── FINAL PROJECT REPORT.pdf # Project report
├── schema.txt          # schema used in creating database
├── README.md
```

---

## How to Run

###  Setup Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### Install Dependencies

```bash
pip install flask mysql-connector-python
```

### Setup Database

* Start MySQL Server
* Import schema & data files
* Update `db_config.py`

### Run Application

```bash
python app.py
```

Open browser:

```
http://127.0.0.1:5000/login
```

---

## Example Workflow

* Login as student
* Search & add book to cart
* Checkout → Order placed
* Cancel within 120 sec OR review after delivery
* Raise support ticket if needed

 Screenshots in the report (pages 21–30) show UI flows like login, cart, and admin dashboard. 

---

## Assumptions

* Mock payment system (no real transactions)
* Username = password (for testing)
* Only one superadmin
* Reviews are fully anonymous

---

## Future Improvements

* Real payment gateway integration
* Recommendation system (ML-based)
* JWT authentication
* Docker deployment
* Mobile app version

---

## Contributors

* Vasamsetti Nihal Tej
* Velineni Harshavaishnav
* Rebba Charan

---
