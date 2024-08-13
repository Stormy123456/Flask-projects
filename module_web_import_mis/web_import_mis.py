from flask import Flask, request, render_template, redirect, flash
from config_db import connection_string_invoice
from datetime import datetime
import pandas as pd
import os
import pyodbc 

def insert_data_to_pgsql(data_list):
    try:
        connection_invoice = pyodbc.connect(connection_string_invoice)
        cursor = connection_invoice.cursor()
        for item in data_list:
            if isinstance(item[0], datetime):
                day_date = str(item[0].strftime("%m/%d/%Y"))
            else:
                day_date = str(item[0])
            transfer_from_code = item[1] if item[1] is not None and not pd.isna(item[1]) and item[1] != '' else ' '
            item_code = item[2] if item[2] is not None and not pd.isna(item[2]) and item[2] != '' else ' '
            full_description = item[3] if item[3] is not None and not pd.isna(item[3]) and item[3] != '' else ' '
            inventory_posting_group = item[4] if item[4] is not None and not pd.isna(item[4]) and item[4] != '' else ' '
            cat2 = item[5] if item[5] is not None and not pd.isna(item[5]) and item[5] != '' else ' '
            brand = item[6] if item[6] is not None and not pd.isna(item[6]) and item[6] != '' else ' '
            branch = item[7] if item[7] is not None and not pd.isna(item[7]) and item[7] != '' else ' '
            branch_name = item[8] if item[8] is not None and not pd.isna(item[8]) and item[8] != '' else ' '
            area_manager = item[9] if item[9] is not None and not pd.isna(item[9]) and item[9] != '' else ' '
            sales_support = item[10] if item[10] is not None and not pd.isna(item[10]) and item[10] != '' else ' '
            zone = item[11] if item[11] is not None and not pd.isna(item[11]) and item[11] != '' else ' '
            pickup_date = item[12] if item[12] is not None and not pd.isna(item[12]) and item[12] != '' else ' '
            branch_arrival_date = item[13] if item[13] is not None and not pd.isna(item[13]) and item[13] != '' else ' '
            location_group_code = item[14] if item[14] is not None and not pd.isna(item[14]) and item[14] != '' else ' '
            _28_days_sales = item[15] if item[15] is not None and not pd.isna(item[15]) and item[15] != '' else ' '
            _21_days_sales = item[16] if item[16] is not None and not pd.isna(item[16]) and item[16] != '' else ' '
            _14_days_sales = item[17] if item[17] is not None and not pd.isna(item[17]) and item[17] != '' else ' '
            _7_days_sales = item[18] if item[18] is not None and not pd.isna(item[18]) and item[18] != '' else ' '
            make_up_sales = item[19] if item[19] is not None and not pd.isna(item[19]) and item[19] != '' else ' '
            _1_day_sales = item[20] if item[20] is not None and not pd.isna(item[20]) and item[20] != '' else ' '
            final_doh = item[21] if item[21] is not None and not pd.isna(item[21]) and item[21] != '' else ' '
            scg_qty = item[22] if item[22] is not None and not pd.isna(item[22]) and item[22] != '' else ' '
            spare = item[23] if item[23] is not None and not pd.isna(item[23]) and item[23] != '' else ' '
            spare_warehouse_qty = item[24] if item[24] is not None and not pd.isna(item[24]) and item[24] != '' else ' '
            spend_warehouse_qty = item[25] if item[25] is not None and not pd.isna(item[25]) and item[25] != '' else ' '
            shop_remaining = item[26] if item[26] is not None and not pd.isna(item[26]) and item[26] != '' else ' '
            in_transit = item[27] if item[27] is not None and not pd.isna(item[27]) and item[27] != '' else ' '
            adjust_shop_remaining = item[28] if item[28] is not None and not pd.isna(item[28]) and item[28] != '' else ' '
            final_suggested_transfer = item[29] if item[29] is not None and not pd.isna(item[29]) and item[29] != '' else ' '

            # สร้างคำสั่ง SQL สำหรับแทรกข้อมูลลงในฐานข้อมูล
            sql_query = f"""
                INSERT INTO inventory_transfer (day_date,transfer_from_code,item_code,full_description,inventory_posting_group,cat2,brand,branch,branch_name,area_manager,sales_support,
                zone,pickup_date,branch_arrival_date,location_group_code,_28_days_sales,_21_days_sales,_14_days_sales,_7_days_sales,make_up_sales,_1_day_sales,final_doh,scg_qty,spare,spare_warehouse_qty,
                spend_warehouse_qty,shop_remaining,in_transit,adjust_shop_remaining,final_suggested_transfer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            # Execute SQL query
            cursor.execute(sql_query, (day_date,transfer_from_code,item_code,full_description,inventory_posting_group,cat2,brand,branch,branch_name,area_manager,sales_support,
                zone,pickup_date,branch_arrival_date,location_group_code,_28_days_sales,_21_days_sales,_14_days_sales,_7_days_sales,make_up_sales,_1_day_sales,final_doh,scg_qty,spare,spare_warehouse_qty,
                spend_warehouse_qty,shop_remaining,in_transit,adjust_shop_remaining,final_suggested_transfer))
        # Commit เปลี่ยนแปลง
        connection_invoice.commit()
    except Exception as e:
        print(f"Error on item: {item}")
        print("Error:", str(e))
        flash(f'An error occurred while processing the file: {e}')
    finally:
        connection_invoice.close()   

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}

def import_data_mis():
    data = [] 
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        try:
            df = pd.read_excel(filepath, skiprows=0, usecols="A:AD")
            data = df.values.tolist()
            # Process the list `data_list` as needed
        except Exception as e:
            flash(f'An error occurred while processing the file: {e}')
        if data:
            insert_data_to_pgsql(data)
            flash('File successfully uploaded and processed')
        else:
            flash('File has no data!')
    else:
        flash('Invalid file type')
    return redirect('/web_import_data_mis')