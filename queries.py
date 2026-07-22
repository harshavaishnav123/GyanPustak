from datetime import datetime, timedelta

# authentication of a user with their username and password
def check_user_credentials(cursor, username, password):
    # certainly in our implementation username and password must be same
    if username != password:
        return {"success": False}

    # fetching the query for searching username in the database
    cursor.execute("SELECT * FROM student_users WHERE student_id = %s ", (username,))

    # if the cursor returns the role as a student then it is diverted to student's page
    student = cursor.fetchone()
    if student:
        return {"success": True, "role": "student", "data": student}

    # if the cursor returns the role as a customer support user then it is diverted to customer support user's page
    cursor.execute("SELECT * FROM customer_support_users WHERE employee_id = %s ", (username,))
    employee = cursor.fetchone()
    if employee:
        return {"success": True, "role": "support", "data": employee}

    # if the cursor returns the role as a super admin then it is diverted to super admin's page    
    cursor.execute("SELECT * FROM administrators WHERE employee_id = %s AND first_name='Super' ", (username,))
    employee = cursor.fetchone()
    if employee:
        return {"success": True, "role": "superadmin", "data": employee}
        
    # if the cursor returns the role as an admin then it is diverted to admin's page
    cursor.execute("SELECT * FROM administrators WHERE employee_id = %s", (username,))
    employee = cursor.fetchone()
    if employee:
        return {"success": True, "role": "admin", "data": employee}

    return {"success": False}


# student queries in the explore page
def explore_db(cursor, data):
    uni_name = data.get('university')
    dept_name = data.get('department')
    course_name = data.get('course')
    # based on the university,department and course name we make a query for searching recomended books in database
    query = """
       SELECT 
        b.book_id, 
        b.title, 
        b.rating, 
        b.price, 
        GROUP_CONCAT(DISTINCT ba.author_name SEPARATOR ', ') AS authors
        FROM books b
        JOIN courses_books bc ON b.book_id = bc.book_id
        JOIN courses c ON bc.course_id = c.course_id
        JOIN departments d ON c.department_id = d.department_id
        JOIN universities u ON d.university_id = u.university_id
        LEFT JOIN book_author ba ON b.book_id = ba.book_id
        WHERE u.name = %s 
        AND d.department_name = %s 
        AND c.course_name = %s
        GROUP BY b.book_id;
    """
    cursor.execute(query, (uni_name, dept_name, course_name))
    books = cursor.fetchall()
    if not books:
        return False, 'Verification failed: Course details do not match our records.'
    return True, books

# function to search books in the database
def search_books_in_db(cursor, search_term):
    book_ids = set()
    search_pattern = f"%{search_term}%"
    # searching based on book's title and category
    cursor.execute("SELECT book_id FROM books WHERE title LIKE %s OR category LIKE %s", 
                   (search_pattern, search_pattern))
    book_ids.update([row['book_id'] for row in cursor.fetchall()])
    # searching based on keywords present in the books
    cursor.execute("SELECT book_id FROM book_keywords WHERE keywords LIKE %s", (search_pattern,))
    book_ids.update([row['book_id'] for row in cursor.fetchall()])
    # searching based on the author name of the book
    cursor.execute("SELECT book_id FROM book_author WHERE author_name LIKE %s", (search_pattern,))
    book_ids.update([row['book_id'] for row in cursor.fetchall()])
    # searching based on the subcategory of the book
    cursor.execute("SELECT book_id FROM book_subcategory WHERE subcategory LIKE %s", (search_pattern,))
    book_ids.update([row['book_id'] for row in cursor.fetchall()])
    if not book_ids:
        return []
    format_strings = ','.join(['%s'] * len(book_ids))
    # using group_concat to get all authors for the search
    query = f"""
        SELECT b.book_id, b.title, b.rating, b.price, 
               GROUP_CONCAT(ba.author_name SEPARATOR ', ') as authors
        FROM books b
        LEFT JOIN book_author ba ON b.book_id = ba.book_id
        WHERE b.book_id IN ({format_strings})
        GROUP BY b.book_id
        
    """
    cursor.execute(query, tuple(book_ids))
    return cursor.fetchall()


# function for adding item into the cart
def add_item_to_cart(cursor, student_id, id, price):
    # fetching the current date and time
    current_date = datetime.now().strftime("%Y-%m-%d")
    # adding a book into the cart for a student id
    try:
        query = "INSERT INTO cart (student_id, book_id, price, date_created,quantity) VALUES (%s, %s, %s, %s,%s)"
        cursor.execute(query, (student_id, id, price, current_date,1))
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False

