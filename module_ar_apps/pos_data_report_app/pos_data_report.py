from flask import Flask, render_template, request, redirect, Response, jsonify, send_file
# from datetime import datetime, timedelta
from config_db import connection_string
# from collections import defaultdict
from pyexcelerate import Workbook
import pyodbc 
import pandas as pd
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
            sql_query = f"""WITH stock_picking_lot AS (
                                    SELECT 
                                            sp1.pos_order_id AS pos_order_id,
                                            sml1.id AS id,
                                            sml1.lot_id AS lot_id,
                                            sml1.product_id AS product_id,
                                            sml1.qty_done
                                    FROM stock_picking sp1
                                    LEFT JOIN stock_move_line sml1 ON sml1.picking_id = sp1.id 
                                    WHERE sp1.is_picking_combo IS NOT FALSE
                            ),
                            PaymentMedthod as (
                                    SELECT 
                                        pos.id as pos_id,
                                        STRING_AGG(CASE 
                                            WHEN ppm.name != 'Cash' THEN COALESCE(rb.name, '') 
                                            ELSE NULL 
                                        END, ' - ') AS bank_list,
    		                            STRING_AGG(COALESCE(cip.name, ''), ' - ') AS months,
    		                            STRING_AGG(COALESCE(cit.name, ''), ' - ') AS type,
    		                            STRING_AGG(COALESCE(ppay.card_no, ''), ' - ') AS card_number,
    		                            STRING_AGG(COALESCE(ppm.name, '') || COALESCE(' - ' || rb.name, ''), ' - ') AS label
                                 	FROM
                                    	pos_payment ppay
                                 	LEFT JOIN res_bank rb ON rb.id = ppay.bank_id 
                                 	LEFT JOIN pos_order pos ON pos.id = ppay.pos_order_id 
                                 	LEFT JOIN pos_payment_method ppm ON ppm.id = ppay.payment_method_id 
                                 	LEFT JOIN cu_installment_type cit ON cit.id = ppay.inst_type_id 
                                 	LEFT JOIN cu_installment_period cip ON cip.id = ppay.inst_period_id 
                                 	GROUP BY pos.id, pos.name
                            )
                            select DISTINCT
                            	posl.id,
                            	TO_CHAR(pos.date_order + interval '7 hours', 'DD/MM/YYYY') AS created_on,
                            	pos.name as order_ref,
                            	pos_return.name as return_from_order,
                            	s_pro_l.name as serial_number,
                                pp.default_code as internal_reference,
                                pos.pos_reference as receipt_number,
                                pt.name as full_product_name,
                                case 
                                        when s_pro_l.name IS NOT NULL THEN 1.00
                                        else ROUND(posl.qty, 2)
                                end AS quantity,
                                case 
                                        when s_pro_l.name is not null and posl.qty = 1 then ROUND((1 * posl.price_unit) * (1 - (posl.discount / 100)), 2)
                                        when s_pro_l.name is not null and posl.qty = -1 then ROUND((-1 * posl.price_unit) * (1 - (posl.discount / 100)), 2)
                                        else ROUND((posl.price_subtotal_incl) * (1 - (posl.discount / 100)), 2)
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
                            LEFT join pos_order pos ON pos.id = posl.order_id 
                            LEFT join pos_order pos_return ON pos_return.id = pos.return_order_id 
                            LEFT JOIN pos_session ps on ps.id = pos.session_id 
                            LEFT JOIN product_product pp ON pp.id = posl.product_id  
                            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id 
                            LEFT JOIN product_category pc ON pc.id = pt.categ_id
                            LEFT JOIN product_brand pb on pb.id = pt.cu_product_brand_id  
                            LEFT JOIN cu_product_model pm on pm.id = pt.cu_product_model_id 
                            LEFT JOIN pos_pack_operation_lot ppol on ppol.pos_order_line_id = posl.id 
                            LEFT JOIN
     	                    (
     	                        SELECT
     	                            sp1.id AS id,
     	                            sp1.pos_order_id as pos_order_id,
     	                            sp1.is_picking_combo as is_picking_combo,
     	                            ROW_NUMBER() OVER (PARTITION BY sp1.pos_order_id ORDER BY sp1.create_date ASC) AS row_num
     	                        FROM
     	                            stock_picking sp1
     	                    ) sp ON sp.row_num = 1 AND sp.pos_order_id = pos.id and sp.is_picking_combo is not false
                            LEFT JOIN (
                                       SELECT DISTINCT ON (sml_sub.picking_id, sml_sub.product_id)
                                                  sml_sub.id,
                                                  sml_sub.lot_id,
                                                  sml_sub.qty_done,
                                                  sml_sub.location_id,
                                                  sml_sub.location_dest_id,
                                                  sml_sub.picking_id,
                                                  sml_sub.product_id
                                           FROM stock_move_line sml_sub
                            		  ) as sml ON sml.picking_id = sp.id AND sml.product_id = pp.id  
                            LEFT join stock_production_lot s_pro_l on s_pro_l.id = sml.lot_id
                            LEFT JOIN res_partner rp on rp.id = pos.partner_id  
                            LEFT JOIN res_company_branches rcb on rcb.id = pos.company_branch_id 
                            LEFT JOIN res_partner rp_area on rp_area.id = rcb.area_manager_id 
                            LEFT JOIN res_users ru on ru.id = posl.user_id 
                            LEFT JOIN res_partner rp_ru on rp_ru.id = ru.partner_id 
                            LEFT JOIN res_users ru_c on ru_c.id = pos.user_id 
                            LEFT JOIN res_partner rp_ru_c on rp_ru_c.id = ru_c.partner_id 
                            LEFT JOIN account_analytic_account aaa on aaa.id = posl.analytic_account_id 
                            LEFT JOIN PaymentMedthod as peyment_pos on peyment_pos.pos_id  = pos.id   
                            WHERE pos.date_order + interval '7 hours' >= '{min_date}'
                            AND pos.date_order + interval '7 hours' <= '{max_date}'
                            AND pos.state IN ('paid','done','invoiced')
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
            
    return jsonify({
        'data_pos': data
    })