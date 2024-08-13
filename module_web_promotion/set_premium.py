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

def set_premium_insert():
    print("Successfully")
    if request.method == 'POST':
        data = request.json['table_data']
        try:
            connection_db = pyodbc.connect(db_test)
            cursor = connection_db.cursor()
            for item in data:
                lowest_price = item['lowest_price'] 
                highest_price = item['highest_price'] 
                optionset1 = item['optionset1'] 
                optionset2 = item['optionset2']
                optionset3 = item['optionset3'] 
                cost_installment = item['cost_installment']
                month = item['month']
                warranty = item['warranty']
                type = item['type']
                avg_p = item['avg_p']
                voucher_value = item['voucher_value']
                percent = item['percent']
                status_delete = False
                
                
                sql_query = f"""
                    INSERT INTO set_premium (lowest_price, highest_price, optionset1, optionset2, optionset3, cost_installment, month, warranty, type, avg_p, voucher_value, percent ,status_delete)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                print("cursor = ",sql_query)
                # Execute SQL query
                cursor.execute(sql_query, (lowest_price, highest_price, optionset1, optionset2, optionset3, cost_installment, month, warranty, type, avg_p, voucher_value, percent ,status_delete))
                
                # Commit เปลี่ยนแปลง
                connection_db.commit()
        except Exception as e:
            print(f"Error on item: {item}")
            print("Error:", str(e))
        finally:
            connection_db.close()  
            
        return jsonify({'message': 'Data inserted successfully'})
    return render_template('web_promotion/set_premium.html')

def set_premium_edit():
    data = request.json['table_data']
    try:
        connection_db = pyodbc.connect(db_test)
        cursor = connection_db.cursor()
        for item in data:
            try:
                id = item['id']
                lowest_price = item['lowest_price'] 
                highest_price = item['highest_price'] 
                optionset1 = item['optionset1'] 
                optionset2 = item['optionset2']
                optionset3 = item['optionset3'] 
                cost_installment = item['cost_installment']
                month = item['month']
                warranty = item['warranty']
                type = item['type']
                avg_p = item['avg_p']
                voucher_value = item['voucher_value']
                percent = item['percent']
                
                sql_query = """
                    UPDATE set_premium
                    SET lowest_price = ?, highest_price = ?, optionset1 = ?, optionset2 = ?, optionset3 = ?, cost_installment = ?, month = ?, warranty = ?, type = ?, avg_p = ?, voucher_value = ?, percent = ?
                    WHERE id = ?
                """
                cursor.execute(sql_query, (lowest_price, highest_price, optionset1, optionset2, optionset3, cost_installment, month, warranty, type, avg_p, voucher_value, percent, id))
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

def set_premium_delete():
    try:
        connection_db = pyodbc.connect(db_test)
        cursor = connection_db.cursor()
        row_id = request.form.get('id')
        
        status_delete = True
                
        sql_query = """
            UPDATE set_premium
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