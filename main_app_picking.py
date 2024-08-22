from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from datetime import datetime, timedelta
from module_warehouse_apps.sp_automate_app.sp_automate import api_get_datapicking, generate_excel, generate_excellines 
from module_ar_apps.pos_data_report_app.pos_data_report import api_get_datapos 
from module_ar_apps.e_tax_report_app.e_tax_report import api_get_from_data_cn, api_get_from_data_inv
from module_ar_apps.texcom_report_app.get_data import api_get_data
from module_ar_apps.texcom_report_app.get_data_with_po import api_get_data_with_po
from module_ar_apps.texcom_report_app.data_payment import api_get_data_payment
from module_ar_apps.texcom_report_app.data_cost import api_get_data_cost
from module_auth.auth_module import auth_users
from module_permission.config_permission import user_permission_check, config_page, add_permissions_spautomate, add_permissions_pos_data, add_permissions_etax, add_permissions_texcom
from modeule_log_users.log_users_module import log_users
from module_ar_apps.gi_data_report_app.gi_data_report import print_gi_data_report
from module_web_import_mis.web_import_mis import import_data_mis
from module_web_promotion.price_set import add_data, update_data, delete_data
from module_web_promotion.cost_data import stock_qty, cost_insert, cost_edit, cost_delete
from module_web_promotion.set_premium import set_premium_insert, set_premium_edit, set_premium_delete
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)


# from module_web_promotion.web_promotion import index
from config_db import connection_string, connection_string_invoice, db_test
import pyodbc 

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/logout')
def logout():
    session.pop('employee_code', None)
    session.pop('emplyee_name', None)
    session.pop('employee_group_id', None)
    session.pop('employee_group', None)
    return redirect('https://app01.tgfone.com/one_service/')

################################################### Main Web ###################################################
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.args.get('Code', 'No EMP code') != 'No EMP code':
            auth_users()
            return render_template('index.html', refresh=True)
        elif request.args.get('Code', 'No EMP code') == 'No EMP code' and session.get('employee_code', 'Unknown') != 'Unknown':
            return render_template('index.html', refresh=False)
        else:
            return redirect('https://app01.tgfone.com/one_service/')
    except Exception as e:
        print("An error occurred:", e)
        return redirect('https://app01.tgfone.com/one_service/')

################################################### User auth setting ###################################################
@app.route('/config_auth')
def config_auth():
    return config_page()

@app.route('/api/config_add_permissions_spautomate', methods=['POST'])
def config_add_permissions_spautomate():
    return add_permissions_spautomate()

@app.route('/api/config_add_permissions_pos_data', methods=['POST'])
def config_add_permissions_pos_data():
    return add_permissions_pos_data()

@app.route('/api/config_add_permissions_etax', methods=['POST'])
def config_add_permissions_etax():
    return add_permissions_etax()

@app.route('/api/config_add_permissions_texcom', methods=['POST'])
def config_add_permissions_texcom():
    return add_permissions_texcom()

################################################### User logs ###################################################
@app.route('/user_logs')
def user_logs():
    if session['employee_group_id'] == '59':
        log_data = []
        try:
            connection = pyodbc.connect(connection_string_invoice)
            cursor = connection.cursor()
            sql_query = f"""
                            select
                                ea.emp_code as emp_code,
                                ea.emp_name as emp_name,
                                ea.type_name as type_name,
                                ea.activity as activity,
                                ea.date_time as date_time
                            FROM  
                                employee_activities ea
                            ORDER BY 
                                ea.date_time DESC
                """
            cursor.execute(sql_query)
            result = cursor.fetchall()
            log_data = [{
                        'emp_code': str(item.emp_code),
                        'emp_name': str(item.emp_name),
                        'type_name': str(item.type_name),
                        'activity': str(item.activity),
                        'date_time': item.date_time,
                    } for item in result]
        except Exception as e:
            print("Data Error:", str(e))
        finally:
            connection.close()  # ปิด Connection
        return render_template('log_activity/user_logs.html',log_data=log_data)
    else:
        return render_template('index.html', show_popup=True, popup_message='คุณไม่ได้รับอนุญาติให้เข้าถึงหน้าเว็ปนี้!!!')

