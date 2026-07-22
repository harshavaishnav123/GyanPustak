from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date
import mysql.connector
from db_config import get_db_connection
import queries

# creating a flash application instance
app = Flask(__name__)

# secret key used to securely sign-in
app.secret_key = 'user@123'

# route for login page which accepts both get and post methods
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        db = get_db_connection()
        if db is None:
            return jsonify({"success": False, "error": "DB connection failed"})
        
        data = request.get_json(force=True)
        username = data.get('username')
        password = data.get('password')
      
        cursor = db.cursor(dictionary=True)
        # verify user's credentials in the database
        result = queries.check_user_credentials(cursor, username, password)
        
        if result.get('success'):
            session['user_id'] = username
            session['role'] = result.get('role')
            if result.get('data'):
                session['user_name'] = result['data'].get('first_name', username)

        cursor.close()
        db.close()
        # returning the login results in json format 
        return jsonify(result)

    # displaying th login request for get request
    return render_template('login.html')
# route for logout that clears the session and redirects to the login page
@app.route('/logout',methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))

# student apis

# this is a helper function that returns the user_id of the current session
def get_current_student():
    return session.get('user_id') 

# route For student dashboard
@app.route('/student_dash')
def dashboard(): return render_template('student_dash.html')

# route For explore page
@app.route('/explore')
def explore(): return render_template('explore.html')

# route For cart page
@app.route('/cart')
def cart(): return render_template('cart.html')

# route For orders page
@app.route('/orders')
def orders(): return render_template('orders.html')

# route For help page
@app.route('/help')
def help_center(): return render_template('help.html')

# route For profile page
@app.route('/profile')
def profile(): return render_template('profile.html')

# api end point for getting profile information of a logged-in student
@app.route('/student/student-profile',methods=['GET'])
def api_student_profile():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    student_id = session.get('user_id')
    if not student_id:
        cursor.close()
        db.close()
        return jsonify({"error": "User not logged in"}),401
    # fetching data of student profile in the database
    data = queries.get_student_profile(cursor, student_id)
    cursor.close(); db.close()
    if not data:
        return jsonify({"error": "User not found"}),404
    # returning results in the json format
    return jsonify(data)

# api end point for getting customer support tickets
@app.route('/tickets/get-tickets', methods=['GET'])
def api_get_tickets():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    student_id = get_current_student()
    # fetching the tickets based on the student name in the database
    tickets = queries.get_student_tickets(cursor, queries.get_student_username(cursor,student_id))
    cursor.close(); db.close()
    # returning the tickets in the json format
    return jsonify(tickets)

# api endpoint for creating a customer support ticket
@app.route('/tickets/create-ticket', methods=['POST'])
def api_create_ticket():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    student_id = get_current_student()
    data = request.json
    # inserting values of customer support ticket into the database
    success = queries.insert_ticket(cursor, data['title'], data['desc'], data['type'], student_id)
    if success: 
        db.commit() 
    cursor.close(); db.close()
    return jsonify({'success': success})
# api end point for fetching the book details based on the book id
@app.route('/book_details/<int:book_id>',methods=['GET'])
def book_details(book_id):
    db=get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching the required books with the query in the database
    cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    # fetching author_name with the query in the database
    cursor.execute("SELECT author_name FROM book_author WHERE book_id = %s", (book_id,))
    author_list = [row['author_name'] for row in cursor.fetchall()]
    authors_str = ", ".join(author_list) if author_list else "Unknown"
    # fetching rating,review with the query in the database
    cursor.execute("SELECT rating, review_text FROM reviews WHERE book_id = %s", (book_id,))
    reviews = cursor.fetchall()
    # diverting the page into book_details page
    return render_template('book_details.html', book=book, authors=authors_str, reviews=reviews)
# api endpoint for cart page
@app.route('/api/cart', methods=['GET'])
def get_cart():
    student_id = session.get('user_id')
    if not student_id:
        return jsonify([])
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching a particular student's cart in the database
    items = queries.get_student_cart(cursor, student_id)
    db.commit()
    cursor.close()
    db.close()
    # returning the results in json file
    return jsonify(items)

