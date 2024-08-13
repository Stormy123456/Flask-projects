from flask import Flask, render_template, request, redirect, session, url_for, flash
from config_db import connection_string, connection_string_invoice
import pyodbc 

def user_permission_check(menu_id):
    user_groups = []
    try:
        connection_menu1 = pyodbc.connect(connection_string_invoice)
        cursor_menu1 = connection_menu1.cursor()
        sql_query = """
                    SELECT
                        tp.id_user_group AS id
                    FROM  
                        table_permission tp
                    WHERE
                        tp.id_menu_page = ?
                    """
        cursor_menu1.execute(sql_query, menu_id)
        result = cursor_menu1.fetchall()
        user_groups = [{
                    'id': str(item.id)
                } for item in result]
    except Exception as e:
        print("Data Error:", str(e))
    finally:
        connection_menu1.close()
    if 'employee_code' in session and session['employee_code'] != 'Unknow':
        employee_group_id_str = str(session['employee_group_id'])
        if any(group['id'] == employee_group_id_str for group in user_groups):
            return True
        else:
            flash('คุณไม่ได้รับอนุญาติให้เข้าถึงหน้าเว็ปนี้!!!')
            return redirect(request.referrer)
    else:
        return redirect('https://app01.tgfone.com/demo_saleforcase/')
    
    
    
def config_page():
    user_group = []
    user_group_checked = []
    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        sql_query = f"""
                        select
                            rug.id as id,
                            rug.name as name
                        FROM  
                            res_user_group rug
            """
        cursor.execute(sql_query)
        result = cursor.fetchall()
        user_group = [{
                    'id': str(item.id),
                    'name': str(item.name)
                } for item in result]
    except Exception as e:
        print("Data Error:", str(e))
    finally:
        connection.close()  # ปิด Connection
    
    try:
        connection_menu1 = pyodbc.connect(connection_string_invoice)
        cursor_menu1 = connection_menu1.cursor()
        sql_query = f"""
                        select
                            tp.id_user_group as id,
                            tp.id_menu_page as id_menu_page
                        FROM  
                            table_permission tp
            """
        cursor_menu1.execute(sql_query)
        result = cursor_menu1.fetchall()
        user_group_checked = [{
                    'id': str(item.id),
                    'id_menu_page': str(item.id_menu_page)
                } for item in result]
    except Exception as e:
        print("Data Error:", str(e))
    finally:
        connection_menu1.close()  # ปิด Connection
    return render_template('log_activity/config_auth.html',user_group=user_group,user_group_checked=user_group_checked)

def add_permissions_spautomate():
    selected_permissions = request.form.getlist('items')
    try:
        connection = pyodbc.connect(connection_string_invoice)
        cursor = connection.cursor()
        sql_delete_query = "DELETE FROM table_permission WHERE id_menu_page = 1"
        cursor.execute(sql_delete_query)
        for item in selected_permissions:
            id_user_group = item
            id_menu_page = 1
            # สร้างคำสั่ง SQL สำหรับแทรกข้อมูลลงในฐานข้อมูล
            sql_query = f"""
                INSERT INTO table_permission (id_user_group, id_menu_page)
                VALUES (?, ?)
            """
            # Execute SQL query
            cursor.execute(sql_query, (id_user_group, id_menu_page))
        # Commit เปลี่ยนแปลง
        connection.commit()
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection.close()
    return redirect(url_for('config_auth'))

def add_permissions_pos_data():
    selected_permissions = request.form.getlist('items2')
    try:
        connection = pyodbc.connect(connection_string_invoice)
        cursor = connection.cursor()
        sql_delete_query = "DELETE FROM table_permission WHERE id_menu_page = 2"
        cursor.execute(sql_delete_query)
        for item in selected_permissions:
            id_user_group = item
            id_menu_page = 2
            # สร้างคำสั่ง SQL สำหรับแทรกข้อมูลลงในฐานข้อมูล
            sql_query = f"""
                INSERT INTO table_permission (id_user_group, id_menu_page)
                VALUES (?, ?)
            """
            # Execute SQL query
            cursor.execute(sql_query, (id_user_group, id_menu_page))
        # Commit เปลี่ยนแปลง
        connection.commit()
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection.close()
    return redirect(url_for('config_auth'))

def add_permissions_etax():
    selected_permissions = request.form.getlist('items3')
    try:
        connection = pyodbc.connect(connection_string_invoice)
        cursor = connection.cursor()
        sql_delete_query = "DELETE FROM table_permission WHERE id_menu_page = 3"
        cursor.execute(sql_delete_query)
        for item in selected_permissions:
            id_user_group = item
            id_menu_page = 3
            # สร้างคำสั่ง SQL สำหรับแทรกข้อมูลลงในฐานข้อมูล
            sql_query = f"""
                INSERT INTO table_permission (id_user_group, id_menu_page)
                VALUES (?, ?)
            """
            # Execute SQL query
            cursor.execute(sql_query, (id_user_group, id_menu_page))
        # Commit เปลี่ยนแปลง
        connection.commit()
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection.close()
    return redirect(url_for('config_auth'))

def add_permissions_texcom():
    selected_permissions = request.form.getlist('items4')
    try:
        connection = pyodbc.connect(connection_string_invoice)
        cursor = connection.cursor()
        sql_delete_query = "DELETE FROM table_permission WHERE id_menu_page = 4"
        cursor.execute(sql_delete_query)
        for item in selected_permissions:
            id_user_group = item
            id_menu_page = 4
            # สร้างคำสั่ง SQL สำหรับแทรกข้อมูลลงในฐานข้อมูล
            sql_query = f"""
                INSERT INTO table_permission (id_user_group, id_menu_page)
                VALUES (?, ?)
            """
            # Execute SQL query
            cursor.execute(sql_query, (id_user_group, id_menu_page))
        # Commit เปลี่ยนแปลง
        connection.commit()
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection.close()
    return redirect(url_for('config_auth'))