################################################### งานแผนกคลัง ###################################################
################################################### งานแผนกคลัง ###################################################
################################################### งานแผนกคลัง ###################################################
################################################### Module Warehouse Apps ###################################################
@app.route('/sp_automate_index')
def sp_automate_index():
    response = user_permission_check(menu_id=1)
    if response == True:
        log_users(Type_name='Stock Picking Automate', Activity='Open stock picking automate page')
        return render_template('warehouse_templates/index_stock_picking_automate.html')
    return response

@app.route('/api/get_datapicking', methods=['GET', 'POST'])
def call_api_get_datapicking():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='Stock Picking Automate',Activity='Load data picking')
        return api_get_datapicking()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

@app.route('/generate_excel', methods=['POST'])
def call_generate_excel():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='Stock Picking Automate',Activity='Export data picking')
        return generate_excel()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')


@app.route('/generate_excellines', methods=['POST'])
def call_generate_excellines():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='Stock Picking Automate',Activity='Export data line picking')
        return generate_excellines()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')


################################################### งานแผนก AR ###################################################
################################################### งานแผนก AR ###################################################
################################################### งานแผนก AR ###################################################
################################################### Module pos data apps ###################################################
@app.route('/pos_data_report_index', methods=['GET', 'POST'])
def pos_data_report_index():
    response = user_permission_check(menu_id=2)
    if response == True:
        log_users(Type_name='POS data report',Activity='Open POS data report page')
        return render_template('ar_templates/index_ar_pos_data.html')
    return response

@app.route('/api/get_datapos', methods=['GET', 'POST'])
def call_api_get_datapos():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='POS data report',Activity='Load POS data')
        return api_get_datapos()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

################################################### Module e-tax apps ###################################################
@app.route("/e_tax_index")
def e_tax_index():
    response = user_permission_check(menu_id=3)
    if response == True:
        log_users(Type_name='E-tax data report',Activity='Open E-tax data main menu page')
        return render_template('ar_templates/index_etax_page.html')
    return response


@app.route("/index_inv")
def index_inv():
    response = user_permission_check(menu_id=3)
    if response == True:
        log_users(Type_name='E-tax data report',Activity='Open E-tax data invoice page')
        return render_template('ar_templates/index_inv.html')
    return response

@app.route("/index_cn")
def index_cn():
    response = user_permission_check(menu_id=3)
    if response == True:
        log_users(Type_name='E-tax data report',Activity='Open E-tax data credit note page')
        return render_template('ar_templates/index_cn.html')
    return response

@app.route('/api/get_data_cn', methods=['GET', 'POST'])
def call_api_get_data_cn():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='E-tax data report',Activity='Load E-tax invoice data')
        return api_get_from_data_cn()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')
        

@app.route('/api/get_data_inv', methods=['GET', 'POST'])
def call_api_get_from_data_inv():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='E-tax data report',Activity='Load E-tax credit note data')
        return api_get_from_data_inv()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

################################################## Module texcom apps ###################################################
@app.route("/index_texcom")
def index_texcom():
    response = user_permission_check(menu_id=4)
    if response == True:
        try:
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            sql_query = """select 
                                	rcb.id,
                                	rcb."name"
                                from
                                	res_company_branches rcb 
                                order by rcb.name ASC"""
            cursor.execute(sql_query)
            data_list = cursor.fetchall()
            dropdown_data = data_list
        except Exception as e:
            print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
        finally:
            connection.close()  # ปิด Connection
        log_users(Type_name='E-tax data report',Activity='Open Texcom page')
        return render_template('ar_templates/index_texcom.html', dropdown_data=dropdown_data)
    return response

@app.route('/api/get_data', methods=['GET'])
def call_api_get_from_data():
    if session['employee_code'] != 'Unknow':
        log_users(Type_name='E-tax data report',Activity='Load texcom data')
        option = request.args.get('option')
        if option == 'true':
            return api_get_data_with_po()
        else:
            return api_get_data()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

@app.route('/api/get_data_cost', methods=['GET'])
def call_api_get_from_data_cost():
    if session['employee_code'] != 'Unknow':
        return api_get_data_cost()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

