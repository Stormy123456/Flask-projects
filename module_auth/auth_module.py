from flask import Flask, render_template, request, session
from datetime import datetime
from config_db import connection_string
import pyodbc 

def auth_users():
    Code = request.args.get('Code', 'No EMP code') 
    data = []
    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        ############################################################ So query ############################################################
        sql_query = f"""select
                             ru.login as employee_code,
                             rp.name as emplyee_name,
                             rug.id as employee_group_id,
                             rug.name as employee_group
                        FROM  
                             res_partner rp
                             INNER JOIN res_users ru ON ru.partner_id = rp.id  
                             LEFT JOIN res_user_group rug ON rug.id = ru.user_group_id
                        WHERE ru.login = '{Code}'
            """
        cursor.execute(sql_query)
        result = cursor.fetchall()
        data = [{
                    'employee_code': str(item.employee_code),
                    'emplyee_name': str(item.emplyee_name),
                    'employee_group_id': str(item.employee_group_id),
                    'employee_group': str(item.employee_group)
                } for item in result]
        print("Users is Success")
    except Exception as e:
        print("Users Error:", str(e))
    finally:
        connection.close()  # ปิด Connection
    employee_code = ''
    emplyee_name = ''
    employee_group_id = ''
    employee_group = ''
    for data_u in data:
        employee_code = data_u['employee_code']
        emplyee_name = data_u['emplyee_name']
        employee_group_id = data_u['employee_group_id']
        employee_group = data_u['employee_group']
    if employee_code == '' or employee_code == None:
        employee_code = 'Unknow'
    if emplyee_name == '' or emplyee_name == None:
        emplyee_name = 'Unknow'
    if employee_group_id == '' or employee_group_id == None:
        employee_group_id = 'Unknow'
    if employee_group == '' or employee_group == None:
        employee_group = 'Unknow'
    session['employee_code'] = employee_code
    session['emplyee_name'] = emplyee_name
    session['employee_group_id'] = employee_group_id
    session['employee_group'] = employee_group
    print("data = ",data)
    print(f"Session set: employee_code={employee_code}, emplyee_name={emplyee_name}, employee_group_id={employee_group_id}, employee_group={employee_group}")