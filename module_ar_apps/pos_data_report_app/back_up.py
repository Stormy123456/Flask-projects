from flask import Flask, render_template, request, redirect, Response, jsonify, send_file
# from datetime import datetime, timedelta
from config_db import connection_string, connection_string_invoice
# from collections import defaultdict
from openpyxl.styles import Alignment
from openpyxl.styles import Font, Border, Side
import pyodbc 
import pandas as pd
from pyexcelerate import Workbook
import json

def api_get_datapos():
    data = []
    min_date = request.args.get('date_from')
    max_date = request.args.get('date_to')
    min_date = min_date + ' ' + '00:00:00'
    max_date = max_date + ' ' + '23:59:59'
    if min_date and max_date:
        # SQL 
        try:
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            ############################################################ So query ############################################################
            sql_query = f"""
                                                        with stock_picking_lot as (
                                    select 
                                            sp1.pos_order_id as pos_order_id,
                                            sml1.id as id,
                                            sml1.lot_id as lot_id,
                                            sml1.product_id as product_id,
                                            sml1.qty_done
                                    from stock_picking sp1
                                    left join stock_move_line sml1 ON sml1.picking_id = sp1.id 
                                    where sp1.is_picking_combo is not false 
                            ),
                            PaymentMedthod as (
                                    SELECT 
                                        pos.id as pos_id,
                                        STRING_AGG(rb.name, ' - ') AS bank_list,
                                        STRING_AGG(cip.name, ' - ') AS months,
                                        STRING_AGG(cit.name, ' - ') AS type,
                                        STRING_AGG(ppay.card_no, ' - ') AS card_number,
                                        STRING_AGG(ppm.name, ' - ') || ' - ' || STRING_AGG(rb.name, ' - ') AS label
                                 	FROM
                                    	pos_payment ppay
                                 	LEFT JOIN res_bank rb ON rb.id = ppay.bank_id 
                                 	LEFT JOIN pos_order pos ON pos.id = ppay.pos_order_id 
                                 	LEFT JOIN pos_payment_method ppm ON ppm.id = ppay.payment_method_id 
                                 	LEFT JOIN cu_installment_type cit ON cit.id = ppay.inst_type_id 
                                 	LEFT JOIN cu_installment_period cip ON cip.id = ppay.inst_period_id 
                                 	where ppm.name != 'Cash'
                                 	GROUP BY pos.id, pos.name
                            )
                            select 
                            	TO_CHAR(pos.date_order + interval '7 hours', 'DD/MM/YYYY') AS created_on,
                            	pos.name as order_ref,
                            	pos_return.name as return_from_order,
                            	s_pro_l.name AS serial_number,
                                pp.default_code as internal_reference,
                                pos.pos_reference as receipt_number,
                                pt.name as full_product_name,
                                case 
                                        when s_pro_l.name is not null then 1
                                        else posl.qty
                                end AS quantity,
                                case 
                                        when s_pro_l.name is not null then ROUND(1 * posl.price_unit, 2)
                                        else ROUND(posl.qty * posl.price_unit, 2)
                                end AS price_subtotal,
                                ROUND(posl.price_unit, 2) as unit_price,
                                ROUND(pos.amount_total, 2) as total,
                                rp.name as customer,
                                rcb.code as branch_code,
                                rcb.name as branch_name,
                                '[' || pp.default_code || '] ' || pp.product_name AS product,
                                ru.login as login,
                                rp_ru.name as sale_person,
                                rp_ru_c.name as cashier,
                                pb.name as product_brand,
                                pm.name as product_model,
                                peyment_pos.bank_list as bank_list,
                                peyment_pos.months as months,
                                peyment_pos.type as type,
                                peyment_pos.card_number as card_number,
                                peyment_pos.label as label,
                                posl.note as note,
                                pos.note as internal_note,
                                rp.phone as customer_phone,
                             	ps.name as session,
                             	pt.description as description,
                             	rp.street as complete_address,
                             	rp.vat as tax_id,
                             	'' as vendors,
                             	pc.complete_name as category,
                             	pt.cate_code_scg as category_code_scg,
 	                            aaa.name as analytic_account,
 	                            pt.scg_uom as product_uom,
 	                            rp_area.name as area 
                            from pos_order_line posl
                            left join pos_order pos ON pos.id = posl.order_id 
                            left join pos_order pos_return ON pos_return.id = pos.return_order_id 
                            LEFT JOIN pos_session ps on ps.id = pos.session_id 
                            INNER JOIN product_product pp ON pp.id = posl.product_id  
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id 
                            INNER JOIN product_category pc ON pc.id = pt.categ_id
                            LEFT JOIN product_brand pb on pb.id = pt.cu_product_brand_id  
                            LEFT JOIN cu_product_model pm on pm.id = pt.cu_product_model_id 
                            LEFT JOIN pos_pack_operation_lot ppol on ppol.pos_order_line_id = posl.id 
                            LEFT JOIN stock_picking_lot sp on pos.id = sp.pos_order_id and pp.id = sp.product_id 
                            LEFT JOIN stock_production_lot s_pro_l on s_pro_l.id = sp.lot_id 
                            LEFT JOIN res_partner rp on rp.id = pos.partner_id  
                            LEFT JOIN res_company_branches rcb on rcb.id = pos.company_branch_id 
                            LEFT JOIN res_partner rp_area on rp_area.id = rcb.area_manager_id 
                            LEFT JOIN res_users ru on ru.id = posl.user_id 
                            LEFT JOIN res_partner rp_ru on rp_ru.id = ru.partner_id 
                            LEFT JOIN res_users ru_c on ru_c.id = pos.user_id 
                            LEFT JOIN res_partner rp_ru_c on rp_ru_c.id = ru_c.partner_id 
                            LEFT JOIN account_analytic_account aaa on aaa.id = posl.analytic_account_id 
                            left join PaymentMedthod as peyment_pos on peyment_pos.pos_id  = pos.id  
                            WHERE pos.date_order + interval '7 hours' >= '{min_date}'
                            AND pos.date_order + interval '7 hours' <= '{max_date}'
                            AND pos.state IN ('paid','done','invoiced')
                            group by posl.id,sp.id,aaa.id,s_pro_l.id,pos.date_order,pp.product_name,pos.name,
	                        pos_return.name,s_pro_l.name,serial_number,pp.default_code,pos.pos_reference,
                            pt.name,posl.qty,posl.qty,posl.price_unit,posl.price_unit,pos.amount_total,
                            rp.name,rcb.code,rcb.name,pp.default_code,ru.login,rp_ru.name,rp_ru_c.name,
                            pb.name,pm.name,peyment_pos.bank_list,peyment_pos.months,peyment_pos.type,
                            peyment_pos.card_number,peyment_pos.label,posl.note,pos.note,rp.phone,ps.name,
 	                        pt.description,rp.street,rp.vat,pc.complete_name,pt.cate_code_scg,aaa.name,pt.scg_uom,rp_area.name
                        """
            cursor.execute(sql_query)
            result = cursor.fetchall()
            data = [{
                        'created_on': item.created_on,
                        'order_ref': item.order_ref,
                        'return_from_order': item.return_from_order,
                        'serial_number': item.serial_number,
                        'internal_reference': item.internal_reference,
                        'receipt_number': item.receipt_number,
                        'full_product_name': item.full_product_name,
                        'quantity': item.quantity,
                        'price_subtotal': item.price_subtotal,
                        'unit_price': item.unit_price,
                        'total': item.total,
                        'customer': item.customer,
                        'branch_code': item.branch_code,
                        'branch_name': item.branch_name,
                        'product': item.product,
                        'login': item.login,
                        'sale_person': item.sale_person,
                        'cashier': item.cashier,
                        'product_brand': item.product_brand,
                        'product_model': item.product_model,
                        'bank_list': item.bank_list,
                        'months': item.months,
                        'type': item.type,
                        'card_number': item.card_number,
                        'label': item.label,
                        'note': item.note,
                        'internal_note': item.internal_note,
                        'customer_phone': item.customer_phone,
                        'session': item.session,
                        'description': item.description,
                        'complete_address': item.complete_address,
                        'tax_id': item.tax_id,
                        # 'vendors': item.vendors,
                        'vendors': 'Comming soon!',
                        'category': item.category,
                        'category_code_scg': item.category_code_scg,
                        'analytic_account': item.analytic_account,
                        'product_uom': item.product_uom,
                        'area': item.area
                    } for item in result]
            print("POS is Success")
        except Exception as e:
            print("POS Error:", str(e))
        finally:
            connection.close()  # ปิด Connection   
        try:
            connection_invoice = pyodbc.connect(connection_string_invoice)
            cursor_inv = connection_invoice.cursor()
            sql_delete_query = "DELETE FROM pos_for_export"
            cursor_inv.execute(sql_delete_query)
            connection_invoice.commit()
            for item in data:
                created_on = item['created_on'] if item['created_on'] is not None else ' '
                order_ref = item['order_ref'] if item['order_ref'] is not None else ' '
                return_from_order = item['return_from_order'] if item['return_from_order'] is not None else ' '
                serial_number = item['serial_number'] if item['serial_number'] is not None else ' '
                internal_reference = item['internal_reference'] if item['internal_reference'] is not None else ' '
                receipt_number = item['receipt_number'] if item['receipt_number'] is not None else ' '
                full_product_name = item['full_product_name'] if item['full_product_name'] is not None else ' '
                quantity = item['quantity'] if item['quantity'] is not None else ' '
                price_subtotal = item['price_subtotal'] if item['price_subtotal'] is not None else ' '
                unit_price = item['unit_price'] if item['unit_price'] is not None else ' '
                total = item['total'] if item['total'] is not None else ' '
                customer = item['customer'] if item['customer'] is not None else ' '
                branch_code = item['branch_code'] if item['branch_code'] is not None else ' '
                branch_name = item['branch_name'] if item['branch_name'] is not None else ' '
                product = item['product'] if item['product'] is not None else ' '
                login = item['login'] if item['login'] is not None else ' '
                sale_person = item['sale_person'] if item['sale_person'] is not None else ' '
                cashier = item['cashier'] if item['cashier'] is not None else ' '
                product_brand = item['product_brand'] if item['product_brand'] is not None else ' '
                product_model = item['product_model'] if item['product_model'] is not None else ' '
                bank_list = item['bank_list'] if item['bank_list'] is not None else ' '
                months = item['months'] if item['months'] is not None else ' '
                type = item['type'] if item['type'] is not None else ' '
                card_number = item['card_number'] if item['card_number'] is not None else ' '
                label = item['label'] if item['label'] is not None else ' '
                note = item['note'] if item['note'] is not None else ' '
                internal_note = item['internal_note'] if item['internal_note'] is not None else ' '
                customer_phone = item['customer_phone'] if item['customer_phone'] is not None else ' '
                session = item['session'] if item['session'] is not None else ' '
                description = item['description'] if item['description'] is not None else ' '
                complete_address = item['complete_address'] if item['complete_address'] is not None else ' '
                tax_id = item['tax_id'] if item['tax_id'] is not None else ' '
                vendors = item['vendors'] if item['vendors'] is not None else ' '
                category = item['category'] if item['category'] is not None else ' '
                category_code_scg = item['category_code_scg'] if item['category_code_scg'] is not None else ' '
                analytic_account = item['analytic_account'] if item['analytic_account'] is not None else ' '
                product_uom = item['product_uom'] if item['product_uom'] is not None else ' '
                area = item['area'] if item['area'] is not None else ' '
                # สร้างคำสั่ง SQL สำหรับแทรกข้อมูลลงในฐานข้อมูล
                sql_query = f"""
                    INSERT INTO pos_for_export (created_on,order_ref,return_from_order,serial_number,internal_reference,receipt_number,full_product_name,quantity,price_subtotal,unit_price,total,customer,branch_code,branch_name,
                                                product,login,sale_person,cashier,product_brand,product_model,bank_list,months,type,card_number,label,note,internal_note,customer_phone,session,description,complete_address,tax_id,
                                                vendors,category,category_code_scg,analytic_account,product_uom,area)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                # Execute SQL query
                cursor_inv.execute(sql_query, (created_on,order_ref,return_from_order,serial_number,internal_reference,receipt_number,full_product_name,quantity,price_subtotal,unit_price,total,customer,branch_code,branch_name,
                                                product,login,sale_person,cashier,product_brand,product_model,bank_list,months,type,card_number,label,note,internal_note,customer_phone,session,description,complete_address,tax_id,
                                                vendors,category,category_code_scg,analytic_account,product_uom,area))
            # Commit เปลี่ยนแปลง
            connection_invoice.commit()
        except Exception as e:
            print("Error:", str(e))
            print("Failed to insert data:", created_on,order_ref,return_from_order,serial_number,internal_reference,receipt_number,full_product_name,quantity,price_subtotal,unit_price,total,customer,branch_code,branch_name,
                                                product,login,sale_person,cashier,product_brand,product_model,bank_list,months,type,card_number,label,note,internal_note,customer_phone,session,description,complete_address,tax_id,
                                                vendors,category,category_code_scg,analytic_account,product_uom,area)
            print("Error:", str(e))
        finally:
            connection_invoice.close()   
    return jsonify({
        'data_pos': data
    })

def generate_excel_pos():
    data = []
    try:
        connection_invoice = pyodbc.connect(connection_string_invoice)
        cursor_inv = connection_invoice.cursor()
        sql_query = """SELECT * FROM pos_for_export"""
        cursor_inv.execute(sql_query)
        result = cursor_inv.fetchall()
        
        # Map fetched data to a list of dictionaries
        data = [{
            'Date': item.created_on,
            'Order Ref': item.order_ref,
            'Return From Order': item.return_from_order,
            'Serial Number': item.serial_number,
            'Internal Reference': item.internal_reference,
            'Receipt Number': item.receipt_number,
            'Full Product Name': item.full_product_name,
            'Quantity': item.quantity,
            'Price Subtotal': item.price_subtotal,
            'Unit Price': item.unit_price,
            'Total': item.total,
            'Customer': item.customer,
            'Branch Code': item.branch_code,
            'Branch Name': item.branch_name,
            'Product': item.product,
            'Login': item.login,
            'Sale Person': item.sale_person,
            'Cashier': item.cashier,
            'Product Brand': item.product_brand,
            'Product Model': item.product_model,
            'Bank List': item.bank_list,
            'Months': item.months,
            'Type': item.type,
            'Card Number': item.card_number,
            'Label': item.label,
            'Note': item.note,
            'Internal Note': item.internal_note,
            'Customer Phone': item.customer_phone,
            'Session': item.session,
            'Description': item.description,
            'Complete Address': item.complete_address,
            'Tax ID': item.tax_id,
            'Vendors': item.vendors,
            'Category': item.category,
            'Category Code SCG': item.category_code_scg,
            'Analytic Account': item.analytic_account,
            'Product UOM': item.product_uom,
            'Area': item.area
        } for item in result]

        print("POS is Success")
    except Exception as e:
        print("Error:", str(e))
    finally:
        connection_invoice.close()   

    if data:
        headers = list(data[0].keys())
        data_rows = [headers] + [[row[header] for header in headers] for row in data]

        # Creating Excel workbook and worksheet
        wb = Workbook()
        ws = wb.new_sheet("Data", data=data_rows)

        # Save the workbook
        file_path = 'POS_DATA.xlsx'
        wb.save(file_path)

        return send_file(file_path, as_attachment=True)
    else:
        print("No data to write")
        return None