@app.route('/api/get_data_payment', methods=['GET'])
def call_api_get_from_data_payment():
    if session['employee_code'] != 'Unknow':
        return api_get_data_payment()
    return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

################################################### Module Web GI data ###################################################
@app.route('/web_gi_data_report', methods=['GET', 'POST'])
def web_gi_data_index():
    # response = user_permission_check(menu_id=2)
    # if response == True:
    #     log_users(Type_name='GL data report',Activity='Open GL data report page')
    #     return render_template('ar_templates/gi_data_report.html')
    # return response
    return render_template('ar_templates/gi_data_report.html')

@app.route('/api/get_gi_data_report', methods=['GET', 'POST'])
def get_gi_data_report():
    return print_gi_data_report()
    # if session['employee_code'] != 'Unknow':
    #     log_users(Type_name='GL data report',Activity='Load GL data')
    #     return print_gi_data_report()
    # return render_template('https://app01.tgfone.com/one_service/', show_popup=True, popup_message='Route นี้ถูกป้องกันไว้')

################################################### Web Import BI ###################################################
################################################### Web Import BI ###################################################
################################################### Web Import BI ###################################################
################################################### Module Web Import BI ###################################################
@app.route('/web_import_data_mis', methods=['GET', 'POST'])
def web_import_data_mis_index():
    return render_template('web_import_mis/import_mis.html')

@app.route('/api/call_api_import_data_mis', methods=['GET', 'POST'])
def call_api_import_data_mis():
    return import_data_mis()


