from flask import Flask, render_template, request, redirect, Response, jsonify
from config_db import connection_string
import pyodbc

connection = pyodbc.connect(connection_string)

def api_get_data_cost():
    data_cost = []
    # SQL
    try:
        ############################################################ Cost query ############################################################
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        sql_query_cost = """
            select
                pol.product_id,
                pol.price_unit,
                max(po.date_order) as latest_order_date
            from
                purchase_order po
            left join purchase_order_line pol on pol.order_id = po.id
            where
                po.state = 'purchase'
            group by
                pol.product_id,pol.price_unit
        """
        # connection = db.session.connection()  # เปิด Connection
        # result = connection.execute(sql_query_cost)
        cursor.execute(sql_query_cost)
        result = cursor.fetchall()
        data_cost = [{
                    'product_id': item.product_id, 
                    'price_unit': item.price_unit, 
                    'latest_order_date': item.latest_order_date
                } for item in result]
        print("Cost Product การเชื่อมต่อฐานข้อมูลสำเร็จ")
    except Exception as e:
        print("Cost Product การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
    finally:
        connection.close()  # ปิด Connection
    return jsonify(data_cost)