# function for updating the cart quantity
def update_cart_quantity(cursor,book_id,student_id):
    # updating the cart quantity in the database
    sql = "UPDATE cart SET quantity = quantity +1 WHERE book_id = %s and student_id=%s"
    cursor.execute(sql, (book_id,student_id))
    return True

# function for displaying the student's cart
def get_student_cart(cursor, student_id):
    # fetching the student's cart in the database
    query = """
        SELECT 
        c.cart_id, c.quantity AS cart_quantity, b.book_id, b.title, 
        b.price as price,  b.quantity AS stock_quantity  
        FROM cart c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.student_id = %s
    """
    cursor.execute(query, (student_id,))
    ans=cursor.fetchall()
    return ans

# function to process the checkout
def process_checkout(cursor, student_id, cart_items, pay):
    try:
        for item in cart_items:
            # validating the stock if present or not
            if item['cart_quantity'] > item['stock_quantity']:
                return {'success': False, 'message': f"Stock ran out for {item['title']}"}
            
            # inserting into the orders table
            query = """
                INSERT INTO orders (student_id, book_id, quantity, price, shipping_type, 
                                   card_holder_name, credit_card_number, credit_card_expiry,status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
            """
            cursor.execute(query, (
                student_id, item['book_id'], item['cart_quantity'], item['price'],
                pay.get('shipping_type'), pay.get('card_holder_name'),
                pay.get('credit_card_number'), pay.get('credit_card_expiry'),'inprocess'
            ))

            # decreasing the quantity from the database for the book student has bought
            cursor.execute(
                "UPDATE books SET quantity = quantity - %s WHERE book_id = %s",
                (item['cart_quantity'], item['book_id'])
            )
            
        # clearing the cart since we are processing the whole checkout of the cart
        cursor.execute("DELETE FROM cart WHERE student_id = %s", (student_id,))
        return {'success': True}
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False, 'message': str(e)}

# function for removing an element from the cart
def delete_cart_item(cursor, cart_id, student_id):
    # deleting from the cart
    query = "DELETE FROM cart WHERE cart_id = %s AND student_id = %s"
    try:
        cursor.execute(query, (cart_id, student_id))
        return True
    except Exception as e:
        return False

# function for fetching orders with student id
def get_student_orders(cursor, student_id):
    
    # added is_reviewed to the query to disable buttons on load
    query = """
        SELECT order_id as id, date_created as full_timestamp, 
               DATE_FORMAT(date_created, '%%d %%b %%Y, %%H:%%i') as date, 
               book_id, status, quantity, IFNULL(is_reviewed, 0) as is_reviewed
        FROM orders 
        WHERE student_id = %s 
        ORDER BY date_created DESC
    """
    cursor.execute(query, (student_id,))
    raw_orders = cursor.fetchall()
    
    for order in raw_orders:
        cursor.execute("SELECT title FROM books WHERE book_id = %s", (order['book_id'],))
        book = cursor.fetchone()
        order['items'] = [book['title']] if book else ["Unknown Book"]
        # ensuring timestamp is in iso format for js Date object
        if isinstance(order['full_timestamp'], datetime):
            order['full_timestamp'] = order['full_timestamp'].isoformat()
            
    return raw_orders

# function for deleting orders 
def delete_order_if_recent(cursor, order_id, student_id):
    # fetching the order details for a particular student
    cursor.execute("""
        SELECT book_id, quantity, date_created, status 
        FROM orders WHERE order_id = %s AND student_id = %s
    """, (order_id, student_id))
    order = cursor.fetchone()

    if not order or order['status'] == 'cancelled':
        return False, "Order not found or already cancelled."

    # verifying the cancellation request is within 2 minutes window
    created_at = order['date_created']
    if datetime.now() - created_at > timedelta(seconds=120):
        return False, "Cancellation window (2 mins) has expired."

    try:
        # updating the status of the order to cancelled
        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = %s", (order_id,))

        cursor.execute("""
            INSERT INTO cancelled_orders (book_id, quantity, order_id)
            VALUES (%s, %s, %s)
        """, (order['book_id'], order['quantity'], order_id))

        return True, "Order cancelled. Your amount will be refunded shortly."
    except Exception as e:
        return False, str(e)

# function for getting the student profile
def get_student_profile(cursor, student_id):
    # fetching the required info in the database
    cursor.execute("""SELECT s.student_id,s.first_name,
                   s.last_name,s.email,s.phone_number,
                   s.address,s.date_of_birth,u.name,d.department_name,
                   s.student_status,s.current_year
                   FROM student_users as s
                   join universities as u on u.university_id=s.university_id
                   join departments as d on d.department_id=s.department_id
                   WHERE s.student_id=%s""", (student_id,))
    return cursor.fetchone()

