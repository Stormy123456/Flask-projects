from flask import render_template, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import text
# from sqlalchemy import Row
# from datetime import datetime, timedelta
from config_db import connection_string
import pyodbc 

def row_to_dict(row):
    return dict(row.items())

def api_get_from_data_cn():
    data = []
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    date_from = date_from + ' ' + '00:00:00'
    date_to = date_to + ' ' + '23:59:59'
     
    if date_from and date_to:
        if date_from > date_to:
            print("วันเริ่มต้นต้องมากกว่าวันสิ้นสุดเสมอ")
            return render_template('index_cn.html', data=data, error_message="วันเริ่มต้นต้องมากกว่าวันสิ้นสุดเสมอ")
        else:
            # SQL
            try:
                connection = pyodbc.connect(connection_string)
                cursor = connection.cursor()
                ############################################################ So query ############################################################
                sql_query = f"""with CombineTaxes as (
                                            select
                                				STRING_AGG(distinct at.name, ', ') as name,
                                			    aml_sup.id as id
                                			from 
                                			    account_move_line aml_sup
                                			join account_move_line_account_tax_rel amlatr on amlatr.account_move_line_id = aml_sup.id
                                			left join account_tax at on at.id = amlatr.account_tax_id
                                			group by aml_sup.id
                                      ),
                                Amount_total as (
                                            select 
                                            	am_total.id as id,
                                            	sum(
                                					case
                                						when aml_total.price_total < 0 then aml_total.price_total
                                						else 0
                                					end
                                				) as discount,
                                            	sum(
                                            		case
                                            			when aml_total.price_total > 0 then aml_total.price_total
                                            			else 0
                                            		end
                                            	) as amount
                                            from
                                            	account_move_line aml_total
                                            join account_move am_total on am_total.id = aml_total.move_id
                                            where am_total.move_type = 'out_refund' and am_total.is_e_tax_invoice is not true 
                                            group by am_total.id
                                )
                                select 
                                	am.id as id,
                                	ROW_NUMBER() OVER (PARTITION BY am.id ORDER BY am.id) AS row_number,
                                	TO_CHAR(am.invoice_date, 'YYYY-MM-DDTHH24:MI:SS') as invoice_date,
                                    TO_CHAR(am.invoice_date_due, 'YYYY-MM-DDTHH24:MI:SS') as due_date,
                                	am.name as number,
                                	pos.pos_reference as pos_order_receipt_number,
                                	TO_CHAR(pos.date_order, 'YYYY-MM-DDTHH24:MI:SS') as pos_order_date,
                                	pos.create_date as pos_order_create_on,
                                	rcb.code as branch_code,
                                	rcb.name as branch_name,
                                	rp_address.branch_code as branch_address_branch_code,
                                	spt.name as ordery_type,
                                	rp.is_company as partner_is_company,
                                    case 
    								    when rp.tax_name like '%บริษัท%' or rp.tax_name like '%ห้างหุ้นส่วน%' or rp.tax_name like '%หุ้นส่วน%' or rp.tax_name like '%จำกัด%' or rp.tax_name like '%มหาชน%' or rp.tax_name like '%กรุ๊ป%' then 'TAXI'
    								    else 'NIDN'
    								end as partner_buyer_type,
                                    rp.vat as partner_tax_id,
                                	rp.tax_name as partner_tax_name,
                                	rp.email as partner_email,
                                	rc.code as partner_country,
                                	CASE
									    WHEN rp.zip is not NULL THEN rp.zip
    									WHEN rp.tax_street2 IS NOT NULL AND RIGHT(rp.tax_street2, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street2, 5)
    									WHEN rp.tax_street IS NOT NULL AND RIGHT(rp.tax_street, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street, 5)
									END as partner_zip,
                                	rp.tax_street as partner_tax_street,
                                	rp.tax_street2 as partner_tax_street2,
                                	rcurency.name as curency,
                                	am.amount_untaxed as untaxed_amount,
                                	am.amount_tax as total_tax,
                                	am.amount_total as total,
                                    am.amount_total * 0.07 as total_tax_amount,
                                	pos.note as pos_order_internal_notes,
                                	pp.product_name as invoice_lines_product,
                                	aml.quantity as invoice_lines_quantity,
                                	aml.discount_amount as invoice_lines_discount_amount,
                                	aml.price_unit as invoice_lines_unit_price,
                                	cbt.name as invoice_lines_taxes,
                                	aml.price_subtotal as invoice_lines_subtotal,
                                	aml.price_total as invoice_lines_total,
                                	at.discount as discount_amount,
                                	am.amount_untaxed + am.amount_tax as amount_total
                                from account_move_line aml
                                join account_move am on am.id = aml.move_id
                                join product_product pp on pp.id = aml.product_id  
                                left join res_company_branches rcb ON rcb.id = am.company_branch_id 
                                left join res_partner rp on rp.id = am.partner_id  
                                left join res_country rc on rc.id = rp.country_id
                                left join res_partner rp_address on rp_address.id = rcb.address_id 
                                left join res_currency rcurency on rcurency.id = am.currency_id 
                                left join sale_purchase_types spt on spt.id = am.sale_purchase_type_id 
                                left join CombineTaxes cbt on cbt.id = aml.id
                                left join Amount_total at on at.id = am.id
                                left join pos_order pos on pos.id = am.pos_order_id
                                where aml.exclude_from_invoice_tab is not true
                                and am.move_type = 'out_refund' 
                                and am.is_e_tax_invoice is true    
                                and am.invoice_date + interval '7 hours' >= '{date_from}'
                                and am.invoice_date + interval '7 hours' <= '{date_to}'
                            union all
                            	select 
                                	am.id as id,
                                	ROW_NUMBER() OVER (PARTITION BY am.id ORDER BY am.id) AS row_number,
                                	TO_CHAR(am.invoice_date, 'YYYY-MM-DDTHH24:MI:SS') as invoice_date,
                                    TO_CHAR(am.invoice_date_due, 'YYYY-MM-DDTHH24:MI:SS') as due_date,
                                	am.name as number,
                                	so.origin as pos_order_receipt_number,
                                	TO_CHAR(so.date_order, 'YYYY-MM-DDTHH24:MI:SS') as pos_order_date,
                                	so.create_date as pos_order_create_on,
                                	rcb.code as branch_code,
                                	rcb.name as branch_name,
                                	rp_address.branch_code as branch_address_branch_code,
                                	spt.name as ordery_type,
                                	rp.is_company as partner_is_company,
                                	case 
    								    when rp.tax_name like '%บริษัท%' or rp.tax_name like '%ห้างหุ้นส่วน%' or rp.tax_name like '%หุ้นส่วน%' or rp.tax_name like '%จำกัด%' or rp.tax_name like '%มหาชน%' or rp.tax_name like '%กรุ๊ป%' then 'TAXI'
    								    else 'NIDN'
    								end as partner_buyer_type,
                                    rp.vat as partner_tax_id,
                                	rp.tax_name as partner_tax_name,
                                	rp.email as partner_email,
                                	rc.code as partner_country,
                                	CASE
									    WHEN rp.zip is not NULL THEN rp.zip
    									WHEN rp.tax_street2 IS NOT NULL AND RIGHT(rp.tax_street2, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street2, 5)
    									WHEN rp.tax_street IS NOT NULL AND RIGHT(rp.tax_street, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street, 5)
									END as partner_zip,
                                	rp.tax_street as partner_tax_street,
                                	rp.tax_street2 as partner_tax_street2,
                                	rcurency.name as curency,
                                	am.amount_untaxed as untaxed_amount,
                                	am.amount_tax as total_tax,
                                	am.amount_total as total,
                                	am.amount_total * 0.07 as total_tax_amount,
                                	so.note as pos_order_internal_notes,
                                	pp.product_name as invoice_lines_product,
                                	aml.quantity as invoice_lines_quantity,
                                	aml.discount_amount as invoice_lines_discount_amount,
                                	aml.price_unit as invoice_lines_unit_price,
                                	cbt.name as invoice_lines_taxes,
                                	aml.price_subtotal as invoice_lines_subtotal,
                                	aml.price_total as invoice_lines_total,
                                	at.discount as discount_amount,
                                	am.amount_untaxed + am.amount_tax as amount_total
                                from account_move_line aml
                                join account_move am on am.id = aml.move_id
                                join product_product pp on pp.id = aml.product_id  
                                left join res_company_branches rcb ON rcb.id = am.company_branch_id 
                                left join res_partner rp on rp.id = am.partner_id  
                                left join res_country rc on rc.id = rp.country_id
                                left join res_partner rp_address on rp_address.id = rcb.address_id 
                                left join res_currency rcurency on rcurency.id = am.currency_id 
                                left join sale_purchase_types spt on spt.id = am.sale_purchase_type_id 
                                left join CombineTaxes cbt on cbt.id = aml.id
                                left join Amount_total at on at.id = am.id
                                inner join sale_order_line_invoice_rel solir on solir.invoice_line_id = aml.id
                                inner join sale_order_line sol on sol.id = solir.order_line_id
                                inner join sale_order so on so.id = sol.order_id
                                where aml.exclude_from_invoice_tab is not true
                                and am.move_type = 'out_refund'  
                                and am.is_e_tax_invoice is true 
                                and am.invoice_date + interval '7 hours' >= '{date_from}'
                                and am.invoice_date + interval '7 hours' <= '{date_to}'
                    """
                cursor.execute(sql_query)
                result = cursor.fetchall()
                data = [{
                            'invoice_number': item.number,
                            'branch_code': item.branch_code,
                            'buyer_type': item.partner_buyer_type,
                            'buyer_tax_id': item.partner_tax_id,
                            'buyer_nam': item.partner_tax_name,
                            'buyer_email': item.partner_email,
                            'buyer_email_cc': '',
                            'buyer_zipcode': item.partner_zip,
                            'buyer_country': item.partner_country if item.partner_country is not None else 'TH',
                            'buyer_address_1': item.partner_tax_street,
                            'buyer_address_2': item.partner_tax_street2,
                            'currency': item.curency,
                            'amount': str(item.total),
                            'tax_code_type': 'VAT',
                            'tax_rate': 7,
                            'tax_amount': str(item.total_tax_amount),
                            'fee_amount': '',
                            'discount_amount': item.discount_amount if item.discount_amount is not None else 0,
                            'total_amount_old': str(item.total + (item.discount_amount if item.discount_amount is not None else 0)),
                            'total_amount_diff': 0,
                            'total_amount_before_tax': str(item.total - item.total_tax),
                            'total_amount': str(item.amount_total),
                            'payment_condition': '',
                            'due_date': item.due_date,
                            'save_date': item.pos_order_date if item.pos_order_date is not None else None,
                            'document_reference': item.pos_order_receipt_number,
                            'document_reference_date': item.pos_order_date if item.pos_order_date is not None else None,
                            'document_reference_code': 'LC',
                            'document_reason': '',
                            'document_reason_code': '',
                            'note': item.pos_order_internal_notes,
                            'export_date': item.pos_order_date if item.pos_order_date is not None else None,
                            'pdf_password': '',
                            'additional': '',
                            'order_no': item.row_number,
                            'product_description': item.invoice_lines_product,
                            'product_quantity': item.invoice_lines_quantity,
                            'product_unit_code': 'EA',
                            'product_amount': str(item.invoice_lines_total), 
                            'product_amount_vat': str(item.invoice_lines_total - item.invoice_lines_subtotal),
                            'product_amount_per_txn': str(item.invoice_lines_total),
                            'product_total_amount_per_txn': str(item.invoice_lines_total)
                        } for item in result]
                print("Account Move Is Success")
            except Exception as e:
                print("Account Move Error:", str(e))
            finally:
                connection.close()  # ปิด Connection
    return jsonify(data)