# api endpoint for deleting the element in the cart based on cart_id
@app.route('/api/cart/remove/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    student_id = session.get('user_id')
    if not student_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # deleting the item that is added in the cart
    success = queries.delete_cart_item(cursor, cart_id, student_id)
    if success:
        db.commit()
    cursor.close()
    db.close()
    return jsonify({'success': success})

# api endpoint for adding the book into the cart
@app.route('/api/add-to-cart', methods=['POST'])
def api_add_to_cart():
    data = request.json
    book_id=data['book_id']
    student_id = get_current_student() 
    if not student_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    success = False
    try:
        # fetching price of books with the book_id
        q = "SELECT price FROM books WHERE book_id = %s"
        cursor.execute(q, (book_id,))
        result = cursor.fetchone()
        price=result['price']
        # fetching the books in the cart
        cursor.execute("SELECT * FROM cart WHERE book_id = %s AND student_id = %s", (book_id, student_id))
        cart_result = cursor.fetchone()
        # updating the quantity in the cart and adding book in the cart
        if cart_result:
            success = queries.update_cart_quantity(cursor, book_id, student_id)
        else:
            success = queries.add_item_to_cart(cursor, student_id, book_id, price)
        if success:
            db.commit()
    
    except Exception as e:
        print(f"Error in route: {e}")
        db.rollback() 
        success = False
    finally:
        cursor.close()
        db.close()
        
    return jsonify({'success': success})

# api endpoint for checkout
@app.route('/api/checkout', methods=['POST'])
def checkout():
    student_id = session.get('user_id') 
    if not student_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    # data of payment details from frontend
    payment_data = request.json 
    if not payment_data:
        return jsonify({'success': False, 'message': 'Payment details missing'})
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)
    
    try:
        # fetching the student's cart
        cart_items = queries.get_student_cart(cursor, student_id)
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'})
        # fetching processing checkout from payment details
        result = queries.process_checkout(cursor, student_id, cart_items, payment_data)
        if result['success']:
            db.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': result['message']})
            
    except Exception as e:
        db.rollback()
        print(f"Checkout Error: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        db.close()

# api endpoint for orders page
@app.route('/api/orders',methods=['GET'])
def api_orders():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    student_id = get_current_student()
    # fetching orders made by student using student_id
    orders = queries.get_student_orders(cursor, student_id)
    cursor.close(); db.close()
    # returning results in json format
    return jsonify(orders)

# api endpoint for cancelling order based on order_id in 120s window
@app.route('/api/cancel-order/<int:order_id>', methods=['POST'])
def api_cancel_order(order_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    student_id = session.get('user_id') 
    # deleting the order from the database
    success, msg = queries.delete_order_if_recent(cursor, order_id, student_id)
    if success:
        db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'message': msg})
# api endpoint for marking sucessful based on order_id
@app.route('/student/ordersuccess/<int:order_id>', methods=['POST'])
def order(order_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True) 
    # updating the order status to ordered
    cursor.execute(
                "UPDATE orders SET status='ordered' WHERE order_id = %s",
                (order_id,)
            )
    db.commit()
    cursor.close()
    db.close()
    return 
# api endpoint for verifying and getting books
@app.route('/api/verify-and-get-books', methods=['POST'])
def verify_and_get_books():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching the books by exploring the whole database
    ans,books=queries.explore_db(cursor,data)
    cursor.close()
    db.close()
    return jsonify({'success': ans, 'books': books})

# api endpoint for searching the book
@app.route('/api/search', methods=['GET'])
def api_search_books():
    search_term = request.args.get('q', '') 
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching the books in the database
    results = queries.search_books_in_db(cursor, search_term)
    cursor.close()
    db.close()
    return jsonify(results)


# admin and super-admin apis

