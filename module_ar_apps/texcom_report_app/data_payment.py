from flask import Flask, render_template, request, redirect, Response, jsonify
from config_db import connection_string
import pyodbc

connection = pyodbc.connect(connection_string)

def api_get_data_payment():
    data_payment = []
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    print("date_from = ",date_from)
    print("date_to = ",date_to)
    date_from = date_from + ' ' + '00:00:00'
    date_to = date_to + ' ' + '23:59:59'
    # SQL
    try:
        ############################################################ Cost query ############################################################
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        sql_query_payment = """
            SELECT 
                pos.id as pos_id,
                pos.name AS pos_order_name,
                STRING_AGG(ppm.name, ' - ') AS payment_methods,
                ARRAY_TO_STRING(
    			    ARRAY_APPEND(
    			        ARRAY_AGG(
    			            CONCAT(
    			                rb.name, 
								CASE WHEN ppm.name = 'Cash' THEN 'Cash' ELSE ' ' END, 
    			                CASE WHEN cit.name IS NOT NULL THEN CONCAT('-', cit.name) ELSE ' ' END, 
    			                CASE WHEN cip.name IS NOT NULL THEN CONCAT('-', cip.name) ELSE ' ' END
    			            )
    			        ),
    			        CASE WHEN 'Cash1' = ANY(ARRAY_AGG(ppm.name)) THEN 'Cash'END
    			    ),
    			    ','
    			) AS combined_names,
                STRING_AGG(ppay.card_no, ' - ') AS card_no
            FROM
                pos_payment ppay
            LEFT JOIN res_bank rb ON rb.id = ppay.bank_id 
            LEFT JOIN pos_order pos ON pos.id = ppay.pos_order_id 
            LEFT JOIN pos_payment_method ppm ON ppm.id = ppay.payment_method_id 
            LEFT JOIN cu_installment_type cit ON cit.id = ppay.inst_type_id 
            LEFT JOIN cu_installment_period cip ON cip.id = ppay.inst_period_id 
            WHERE pos.date_order + interval '7 hours' >= '%s'
            AND pos.date_order + interval '7 hours' <=  '%s'
            GROUP BY pos.id, pos.name
        """% (date_from,date_to)
        # connection = db.session.connection()  # เปิด Connection
        # result = connection.execute(sql_query_cost)
        cursor.execute(sql_query_payment)
        result = cursor.fetchall()
        data_payment = [{
                    'pos_id': item.pos_id, 
                    'payment_methods': item.payment_methods, 
                    'bank_list': item.combined_names,
                    'card_no': item.card_no
                } for item in result]
        print("Payment Method การเชื่อมต่อฐานข้อมูลสำเร็จ")
    except Exception as e:
        print("Payment Method การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
    finally:
        connection.close()  # ปิด Connection
    return jsonify(data_payment)