# function for getting the student username
def get_student_username(cursor, id):
    # fetching the name of the student in the database
    cursor.execute("SELECT first_name FROM student_users WHERE student_id=%s", (id,))
    user_name = cursor.fetchone()
    return user_name['first_name'] if user_name else None

# function for inserting into the trouble tickets
def insert_ticket(cursor, title, ticket_type, description, student_id):
    current_date = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_name = get_student_username(cursor, student_id)
    new_history_entry = f"\n[{timestamp}] Ticket created by {user_name}"
    query = """INSERT INTO trouble_tickets 
               (category, date_logged, created_by, title, problem_description, status, status_history) 
               VALUES (%s, %s, %s, %s, %s, 'new', %s)"""
    try:
        # inserting the trouble ticket into the database
        cursor.execute(query, (ticket_type, current_date, user_name, title, description, new_history_entry))
        return True
    except Exception as e:
        return False

# function for listing the trouble tickets raised by a particular student
def get_student_tickets(cursor, student_id):
    # fetching trouble tickets for the student in the database
    cursor.execute("SELECT * FROM trouble_tickets WHERE created_by = %s ORDER BY ticket_id ASC", (student_id,))
    return cursor.fetchall()

# function for getting admin profile
def get_admin_profile(cursor, employee_id):
    # fetching in the database for the info related to the admin
    cursor.execute("SELECT * FROM administrators WHERE employee_id = %s", (employee_id,))
    return cursor.fetchone()

# function for getting the customer support user's profile
def get_user_profile(cursor, employee_id):
    # fetching in the database for the info related to the customer support users
    cursor.execute("SELECT * FROM customer_support_users WHERE employee_id = %s", (employee_id,))
    return cursor.fetchone()

# function for getting the dashboard counts 
def get_dashboard_counts(cursor, employee_id):
    counts = {}
    # fetching count in the database
    cursor.execute("SELECT COUNT(*) AS c FROM books")
    book_result = cursor.fetchone()
    counts['total_books'] = book_result['c'] if book_result else 0
    for status in ['in-process', 'completed']:
        # fetching the trouble tickets with status of in-process and completed
        cursor.execute("SELECT COUNT(*) AS c FROM trouble_tickets WHERE status=%s ", (status,))
        res = cursor.fetchone()
        counts[status] = res['c'] if res else 0
    # fetching count of trouble tickets that have status of assigned
    cursor.execute("SELECT COUNT(*) AS c FROM trouble_tickets WHERE status='assigned'")
    res = cursor.fetchone()
    counts['assigned'] = res['c'] if res else 0
    return counts

# function for getting all the trouble tickets 
def get_all_tickets(cursor):
    # fetching the trouble tickets in the database
    cursor.execute("SELECT * FROM trouble_tickets ORDER BY ticket_id DESC")
    return cursor.fetchall()

# function for returning trouble ticket with ticket id
def get_ticket_by_id(cursor, ticket_id):
    # fetching the required ticket in the database
    cursor.execute("SELECT * FROM trouble_tickets WHERE ticket_id=%s", (ticket_id,))
    return cursor.fetchone()

# function for getting trouble tickets based on status and admin
def get_tickets_by_status_and_admin(cursor, status):
    # fetching the required ticket in the database
    cursor.execute("SELECT * FROM trouble_tickets WHERE status=%s ", (status,))
    return cursor.fetchall()

# function for accepting ticket by a customer support user and assigning it to an admin
def accept_ticket(cursor, ticket_id, user_name):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history_entry = f"\n[{timestamp}] Status updated to 'in-process' by {user_name}"
    # updating the trouble ticket's status to in-process in the database
    query = """UPDATE trouble_tickets SET status = 'in-process', 
               status_history = CONCAT(IFNULL(status_history, ''), %s), resolved_by=%s 
               WHERE ticket_id = %s"""
    try:
        cursor.execute(query, (new_history_entry, user_name, ticket_id))
        return True, "Ticket updated successfully!"
    except Exception as e:
        return False, str(e)

