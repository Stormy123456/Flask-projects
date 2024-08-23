import pyodbc
from datetime import datetime
from config_db import db_test

def log_event(connection_params, event_type, employee_code, employee_name, edit_value=None, add_value=None, del_value=None, description=""):
    try:
        # สร้างข้อความ log
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp}"

        if description:
            log_message += f" - Description: {description}"

        if add_value is not None:
            log_message += f" - Add Value: {add_value}"
        elif edit_value is not None:
            log_message += f" - Edit Value: {edit_value}"
        elif del_value is not None:
            log_message += f" - Delete Value: {del_value}"

        # ตัดทอนข้อมูลเพื่อให้แน่ใจว่าไม่เกินขนาดคอลัมน์
        event_type = event_type[:255]
        log_message = log_message[:1024]  # ตัดทอนให้เหลือไม่เกิน 1024 ตัวอักษร
        employee_code = employee_code[:255]
        employee_name = employee_name[:255]

        # แทรกข้อมูลลงในฐานข้อมูล
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO logger_edit_data (created_at, event_name, event_description, employee_code_edit, employee_name_edit) 
            VALUES (?, ?, ?, ?, ?)
         """

        cursor.execute(insert_query, (datetime.now(), event_type, log_message, employee_code, employee_name))
        connection.commit()  # บันทึกการเปลี่ยนแปลง

        # บันทึกข้อมูลลงไฟล์ log (optional)
        print(log_message)

    except Exception as error:
        print(f"Failed to log event: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()