################################################### Web Promotion ###################################################
################################################### Web Promotion ###################################################
################################################### Web Promotion ###################################################
################################################### Module PriceSet ###################################################
@app.route('/web_promotion_price_set', methods=['GET', 'POST'])
def web_promotion_price_set():
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()
        sql_query = """select 
                        *
                    from
                    	price_set ps
                    where ps.status_delete is not true
                    order by ps.id ASC"""
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        
        cost_data_query = """select 
                        *
                    from
                    	cost_and_status cs
                    order by cs.model_sku ASC"""
        cursor.execute(cost_data_query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        cost_data = [dict(zip(columns, row)) for row in rows]

        # แทนที่ค่า NULL ด้วยช่องว่าง
        for row in data:
            for key in row:
                if row[key] is None:
                    row[key] = ''

    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
    finally:
        connection.close()  # ปิด Connection
        
    try:    
        connection_db_test = pyodbc.connect(db_test)
        cursor = connection_db_test.cursor()
        set_premium_query = """
            SELECT *
            FROM set_premium sp
        """
        cursor.execute(set_premium_query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        set_premium_data = [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))

    finally:
        connection_db_test.close()  # ปิด connection_db_testt
    return render_template('web_promotion/price_set.html', data=data,cost_data=cost_data,set_premium_data=set_premium_data)


@app.route('/add_price_set', methods=['POST'])
def add_price_set():
    return add_data()

@app.route('/update_price_set/<int:id>', methods=['POST'])
def update_price_set(id):
    return update_data(id)

@app.route('/delete_price_set/<int:id>', methods=['POST'])
def delete_price_set(id):
    return delete_data(id)

@app.route('/fetch_last_month_data', methods=['GET'])
def fetch_last_month_data():
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()

        # คำนวณเดือนก่อนหน้า
        # last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        # print("last_month = ",last_month)
        
        query = """SELECT id, show_status, update_status, start_date, end_date, location, brand, fulldescription
                   FROM price_set
                   WHERE (show_status = 'True' OR update_status = 'True') 
                   AND status_delete = 'True'"""
                   
        cursor.execute(query)
        
        # query = """SELECT id, show_status, update_status, start_date, end_date, location, brand, fulldescription
        #            FROM price_set
        #            WHERE (show_status = 'True' OR update_status = 'True')
        #            AND start_date LIKE ?"""

        # cursor.execute(query, (last_month + '%',))
        rows = cursor.fetchall()

        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        connection.close()

@app.route('/pull_back_data', methods=['POST'])
def pull_back_data():
    ids = request.json.get('ids', [])
    
    if not ids:
        return jsonify({'success': False, 'message': 'ไม่มีข้อมูลที่เลือก'})
    
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()

        query = """UPDATE price_set SET status_delete = False WHERE id IN ({})""".format(','.join('?' * len(ids)))
        cursor.execute(query, ids)
        connection.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        connection.close()

################################################### Module Cost&Status ###################################################
@app.route('/web_promotion_cost', methods=['GET', 'POST'])
def web_promotion_cost():
    odoo_product = []
    try:
        connection_odoo = pyodbc.connect(connection_string)
        cursor = connection_odoo.cursor()
        sql_query = """SELECT 
                                pt.id,
                        	    pt."name" as name,
                        	    pb.name as brand,
                                ps.name as status
                        FROM
                        	    product_template pt 
                        JOIN product_product pp ON pp.product_tmpl_id = pt.id
                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                        LEFT JOIN product_brand pb ON pb.id = pt.cu_product_brand_id 
                        LEFT JOIN product_status ps on ps.id = pt.cu_product_status_id 
                        WHERE pt.type != 'service' 
                        AND ( pp.default_code not like '%DM%' AND pp.default_code not like '%DS%')
                        AND pc.complete_name like '%SALEABLE%'
                        group by pt.id,pt.name,pb.name,ps.name"""
        cursor.execute(sql_query)
        data_list = cursor.fetchall()
        odoo_product = [{"id": row.id, "name": row.name, "brand": row.brand, "status": row.status} for row in data_list]
    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูล Odoo ไม่สำเร็จ:", str(e))
    finally:
        connection_odoo.close()  # ปิด connection_odoo
        
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()
        sql_query = """select 
                        cas.id,
                    	cas.start,
                    	cas.end,
                        cas.brand,
                        cas.model_sku,
                        cas.price_rrp,
                        cas.margin,
                        cas.cost_b,
                        cas.timestamp,
                        cas.status,
                        cas.status_cost,
                        cas.stock_qty
                    from
                    	cost_and_status cas 
                     where
                        cas.status_delete is not true
                    order by cas.id ASC"""
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
    finally:
        connection.close()  # ปิด Connection
    return render_template('web_promotion/cost_and_status.html', data=data,odoo_product=odoo_product)

@app.route('/get_stock_qty', methods=['POST'])
def get_stock_qty():
    return stock_qty()

@app.route('/web_promotion_cost_insert', methods=['GET', 'POST'])
def web_promotion_cost_insert():
    return cost_insert()

@app.route('/web_promotion_cost_update', methods=['GET', 'POST'])
def web_promotion_cost_update():
    return cost_edit()

@app.route('/web_promotion_cost_delete', methods=['GET', 'POST'])
def web_promotion_cost_delete():
    return cost_delete()

################################################### Module SetPremium ###################################################
@app.route('/web_promotion_set_premium', methods=['GET', 'POST'])
def web_promotion_set_premium():
    try:
        connection = pyodbc.connect(db_test)
        cursor = connection.cursor()
        sql_query = """select 
                        sp.id,
                        sp.lowest_price,
                        sp.highest_price,
                        sp.optionset1,
                        sp.optionset2,
                        sp.optionset3,
                        sp.cost_installment,
                        sp.month,
                        sp.warranty,
                        sp.type,
                        sp.avg_p,
                        sp.voucher_value,
                        sp.percent
                    from
                    	set_premium sp
                     where
                        sp.status_delete is not true
                    order by sp.id ASC"""
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print("การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
    finally:
        connection.close()  # ปิด Connection
    return render_template('web_promotion/set_premium.html', data=data)

@app.route('/web_set_premium_insert', methods=['GET', 'POST'])
def web_set_premium_insert():
    return set_premium_insert()

@app.route('/web_set_premium_update', methods=['GET', 'POST'])
def web_set_premium_update():
    return set_premium_edit()

@app.route('/web_set_premium_delete', methods=['GET', 'POST'])
def web_set_premium_delete():
    return set_premium_delete()
 
 
################################################### END FLASK ###################################################
if __name__ == '__main__':
    app.run(debug=True,port=5002)