# api endpoint for routing to admin dashboard
@app.route('/admin_dash')
def admin_dashboard():
    if session.get('role') not in ['admin']:
        return redirect(url_for('login'))
        
    employee_id = session.get('user_id')
    db = get_db_connection()
    if db is None:
        return "Database Connection Error", 500
    
    cursor = db.cursor(dictionary=True)
    # fetching relevant data based on employee_id
    admin_data = queries.get_admin_profile(cursor, employee_id)
    counts = queries.get_dashboard_counts(cursor, employee_id)
    books = queries.get_all_books_basic(cursor)
    assigned = queries.get_tickets_by_status_and_admin(cursor,'assigned')
    in_process = queries.get_tickets_by_status_and_admin(cursor, 'in-process')
    completed = queries.get_tickets_by_status_and_admin(cursor, 'completed')

    cursor.close()
    db.close()

# diverting to the admin dashboard with respective values
    return render_template(
        'admin_dash.html',
        admin=admin_data,
        total_books=counts.get('total_books', 0),
        assigned_count=counts.get('assigned', 0),
        inprocess_count=counts.get('in-process', 0),
        completed_count=counts.get('completed', 0),
        books=books,
        assigned_tickets=assigned,
        inprocess_tickets=in_process,
        completed_tickets=completed
    )

# api endpoints for routing to super-admin apis
@app.route('/superadmin_dash')
def superadmin_dashboard():
    if session.get('role') != 'superadmin':
        return redirect(url_for('login'))
        
    employee_id = session.get('user_id')
    db = get_db_connection()
    if db is None:
        return "Database Connection Error", 500
    
    cursor = db.cursor(dictionary=True)
    # fetching the relevant data based on employee_id
    admin_data = queries.get_admin_profile(cursor, employee_id)
    counts = queries.get_dashboard_counts(cursor, employee_id)
    books = queries.get_all_books_basic(cursor)
    adminstra = queries.get_all_admins(cursor)
    cust_support = queries.get_all_support(cursor)
    
    assigned = queries.get_tickets_by_status_and_admin(cursor,'assigned')
    in_process = queries.get_tickets_by_status_and_admin(cursor, 'in-process')
    completed = queries.get_tickets_by_status_and_admin(cursor, 'completed')

    cursor.close()
    db.close()

# diverting to the super-admin dashboard with respective values
    return render_template(
        'superadmin_dash.html',
        admin=admin_data,
        total_books=counts.get('total_books', 0),
        assigned_count=counts.get('assigned', 0),
        inprocess_count=counts.get('in-process', 0),
        completed_count=counts.get('completed', 0),
        books=books,
        assigned_tickets=assigned,
        inprocess_tickets=in_process,
        completed_tickets=completed,
        adminst=adminstra,
        cust_sup_team=cust_support
    )
# api endpoints for adding book by the admin
@app.route('/admin/books/add', methods=['POST'])
def admin_add_book():
    if session.get('role') not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # fetching the quantity based on book_id
        cursor.execute("SELECT quantity FROM books WHERE book_id = %s", (data['book_id'],))
        result = cursor.fetchone()
        # updating the book_quantity or inserting book into the database
        if result:
            queries.update_book_quantity(cursor, data['book_id'],data['quantity'])
        else:
            queries.insert_book(cursor, data)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        db.close()
# api endpoints for deleting a book using the book_id
@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
def admin_delete_book(book_id):
    if session.get('role') not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # deleting a book by using book_id
        queries.delete_book_by_id(cursor, book_id)
        db.commit()
        success = True
    except Exception as e:
        success = False
    finally:
        cursor.close(); db.close()
    return jsonify({'success': success})
# api endpoints for adding universities
@app.route('/admin/universities/add', methods=['POST'])
def add_university():
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # adding university into the database
    success, err = queries.add_university(cursor, data)
    if success: db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'error': err})
# api endpoints for adding departments
@app.route('/admin/departments/add', methods=['POST'])
def add_department():
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # adding departments into the database
    success, err = queries.add_department(cursor, data)
    if success: db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'error': err})
# api endpoints for adding courses
@app.route('/admin/courses/add', methods=['POST'])
def add_course():
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # adding courses into the database
    success, err = queries.add_course(cursor, data)
    if success: db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'error': err})
# api endpoints for adding instructors
@app.route('/admin/instructors/add', methods=['POST'])
def add_instructor():
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # adding instructors into the database
    success, err = queries.add_instructor(cursor, data)
    if success: db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'error': err})