def api_get_from_data_inv():
    data = []
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    date_from = date_from + ' ' + '00:00:00'
    date_to = date_to + ' ' + '23:59:59'
     
    if date_from and date_to:
        if date_from > date_to:
            print("วันเริ่มต้นต้องมากกว่าวันสิ้นสุดเสมอ")
            return render_template('index_inv.html', data=data, error_message="วันเริ่มต้นต้องมากกว่าวันสิ้นสุดเสมอ")
        else:
            # SQL
            try:
                connection = pyodbc.connect(connection_string)
                cursor = connection.cursor()
                ############################################################ So query ############################################################
                sql_query = f"""with CombineTaxes as (
                                            select
                                				STRING_AGG(distinct at.name, ', ') as name,
                                			    aml_sup.id as id
                                			from 
                                			    account_move_line aml_sup
                                			join account_move_line_account_tax_rel amlatr on amlatr.account_move_line_id = aml_sup.id
                                			left join account_tax at on at.id = amlatr.account_tax_id
                                			group by aml_sup.id
                                      ),
                                Amount_total as (
                                            select 
                                            	am_total.id as id,
                                            	sum(
                                					case
                                						when aml_total.price_total < 0 then aml_total.price_total
                                						else 0
                                					end
                                				) as discount,
                                            	sum(
                                            		case
                                            			when aml_total.price_total > 0 then aml_total.price_total
                                            			else 0
                                            		end
                                            	) as amount
                                            from
                                            	account_move_line aml_total
                                            join account_move am_total on am_total.id = aml_total.move_id
                                            where am_total.move_type = 'out_invoice' and am_total.is_e_tax_invoice is not true 
                                            group by am_total.id
                                )
                                select 
                                	am.id as id,
                                	ROW_NUMBER() OVER (PARTITION BY am.id ORDER BY am.id) AS row_number,
                                    TO_CHAR(am.invoice_date, 'YYYY-MM-DDTHH24:MI:SS') as invoice_date,
                                    TO_CHAR(am.invoice_date_due, 'YYYY-MM-DDTHH24:MI:SS') as due_date,
                                	am.name as number,
                                	pos.pos_reference as pos_order_receipt_number,
                                	TO_CHAR(pos.date_order, 'YYYY-MM-DDTHH24:MI:SS') as pos_order_date,
                                	pos.create_date as pos_order_create_on,
                                	rcb.code as branch_code,
                                	rcb.name as branch_name,
                                	rp_address.branch_code as branch_address_branch_code,
                                	spt.name as ordery_type,
                                	rp.is_company as partner_is_company,
                                    case 
    								    when rp.tax_name like '%บริษัท%' or rp.tax_name like '%ห้างหุ้นส่วน%' or rp.tax_name like '%หุ้นส่วน%' or rp.tax_name like '%จำกัด%' or rp.tax_name like '%มหาชน%' or rp.tax_name like '%กรุ๊ป%' then 'TXID'
    								    else 'NIDN'
    								end as partner_buyer_type,
                                    rp.vat as partner_tax_id,
                                	rp.tax_name as partner_tax_name,
                                	rp.email as partner_email,
                                	rc.code as partner_country,
                                	CASE
									    WHEN rp.zip is not NULL THEN rp.zip
    									WHEN rp.tax_street2 IS NOT NULL AND RIGHT(rp.tax_street2, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street2, 5)
    									WHEN rp.tax_street IS NOT NULL AND RIGHT(rp.tax_street, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street, 5)
									END as partner_zip,
                                	rp.tax_street as partner_tax_street,
                                	rp.tax_street2 as partner_tax_street2,
                                	rcurency.name as curency,
                                	am.amount_untaxed as untaxed_amount,
                                	am.amount_tax as total_tax,
                                	am.amount_total as total,
                                    am.amount_total * 0.07 as total_tax_amount,
                                	pos.note as pos_order_internal_notes,
                                	pp.product_name as invoice_lines_product,
                                	aml.quantity as invoice_lines_quantity,
                                	aml.discount_amount as invoice_lines_discount_amount,
                                	aml.price_unit as invoice_lines_unit_price,
                                	cbt.name as invoice_lines_taxes,
                                	aml.price_subtotal as invoice_lines_subtotal,
                                	aml.price_total as invoice_lines_total,
                                	at.discount as discount_amount,
                                	am.amount_untaxed + am.amount_tax as amount_total
                                from account_move_line aml
                                join account_move am on am.id = aml.move_id
                                join product_product pp on pp.id = aml.product_id  
                                left join res_company_branches rcb ON rcb.id = am.company_branch_id 
                                left join res_partner rp on rp.id = am.partner_id  
                                left join res_country rc on rc.id = rp.country_id
                                left join res_partner rp_address on rp_address.id = rcb.address_id 
                                left join res_currency rcurency on rcurency.id = am.currency_id 
                                left join sale_purchase_types spt on spt.id = am.sale_purchase_type_id 
                                left join CombineTaxes cbt on cbt.id = aml.id
                                left join Amount_total at on at.id = am.id
                                left join pos_order pos on pos.id = am.pos_order_id
                                where aml.exclude_from_invoice_tab is not true
                                and am.move_type = 'out_invoice' 
                                and am.is_e_tax_invoice is true      
                                and am.invoice_date + interval '7 hours' >= '{date_from}'
                                and am.invoice_date + interval '7 hours' <= '{date_to}'
                            union all
                           		select 
                                	am.id as id,
                                	ROW_NUMBER() OVER (PARTITION BY am.id ORDER BY am.id) AS row_number,
                                    TO_CHAR(am.invoice_date, 'YYYY-MM-DDTHH24:MI:SS') as invoice_date,
                                    TO_CHAR(am.invoice_date_due, 'YYYY-MM-DDTHH24:MI:SS') as due_date,
                                	am.name as number,
                                	so.origin as pos_order_receipt_number,
                                	TO_CHAR(so.date_order, 'YYYY-MM-DDTHH24:MI:SS') as pos_order_date,
                                	so.create_date as pos_order_create_on,
                                	rcb.code as branch_code,
                                	rcb.name as branch_name,
                                	rp_address.branch_code as branch_address_branch_code,
                                	spt.name as ordery_type,
                                	rp.is_company as partner_is_company,
                                    case 
    								    when rp.tax_name like '%บริษัท%' or rp.tax_name like '%ห้างหุ้นส่วน%' or rp.tax_name like '%หุ้นส่วน%' or rp.tax_name like '%จำกัด%' or rp.tax_name like '%มหาชน%' or rp.tax_name like '%กรุ๊ป%' then 'TAXI'
    								    else 'NIDN'
    								end as partner_buyer_type,
                                    rp.vat as partner_tax_id,
                                	rp.tax_name as partner_tax_name,
                                	rp.email as partner_email,
                                	rc.code as partner_country,
                                	CASE
									    WHEN rp.zip is not NULL THEN rp.zip
    									WHEN rp.tax_street2 IS NOT NULL AND RIGHT(rp.tax_street2, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street2, 5)
    									WHEN rp.tax_street IS NOT NULL AND RIGHT(rp.tax_street, 5) ~ '^[0-9]+$' THEN RIGHT(rp.tax_street, 5)
									END as partner_zip,
                                	rp.tax_street as partner_tax_street,
                                	rp.tax_street2 as partner_tax_street2,
                                	rcurency.name as curency,
                                	am.amount_untaxed as untaxed_amount,
                                	am.amount_tax as total_tax,
                                	am.amount_total as total,
                                	am.amount_total * 0.07 as total_tax_amount,
                                	so.note as pos_order_internal_notes,
                                	pp.product_name as invoice_lines_product,
                                	aml.quantity as invoice_lines_quantity,
                                	aml.discount_amount as invoice_lines_discount_amount,
                                	aml.price_unit as invoice_lines_unit_price,
                                	cbt.name as invoice_lines_taxes,
                                	aml.price_subtotal as invoice_lines_subtotal,
                                	aml.price_total as invoice_lines_total,
                                	at.discount as discount_amount,
                                	am.amount_untaxed + am.amount_tax as amount_total
                                from account_move_line aml
                                join account_move am on am.id = aml.move_id
                                join product_product pp on pp.id = aml.product_id  
                                left join res_company_branches rcb ON rcb.id = am.company_branch_id 
                                left join res_partner rp on rp.id = am.partner_id  
                                left join res_country rc on rc.id = rp.country_id
                                left join res_partner rp_address on rp_address.id = rcb.address_id 
                                left join res_currency rcurency on rcurency.id = am.currency_id 
                                left join sale_purchase_types spt on spt.id = am.sale_purchase_type_id 
                                left join CombineTaxes cbt on cbt.id = aml.id
                                left join Amount_total at on at.id = am.id
                                inner join sale_order_line_invoice_rel solir on solir.invoice_line_id = aml.id
                                inner join sale_order_line sol on sol.id = solir.order_line_id
                                inner join sale_order so on so.id = sol.order_id
                                where aml.exclude_from_invoice_tab is not true
                                and am.move_type = 'out_invoice' 
                                and am.is_e_tax_invoice is true 
                                and am.invoice_date + interval '7 hours' >= '{date_from}'
                                and am.invoice_date + interval '7 hours' <= '{date_to}'
                    """
                cursor.execute(sql_query)
                result = cursor.fetchall()
                data = [{
                            'invoice_number': item.number,
                            'branch_code': item.branch_code,
                            'buyer_type': item.partner_buyer_type,
                            'buyer_tax_id': item.partner_tax_id,
                            'buyer_nam': item.partner_tax_name,
                            'buyer_email': item.partner_email,
                            'buyer_email_cc': '',
                            'buyer_zipcode': item.partner_zip,
                            'buyer_country': item.partner_country if item.partner_country is not None else 'TH',
                            'buyer_address_1': item.partner_tax_street,
                            'buyer_address_2': item.partner_tax_street2,
                            'currency': item.curency,
                            'amount': str(item.total),
                            'tax_code_type': 'VAT',
                            'tax_rate': 7,
                            'tax_amount': str(item.total_tax_amount),
                            'fee_amount': '',
                            'discount_amount': str(item.discount_amount if item.discount_amount is not None else 0),
                            'total_amount_before_tax': str(item.total - item.total_tax),
                            'total_amount_tax': str(item.total_tax),
                            'total_amount': str(item.amount_total),
                            'cash_pay': '',
                            'cheque_number': '',
                            'cheque_amount': '',
                            'cheque_date': '',
                            'payment_condition': '',
                            'due_date': item.due_date,
                            'save_date': item.pos_order_date if item.pos_order_date is not None else None,
                            'document_reference': item.pos_order_receipt_number,
                            'document_reference_date': item.pos_order_date if item.pos_order_date is not None else None,
                            'document_reference_code': 'LC',
                            'document_reason': '',
                            'document_reason_code': '',
                            'note': item.pos_order_internal_notes,
                            'export_date': item.pos_order_date if item.pos_order_date is not None else None,
                            'pdf_password': '',
                            'additional': '',
                            'order_no': item.row_number,
                            'product_description': item.invoice_lines_product,
                            'product_quantity': item.invoice_lines_quantity,
                            'product_unit_code': 'EA',
                            'product_amount': str(item.invoice_lines_total), 
                            'product_amount_vat': str(item.invoice_lines_total - item.invoice_lines_subtotal),
                            'product_amount_per_txn': str(item.invoice_lines_total),
                            'product_total_amount_per_txn': str(item.invoice_lines_total)
                        } for item in result]
                print("Account Move Is Success")
            except Exception as e:
                print("Account Move Error:", str(e))
            finally:
                connection.close()  # ปิด Connection
    return jsonify(data)