# function for completing the ticket
def complete_ticket(cursor, ticket_id, user_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # updating the trouble ticket's status to completed in the database
    query = "UPDATE trouble_tickets SET status = 'completed', status_history = CONCAT(IFNULL(status_history, ''), %s) WHERE ticket_id = %s"
    try:
        cursor.execute(query, (timestamp, ticket_id))
        return True, "Ticket updated successfully!"
    except Exception as e:
        return False, str(e)

# function for updating ticket's status
def update_ticket_status(cursor, t_id, user_name):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history_entry = f"\n[{timestamp}] Status updated to 'assigned' by {user_name}"
    # updating the status to assigned in the database
    query = "UPDATE trouble_tickets SET status = 'assigned', status_history = CONCAT(IFNULL(status_history, ''), %s) WHERE ticket_id = %s"
    try:
        cursor.execute(query, (new_history_entry, t_id))
        return True
    except Exception as e:
        return False

# function for getting cancelled orders
def get_cancelled_orders(cursor):
    # fetching the cancelled orders in the database
    query = """
        SELECT c.can_id, c.book_id, c.quantity, c.order_id, b.title 
        FROM cancelled_orders c
        JOIN books b ON c.book_id = b.book_id
    """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

# function for getting all admins
def get_all_admins(cursor):
    # fetching the admins in the database
    cursor.execute("SELECT * FROM administrators where first_name!=%s",("Super",))
    return cursor.fetchall()

# function for getting customer support users
def get_all_support(cursor):
    # fetching the customer support users in the database
    cursor.execute("SELECT * FROM customer_support_users")
    return cursor.fetchall()

# function for adding the admin
def add_administrator(cursor, d):
    # inserting the admin into the database
    sql = """INSERT INTO administrators 
             (employee_id, first_name, last_name, gender, salary, aadhaar_number, email, address, phone_number)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    vals = (d['employee_id'], d['first_name'], d['last_name'], d['gender'], d['salary'], d['aadhaar_number'], d['email'], d['address'], d['phone_number'])
    cursor.execute(sql, vals)

# function for adding a customer support user
def add_support_user(cursor, d):
    # inserting the customer support user into the database
    sql = """INSERT INTO customer_support_users 
             (employee_id, first_name, last_name, gender, salary, aadhaar_number, email, address, phone_number)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    vals = (d['employee_id'], d['first_name'], d['last_name'], d['gender'], d['salary'], d['aadhaar_number'], d['email'], d['address'], d['phone_number'])
    cursor.execute(sql, vals)
   
# function for deleting employee
def delete_employee_query(cursor, emp_id, table_name):
    # deleting the employee from the database
    cursor.execute(f"DELETE FROM {table_name} WHERE employee_id = %s", (emp_id,))

# function for getting all books
def get_all_books_basic(cursor):
    # fetching books from the database
    cursor.execute("SELECT book_id, title, isbn FROM books")
    return cursor.fetchall()

# function for updating the book quantity
def update_book_quantity(cursor, book_id,qua):
    # updating the quantity in the database
    sql = "UPDATE books SET quantity = quantity + %s WHERE book_id = %s"
    cursor.execute(sql, (qua,book_id))

# function for inserting sub-category
def insert_sub(cursor,book_id,s,tab_name,col_name):
    if not s:
        return
    st = {x.strip() for x in s.split(",") if x.strip()}
    for x in st:
      # inserting sub-category into the database
      query=f"Insert into {tab_name} (book_id,{col_name}) values(%s,%s)"
      cursor.execute(query,(book_id,x))

# function for inserting book
def insert_book(cursor, d):
    # inserting into the books table
    sql = """INSERT INTO books 
             (book_id, title, isbn, publisher, publication_date, 
             edition, language, format, book_type, purchase_option, 
             price, rating,quantity,category) 
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    vals = (
        d.get('book_id'), d.get('title'), d.get('isbn'),
        d.get('publisher'), d.get('publication_date'), d.get('edition'), 
        d.get('language'), d.get('format'), d.get('book_type'), 
        d.get('purchase_option'), d.get('price'), d.get('rating'),d.get('quantity'),d.get('category')
    )
    cursor.execute(sql, vals)
    insert_sub(cursor,d.get('book_id'),d.get('subcategory',''),'book_subcategory','subcategory')
    insert_sub(cursor,d.get('book_id'),d.get('keywords',''),'book_keywords','keywords')
    insert_sub(cursor,d.get('book_id'),d.get('authors',''),'book_author','author_name')
    
# function for deleting book by id
def delete_book_by_id(cursor, book_id):
    # deleting from the table from the database
    cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))

# function for adding university
def add_university(cursor, data):
    # inserting the university into the database
    query = """INSERT INTO universities (university_id, name, address, rep_first_name, 
               rep_last_name, rep_email, rep_phone) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    try:
        cursor.execute(query, (data['university_id'], data['name'], data.get('address'),
            data.get('rep_first_name'), data.get('rep_last_name'),
            data.get('rep_email'), data.get('rep_phone')))
        return True, "University created!"
    except Exception as e:
        return False, str(e)

# function for adding department
def add_department(cursor, data):
    # inserting the department into the database
    query = "INSERT INTO departments (department_id, department_name, university_id) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (data['department_id'], data['department_name'], data['university_id']))
        return True, "Department linked!"
    except Exception as e:
        return False, "Error: Check University ID."

# function for adding course
def add_course(cursor, data):
    # inserting the course in the database
    query = "INSERT INTO courses (course_id, course_name, university_id, department_id, year, semester) VALUES (%s, %s, %s, %s, %s, %s)"
    try:
        cursor.execute(query, (data['course_id'], data['course_name'], data['university_id'], data['department_id'], data['year'], data['semester']))
        return True, "Course linked!"
    except Exception as e:
        return False, "Error: Check Department ID."

# function for adding instructor
def add_instructor(cursor, data):
    # inserting the instructor into the database
    query = "INSERT INTO instructors (instructor_id, first_name, last_name, university_id, department_id) VALUES (%s, %s, %s, %s, %s)"
    try:
        cursor.execute(query, (data['instructor_id'], data['first_name'], data['last_name'], data.get('univ'), data.get('dept')))
        return True, "Instructor added!"
    except Exception as e:
        return False, str(e)

# function for assigning instructor to a course
def assign_instructor_to_course(cursor, data):
    try:
        # inserting the mapping of an instructor to a course in the database
        cursor.execute("INSERT INTO inst_courses (instructor_id, course_id) VALUES (%s, %s)", (data['instructor_id'], data['course_id']))
        return True, "Assigned Instructor!"
    except Exception as e:
        return False, str(e)

# function for assigning book to a course
def assign_book_to_course(cursor, data):
    try:
        # inserting the mapping of a book to a course in the database
        cursor.execute("INSERT INTO courses_books (book_id, course_id) VALUES (%s, %s)", (data['book_id'], data['course_id']))
        return True, "Assigned Book!"
    except Exception as e:
        return False, str(e)

# function for getting all univerisities
def get_all_universities(cursor):
    # fetching for all the universities
    cursor.execute("""
        SELECT university_id,name,address
        FROM universities
    """)
    return cursor.fetchall()

# function for getting departments by university
def get_departments_by_university(cursor, university):
    # fetching for departments in database
    cursor.execute("""
        SELECT d.department_id, d.department_name
        FROM departments d
        JOIN universities u ON d.university_id = u.university_id
        WHERE u.name = %s
    """, (university,))
    return cursor.fetchall()

# function for getting courses 
def get_courses_full(cursor, university, department):
    # fetching by university,department for courses in the database
    cursor.execute("""
        SELECT 
            c.course_name,
            GROUP_CONCAT(DISTINCT b.title) AS books,
            GROUP_CONCAT(DISTINCT CONCAT(i.first_name, ' ', i.last_name)SEPARATOR ', ') AS instructors
        FROM courses c
        JOIN departments d ON c.department_id = d.department_id
        JOIN universities u ON c.university_id = u.university_id
        LEFT JOIN courses_books cb ON c.course_id = cb.course_id
        LEFT JOIN books b ON cb.book_id = b.book_id
        LEFT JOIN inst_courses ci ON c.course_id = ci.course_id
        LEFT JOIN instructors i ON ci.instructor_id = i.instructor_id
        WHERE u.name = %s AND d.department_name = %s
        GROUP BY c.course_id
    """, (university, department))
    return cursor.fetchall()

# function for adding reviews and restocking the order
def add_review_and_update_order(cursor, order_id, book_id, rating, review_text):
    try:
        # inserting review into the database
        cursor.execute("""
            INSERT INTO reviews (book_id, rating, review_text)
            VALUES (%s, %s, %s)
        """, (book_id, rating, review_text))
        # restocking the order back into the database
        cursor.execute("""
            UPDATE orders 
            SET is_reviewed = TRUE 
            WHERE order_id = %s
        """, (order_id,))
        # updating the rating for the book in the database
        cursor.execute("""
            UPDATE books 
            SET rating=(rating+%s)/2.0
            WHERE book_id = %s
        """, (rating,book_id,))
        return True
    except Exception as e:
        print("Error saving anonymous review:", e)
        return False

# function for getting review status
def get_orders_with_review_status(cursor, user_id):
    # fetching the review status from table in the database
    query = """
    SELECT o.*, 
           CASE 
               WHEN r.review_id IS NOT NULL THEN TRUE 
               ELSE FALSE 
           END AS is_reviewed
    FROM orders o
    LEFT JOIN reviews r ON o.book_id = r.book_id
    WHERE o.user_id = %s
    """
    cursor.execute(query, (user_id,))
    return cursor.fetchall()