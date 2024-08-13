from flask import Flask, render_template, request, session
from datetime import datetime
from config_db import connection_string_invoice
import pyodbc 

def log_users(Type_name,Activity):
    try:
        connection_log = pyodbc.connect(connection_string_invoice)
        cursor_log = connection_log.cursor()
        emp_code = session['employee_code']
        emp_name = session['emplyee_name']
        type_name = Type_name
        activity = Activity
        date_time = datetime.now()
        sql_query = f"""
            INSERT INTO employee_activities (emp_code, emp_name, type_name, activity, date_time)
            VALUES (?, ?, ?, ?, ?)
        """
        # Execute SQL query
        cursor_log.execute(sql_query, (emp_code, emp_name, type_name, activity, date_time))
        # Commit เปลี่ยนแปลง
        connection_log.commit()
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection_log.close()   