# api endpoints for assigning instructors to courses
@app.route('/admin/courses/assign_instructor', methods=['POST'])
def assign_instructor():
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # assigning an instructor to the course
    success, err = queries.assign_instructor_to_course(cursor, data)
    if success: db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'error': err})
# api endpoints for assigning a book to the course
@app.route('/admin/courses/assign_book', methods=['POST'])
def assign_book():
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # assigning a book to the course
    success, err = queries.assign_book_to_course(cursor, data)
    if success: db.commit()
    cursor.close(); db.close()
    return jsonify({'success': success, 'error': err})
# api endpoints for accepting the customer support ticket by an admin
@app.route('/admin/tickets/accept/<int:ticket_id>', methods=['POST'])
def admin_accept_ticket(ticket_id):
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # accepting a ticket by the admin
    queries.accept_ticket(cursor, ticket_id, session.get('user_id'))
    db.commit()
    cursor.close(); db.close()
    return jsonify({'success': True})
# api endpoints for completing the customer support ticket by an admin
@app.route('/admin/tickets/complete/<int:ticket_id>', methods=['POST'])
def admin_complete_ticket(ticket_id):
    if session.get('role') not in ['admin', 'superadmin']: return jsonify({'success': False})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # completing a ticket by the admin
    queries.complete_ticket(cursor, ticket_id,session.get('user_id'))
    db.commit()
    cursor.close(); db.close()
    return jsonify({'success': True})
# api endpoints for adding employees by a super-admin
@app.route('/superadmin/employees/add', methods=['POST'])
def admin_add_employee():
    if session.get('role') not in ['superadmin']: return jsonify({'success': False})
    data = request.get_json()
    emp_type = data.get('type')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if emp_type == 'admin':
            # adding an admin
            queries.add_administrator(cursor, data)
        elif emp_type == 'support':
            # adding a customer support user
            queries.add_support_user(cursor, data)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close(); db.close()
# api endpoints viewing on employees by a super-admin
@app.route('/superadmin/employees/view/<string:emp_type>',methods=['GET'])
def admin_view_employees(emp_type):
    if session.get('role') not in ['superadmin']: 
        return jsonify({'success': False})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    if emp_type == 'admin':
        # fetching all the admin names
        employees = queries.get_all_admins(cursor)  
    else:
        # fetching all the customer support employees
        employees=queries.get_all_support(cursor)
    cursor.close(); db.close()
    return jsonify({'success': True, 'employees': employees})
# api endpoints for deleting an employee by a super-admin
@app.route('/superadmin/employees/delete/<string:type>/<int:u_id>', methods=['POST']) 
def superadmin_delete_user(type, u_id):
    if session.get('role') not in ['superadmin']: return jsonify({'success': False})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if type=='admin':
            # deleting an admin
            queries.delete_employee_query(cursor, u_id, 'administrators')
        else:
            # deleting a customer support employee
            queries.delete_employee_query(cursor, u_id, 'customer_support_users')
        db.commit()
        success = True
    except Exception:
        success = False
    finally:
        cursor.close(); db.close()
    return jsonify({'success': success})
# api endpoints for viewing the universities 
@app.route('/admin/view/universities',methods=['GET'])
def view_universities():
    db=get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching universities in a database
    data = queries.get_all_universities(cursor)
    cursor.close()
    db.close()
    return jsonify(data)

# api endpoints for viewing departments
@app.route('/admin/view/departments',methods=['GET'])
def view_departments():
    db=get_db_connection()
    university = request.args.get('university')
    cursor = db.cursor(dictionary=True)
    # fetching a department based on the university
    data = queries.get_departments_by_university(cursor, university)
    cursor.close()
    db.close()
    return jsonify(data)

# api endpoints for viewing the courses 
@app.route('/admin/view/courses',methods=['GET'])
def view_courses():
    db=get_db_connection()
    university = request.args.get('university')
    department = request.args.get('department')
    cursor = db.cursor(dictionary=True)
    # fetchign a course based on university and the department
    data = queries.get_courses_full(cursor, university, department)
    db.close()
    cursor.close()
    return jsonify(data)

