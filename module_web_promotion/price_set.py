from flask import Flask, render_template, request, redirect, Response, jsonify, send_file, session, flash
from datetime import datetime, timedelta, time
from config_db import db_test
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import Font, Border, Side
import pyodbc 
import pandas as pd
import ast
import sys
import codecs
from module_web_promotion.log_edit_data import log_event

def add_data():
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()
        for _ in range(10):
            sql_query = """INSERT INTO price_set DEFAULT VALUES"""
            cursor.execute(sql_query)
        connection.commit()
        new_id = cursor.execute("SELECT @@IDENTITY AS id").fetchone().id
    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
        return jsonify({'success': False, 'message': str(e)})
    finally:
        connection.close()  # ปิด Connection
    return jsonify({'success': True, 'id': new_id})

def update_data(id):
    column = request.form['column']
    value = request.form['value']
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()
        sql_query = f"UPDATE price_set SET {column} = ? WHERE id = ?"
        cursor.execute(sql_query, (value, id))
        connection.commit()
        
        log_event(connection_params=connection, event_type='update_data_price_set', employee_code=session['employee_code'], employee_name=session['name_user'], new_value={value, id}, description="Updated update data price set")
    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
        return jsonify({'success': False, 'message': str(e)})
    finally:
        connection.close()  # ปิด Connection
    return jsonify({'success': True})

def delete_data(id):
    try:
        # เชื่อมต่อฐานข้อมูล
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()

        # ดึงชื่อคอลัมน์ทั้งหมดจากตาราง
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'price_set' AND column_name != 'id'")
        columns = cursor.fetchall()

        # สร้างรายการชื่อคอลัมน์
        column_names = [col[0] for col in columns]

        # สร้างคำสั่ง SQL สำหรับการอัปเดตค่าว่าง
        set_clause = ", ".join([f"{col} = ''" for col in column_names])
        sql_query = f"UPDATE price_set SET {set_clause} WHERE id = ?"

        # ใช้คำสั่ง SQL อัปเดต
        cursor.execute(sql_query, (id,))
        connection.commit()

    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
        return jsonify({'success': False, 'message': str(e)})
    
    finally:
        connection.close()  # ปิดการเชื่อมต่อ

    return jsonify({'success': True})