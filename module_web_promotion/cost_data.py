from flask import Flask, render_template, request, redirect, Response, jsonify, send_file, session, flash
from datetime import datetime, timedelta, time
from config_db import db_test, connection_string
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import Font, Border, Side
import pyodbc 
import pandas as pd
import ast
import sys
import codecs

def stock_qty():
    product_id = request.json.get('product_id')
    remaining_qty = 0
    try:
        connection_odoo = pyodbc.connect(connection_string)
        cursor = connection_odoo.cursor()
        sql_query = """
            SELECT sum(sq.available_quantity) as remaining_qty
            FROM stock_quant sq
            JOIN product_product pp ON pp.id = sq.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pt.id = ?
            GROUP BY pt.name
        """
        cursor.execute(sql_query, (product_id,))
        result = cursor.fetchone()
        if result:
            remaining_qty = result.remaining_qty
    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูล Odoo ไม่สำเร็จ:", str(e))
    finally:
        connection_odoo.close()  # ปิด Connection
    return jsonify({'remaining_qty': remaining_qty})


def cost_insert():
    print("Successfully")
    if request.method == 'POST':
        data = request.json['table_data']
        try:
            connection_db = pyodbc.connect(db_test)
            cursor = connection_db.cursor()
            for item in data:
                start = item['start'] 
                end = item['end'] 
                brand = item['brand'] 
                model_sku = item['model_sku']
                price_rrp = item['price_rrp'] 
                margin = item['margin']
                cost_b = item['cost_b']
                timestamp = datetime.now()
                status = item['status']
                status_cost = item['status_cost'] 
                stock_qty = item['stock_qty'] 
                status_delete = False
                sql_query = f"""
                    INSERT INTO cost_and_status (start, "end", brand, model_sku, price_rrp, margin, cost_b, timestamp, status, status_cost, stock_qty, status_delete)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                print("cursor = ",sql_query)
                # Execute SQL query
                cursor.execute(sql_query, (start, end, brand, model_sku, price_rrp, margin, cost_b, timestamp, status, status_cost, stock_qty, status_delete))
                
                # Commit เปลี่ยนแปลง
                connection_db.commit()
        except Exception as e:
            print(f"Error on item: {item}")
            print("Error:", str(e))
        finally:
            connection_db.close()  
            
        return jsonify({'message': 'Data inserted successfully'})
    return render_template('web_promotion/cost_and_status.html')

def cost_edit():
    data = request.json['table_data']
    try:
        connection_db = pyodbc.connect(db_test)
        cursor = connection_db.cursor()
        for item in data:
            try:
                id = item['id']
                start = item['start']
                end = item['end']
                brand = item['brand']
                model_sku = item['model_sku']
                price_rrp = item['price_rrp']
                margin = item['margin']
                cost_b = item['cost_b']
                status = item['status']
                status_cost = item['status_cost']
                stock_qty = item['stock_qty']
                sql_query = """
                    UPDATE cost_and_status
                    SET start = ?, "end" = ?, brand = ?, model_sku = ?, price_rrp = ?, margin = ?, cost_b = ?, status = ?, status_cost = ?, stock_qty = ?
                    WHERE id = ?
                """
                cursor.execute(sql_query, (start, end, brand, model_sku, price_rrp, margin, cost_b, status, status_cost, stock_qty, id))
                connection_db.commit()
            except KeyError as e:
                print(f"Missing key in item: {item}, KeyError: {e}")
            except Exception as e:
                print(f"Error on item: {item}, Error: {e}")
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection_db.close()

    return jsonify({'message': 'Data updated successfully'})

def cost_delete():
    try:
        connection_db = pyodbc.connect(db_test)
        cursor = connection_db.cursor()
        row_id = request.form.get('id')
        
        status_delete = True
                
        sql_query = """
            UPDATE cost_and_status
            SET status_delete = ?
            WHERE id = ?
        """
        cursor.execute(sql_query, (status_delete, row_id))
        connection_db.commit()
    except Exception as e:
        print(f"Error on item: {row_id}")
        print("Error:", str(e))
        return jsonify({'message': f"An error occurred: {str(e)}"}), 500
    finally:
        connection_db.close()
        
    return jsonify({'message': 'Row deleted successfully'})