# customer support employee apis

# api endpoints for support dashboard
@app.route('/support_dash')
def support_dashboard():
    # redirecting to the customer_support dashboard
    if session.get('role') != 'support': 
        return redirect(url_for('login'))
    return render_template('support_dash.html')

# api endpoints for viewing all the customer support tickets
@app.route('/support/tickets', methods=['GET'])
def fetch_tickets():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching all the tickets present in the database
    ans = queries.get_all_tickets(cursor)
    formatted_tickets = []
    for t in ans:
        formatted_tickets.append({
            "ticket_id": t.get("ticket_id"),
            "title": t.get("title"),
            "description": t.get("problem_description"), 
            "category": t.get("category"),
            "status": t.get("status")
        })
    cursor.close()
    db.close()
    # returning the tickets in json format
    return jsonify(formatted_tickets)

# api endpoints for creating a customer support ticket
@app.route('/support/tickets/create', methods=['POST'])
def add_ticket():
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # inserting a customer support ticket into the database
    success = queries.insert_ticket(cursor, data['title'], data['description'], data['category'],session.get('user_id'))
    if success: 
        db.commit()
    cursor.close()
    db.close()
    return jsonify({"success": success})

# api endpoints for assigning the customer support ticket to an admin
@app.route('/support/tickets/assign/<int:t_id>', methods=['POST'])
def assign_ticket(t_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # query for updating the ticket status to assigned
    success = queries.update_ticket_status(cursor, t_id,session.get('user_id'))
    if success:
        db.commit()
    cursor.close()
    db.close()
    return jsonify({"success": success})

# api endpoints for fetching th profile
@app.route('/support/profile', methods=['GET'])
def get_profile():
    user_id = session.get('user_id') 
    if not user_id:
        return jsonify({'status': 'Session missing User ID'})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # getting the user profile by the user id from the database
    user_data = queries.get_user_profile(cursor, user_id)
    db.close()
    return jsonify(user_data) if user_data else jsonify({'error': 'User not found'})
# api endpoints for accepting cancelled orders and restocking them again
@app.route('/support/orders/accept/<int:can_id>', methods=['POST'])
def accept_cancelled_order(can_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # we check the items if any are present in a cancelled_orders table in the database
        cursor.execute("SELECT book_id, quantity FROM cancelled_orders WHERE can_id = %s", (can_id,))
        item = cursor.fetchone()
        if not item:
            return jsonify({'success': False, 'message': 'Cancellation record not found'})
        # restocking the quantity back to the database
        cursor.execute(
            "UPDATE books SET quantity = quantity + %s WHERE book_id = %s",
            (item['quantity'], item['book_id'])
        )
        # deleting the restocked order from the cancelled_orders table
        cursor.execute("DELETE FROM cancelled_orders WHERE can_id = %s", (can_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Inventory restocked successfully'})

    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        db.close()
# api endpoints for cancelled-orders-list
@app.route('/support/cancelled-orders-list',methods=['GET'])
def get_cancelled_orders():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # fetching the cancelled orders in the database
    data=queries.get_cancelled_orders(cursor)
    cursor.close()
    db.close()
    return jsonify(data)

# review route apis

# api endpoints for adding the review
@app.route('/api/add-review', methods=['POST'])
def add_review():
    data = request.get_json()
    # fetching the orders
    order_id = data.get('order_id')
    book_id = data.get('book_id')
    rating = data.get('rating')
    review = data.get('review')    
    try:
        rating = float(rating)
        if rating < 1 or rating > 5:
            return jsonify({'message': 'Rating must be between 1 and 5'}), 400
            
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # adding the review and adding it to the book's review
        success = queries.add_review_and_update_order(cursor, order_id, book_id, rating, review)
        
        if success:
            db.commit()
            return jsonify({'message': 'Review submitted successfully!'})
        else:
            return jsonify({'message': 'Failed to submit review. Order might already be reviewed.'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

# main function to start the flash application on the port 5000
if __name__ == '__main__':
    app.run(debug=True, port=5000)