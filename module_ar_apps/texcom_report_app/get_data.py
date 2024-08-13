from flask import Flask, render_template, request, redirect, Response, jsonify
from config_db import connection_string
import pyodbc

connection = pyodbc.connect(connection_string)

def api_get_data():
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXX CHECK REQUEST XXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    data = []
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    dropdown = request.args.get('dropdown')
    limit = request.args.get('limit') 
    # is_first = request.args.get('is_first')
    # date_stamp = ''
    # date_stamp = request.args.get('date_stamp')
    aml_id = request.args.get('aml_id')
    sml_id = request.args.get('sml_id')
    # if date_stamp:
    #     # แปลงเป็น datetime object
    #     input_date = datetime.strptime(date_stamp , "%a, %d %b %Y %H:%M:%S %Z")

    #     # # กำหนดเขตเวลาเป็น GMT
    #     # input_date = input_date.replace(tzinfo=pytz.UTC)

    #     # แปลงเป็นเขตเวลาท้องถิ่น (กรุงเทพ)
    #     # local_timezone = pytz.timezone("Asia/Bangkok")
    #     # local_date = input_date.astimezone(local_timezone)
    #     # new_date = input_date - timedelta(hours=7)
    #     # แปลงเป็นรูปแบบ "dd/mm/yyyy hh:mm:ss"
    #     date_stamp = input_date.strftime("%Y-%m-%d %H:%M:%S")

    if limit == '':
        limit_sql = ''
    else :
        limit_sql = 'LIMIT '+ limit

    if dropdown == '':
        search_area = ''
    else:
        search_area = 'and rcb.id = %s' %(dropdown)
    # if is_first == 'true':
    #     date_from = date_from + ' ' + '00:00:00'
    # else:
    #     date_from = date_stamp

    date_from = date_from + ' ' + '00:00:00'
    date_to = date_to + ' ' + '23:59:59'
    
    # print("date_stamp = ",date_stamp)
    # if is_first == 'true':
    #     global_date_stamp = []
    # global_date_stamp = date_from
     
    if date_from and date_to:
        if date_from > date_to:
            print("วันเริ่มต้นต้องมากกว่าวันสิ้นสุดเสมอ")
            return render_template('index.html', data=data, error_message="วันเริ่มต้นต้องมากกว่าวันสิ้นสุดเสมอ")
        else:
            # SQL
            try:
                connection = pyodbc.connect(connection_string)
                cursor = connection.cursor()
                ############################################################ So query ############################################################
                sql_query = """with CombineTaxesSo as (
                    select
                        STRING_AGG(distinct at.name, ', ') as name,
                        sol_sup.id
                    from
                        sale_order_line sol_sup
                    left join account_tax_sale_order_line_rel atsolr on atsolr.sale_order_line_id = sol_sup.id
                    left join account_tax at on at.id = atsolr.account_tax_id
                    group by sol_sup.id
                ),
                CombineTaxesPo as (
                    select
                        STRING_AGG(distinct at.name, ', ') as name,
                        pos_line_sup.id
                    from
                        pos_order_line pos_line_sup
                    left join account_tax_pos_order_line_rel atpolr on atpolr.pos_order_line_id = pos_line_sup.id
                    left join account_tax at on at.id = atpolr.account_tax_id
                    group by pos_line_sup.id
                ),
                StockMoveLineSo as (
					SELECT 
                        sml_sub.id,
                        sml_sub.move_id,
                        sml_sub.lot_id,
                        sml_sub.qty_done,
                        sml_sub.location_id,
                        sml_sub.location_dest_id,
                        sml_sub.picking_id,
                        sml_sub.product_id,
                        ROW_NUMBER() OVER (PARTITION BY sml_sub.id ORDER BY sml_sub.id) AS rn
                    FROM
                        stock_move_line sml_sub
				),
                StockMoveLinePos as (
                	SELECT DISTINCT ON (sml_sub.picking_id, sml_sub.product_id)
                        sml_sub.id,
                        sml_sub.lot_id,
                        sml_sub.qty_done,
                        sml_sub.location_id,
                        sml_sub.location_dest_id,
                        sml_sub.picking_id,
                        sml_sub.product_id
                    FROM stock_move_line sml_sub
                ),
				StockPicking as (
					SELECT
     					sp1.id AS id,
 						sp1.name,
 						sp1.state,
     					sp1.pos_order_id as pos_order_id,
     					sp1.is_picking_combo as is_picking_combo,
     					ROW_NUMBER() OVER (PARTITION BY sp1.pos_order_id ORDER BY sp1.create_date ASC) AS row_num
     				FROM
     					stock_picking sp1
				)                
                select
                    so.date_order + interval '7 hours' as posting_date,
                    case
                        when am.state = 'draft' then 'Draft'
                        when am.state = 'posted' then 'Posted'
                        when am.state = 'cancel' then 'Cancel'
                    end as doc_type,
                    null as document_no,
                    am.name as tax_invoice_download,
                    so.name as external_document_no,
                    rp_so.name as sell_to_customer_name,
                    rp_so.street || ' ' || rp_so.street2 || ' ' || rp_so.city as sell_to_address,
                    rp_so.tax_name as bill_to_customer_name,
                    rp_so.tax_street as e_file_address,
                    rp_so.tax_street2 as e_file_address_2,
                    rp_so.vat as tax_id,
                    rp_so.mobile as phone,
                    spt.name as customer_posting_group,
                    rcb.code as location_code,
                    rcb.name as location_name,
                    rcbg.name as location_group_code,
                    ru_am.login as area_manager,
                    rp_am.name as area_name,
                    ru.login as saleperson_code,
                    rp_sale.name as saleperson_name,
                    pt.default_code as no,
                    pp.product_name as full_description,
                    pb.name as brand,
                    cpm.name as model,
                    case
	                    when am.move_type in('out_invoice') and sm.product_uom_qty is null and am.payment_state != 'not_paid' then ROUND(sol.product_uom_qty, 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty > 1 and am.payment_state != 'not_paid' then ROUND(sol.product_uom_qty/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty > 1 and am.payment_state != 'not_paid' then ROUND(-sol.product_uom_qty/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty is null and am.payment_state != 'not_paid' then ROUND(-sol.price_total, 3)
						when sol.product_uom_qty != 0 and am.move_type in('out_invoice') and sm.product_uom_qty = 1 and am.payment_state != 'not_paid' then ROUND(sol.product_uom_qty/abs(sol.product_uom_qty), 3)
                   		when sol.product_uom_qty != 0 and am.move_type in('out_refund') and sm.product_uom_qty = 1 and am.payment_state != 'not_paid' then ROUND(-sol.product_uom_qty/abs(sol.product_uom_qty), 3)
                   		when am.move_type in('out_invoice') and sm.product_uom_qty is null and am.payment_state = 'not_paid' then ROUND(sol.product_uom_qty, 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty > 1 and am.payment_state = 'not_paid' then ROUND(sol.product_uom_qty/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty is null and am.payment_state = 'not_paid' then ROUND(-sol.product_uom_qty, 3)
						when am.move_type in('out_refund') and sm.product_uom_qty > 1 and am.payment_state = 'not_paid' then ROUND(-sol.product_uom_qty/abs(sm.product_uom_qty), 3)
						when sol.product_uom_qty != 0 and am.move_type in('out_refund') and sm.product_uom_qty = 1 and am.payment_state = 'not_paid' then 0
						when am.id is null and sml.qty_done is null then ROUND(sol.product_uom_qty, 3)
						when sol.product_uom_qty != 0 and am.id is null and sml.qty_done = 1 then ROUND(sol.product_uom_qty/abs(sol.product_uom_qty), 3)
					    else ROUND(sol.product_uom_qty, 3)
                    end as quantity,
                   sol.price_unit as unit_price,
                    case
                        when am.move_type in('out_invoice') and sm.product_uom_qty is null and am.payment_state != 'not_paid' then ROUND(sol.price_subtotal, 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty > 1 and am.payment_state != 'not_paid' then ROUND(sol.price_subtotal, 3)
						when am.move_type in('out_refund') and sm.product_uom_qty > 1 and am.payment_state != 'not_paid' then ROUND(-sol.price_subtotal, 3)
						when am.move_type in('out_refund') and sm.product_uom_qty is null and am.payment_state != 'not_paid' then ROUND(-sol.price_total, 3)
						when sol.product_uom_qty != 0 and am.move_type in('out_invoice') and sm.product_uom_qty = 1 and am.payment_state != 'not_paid' then ROUND(sol.price_subtotal/abs(sol.product_uom_qty), 3)
                   		when sol.product_uom_qty != 0 and am.move_type in('out_refund') and sm.product_uom_qty = 1 and am.payment_state != 'not_paid' then ROUND(-sol.price_subtotal/abs(sol.product_uom_qty), 3)
                   		when am.move_type in('out_invoice') and sm.product_uom_qty is null and am.payment_state = 'not_paid' then ROUND(sol.price_subtotal, 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty > 1 and am.payment_state = 'not_paid' then ROUND(sol.price_subtotal/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty is null and am.payment_state = 'not_paid' then ROUND(-sol.price_subtotal, 3)
						when am.move_type in('out_refund') and sm.product_uom_qty > 1 and am.payment_state = 'not_paid' then ROUND(-sol.price_subtotal/abs(sm.product_uom_qty), 3)
						when sol.product_uom_qty != 0 and am.move_type in('out_refund') and sm.product_uom_qty = 1 and am.payment_state = 'not_paid' then 0
						when am.id is null and sml.qty_done is null then ROUND(sol.price_subtotal, 3)
						when sol.product_uom_qty != 0 and am.id is null and sml.qty_done = 1 then ROUND(sol.price_subtotal/abs(sol.product_uom_qty), 3)
					    else ROUND(sol.price_subtotal, 3)
                    end as subtotal_wo_tax,
                   	case
						when am.move_type in('out_invoice') and sm.product_uom_qty is null and am.payment_state != 'not_paid' then ROUND(sol.price_total, 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty > 1 and am.payment_state != 'not_paid' then ROUND(sol.price_total/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty > 1 and am.payment_state != 'not_paid' then ROUND(-sol.price_total/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty is null and am.payment_state != 'not_paid' then ROUND(-sol.price_total, 3)
						when sol.product_uom_qty != 0 and am.move_type in('out_invoice') and sm.product_uom_qty = 1 and am.payment_state != 'not_paid' then ROUND(sol.price_total/abs(sol.product_uom_qty), 3)
                   		when sol.product_uom_qty != 0 and am.move_type in('out_refund') and sm.product_uom_qty = 1 and am.payment_state != 'not_paid' then ROUND(-sol.price_total/abs(sol.product_uom_qty), 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty is null and am.payment_state = 'not_paid' then ROUND(sol.price_total, 3)
						when am.move_type in('out_invoice') and sm.product_uom_qty > 1 and am.payment_state = 'not_paid' then ROUND(sol.price_total/abs(sm.product_uom_qty), 3)
						when am.move_type in('out_refund') and sm.product_uom_qty is null and am.payment_state = 'not_paid' then ROUND(-sol.price_total, 3)
						when am.move_type in('out_refund') and sm.product_uom_qty > 1 and am.payment_state = 'not_paid' then ROUND(-sol.price_total/abs(sm.product_uom_qty), 3)
						when sol.product_uom_qty != 0 and am.move_type in('out_refund') and sm.product_uom_qty = 1 and am.payment_state = 'not_paid' then 0
						when am.id is null and sml.qty_done is null then ROUND(sol.price_total, 3)
						when sol.product_uom_qty != 0 and am.id is null and sml.qty_done = 1 then ROUND(sol.price_total/abs(sol.product_uom_qty), 3)
					    else ROUND(sol.price_total, 3)
				    end as price_subtotal,
                    0 as unit_cost_lcy,
                    uu.name as unit_of_measure,
                    cbtso.name as vat_7,
                    cig.name as inventory_posting_group,
                    s_pro_l.name as imei,
                    so.note as meno,
					null as payment_methods,
                    null as combined_names,
                    null as card_no,
                    rp_sale.name as user_id,
                    sp.name as picking_number,
                    case
                        when sp.state = 'draft' then 'Draft'
                        when sp.state = 'waiting' then 'Waiting Another Operation'
                        when sp.state = 'confirmed' then 'Waiting'
                        when sp.state = 'assinged' then 'Ready'
                        when sp.state = 'done' then 'Done'
                        when sp.state = 'cancel' then 'Cancelled'
                    end as picking_state,
                    sol.pos_note as note,
                    sol.so_amount_total as amount_total,
                    0 as pos_order_id,
                    '0',
                    '0',
                    am.id as am_id,
                    aml.id as aml_id,
                    sml.id as sml_id,
                    pp.id as product_id,
                    null as pos_id
                from
						sale_order so
					left join sale_order_line sol on sol.order_id = so.id
                    left join sale_order_line_invoice_rel solir on solir.order_line_id = sol.id
					left join account_move_line aml on aml.id = solir.invoice_line_id
					left join account_move am on am.id = aml.move_id
                    left join stock_move sm on sm.sale_line_id = sol.id and sm.state = 'done' and sm.to_refund is not true
                    left join StockMoveLineSo as sml on sml.move_id = sm.id and rn = 1
                    left join product_product pp on pp.id = sml.product_id
                    left join product_product pp_order on pp_order.id = sol.product_id
                    left join product_template pt on pt.id = pp_order.product_tmpl_id 
                    left join product_category pc on pt.categ_id = pc.id
                    left join product_brand pb on pb.id = pt.cu_product_brand_id
                    left join uom_uom uu on uu.id = pt.uom_id
                    left join cu_product_model cpm on pb.id = pt.cu_product_model_id
                    left join stock_picking sp on sp.id = sm.picking_id
                    left join stock_production_lot s_pro_l on s_pro_l.id = sml.lot_id
                    left join stock_location sl on sl.id = sm.location_dest_id and sl.usage = 'customer'
                    left join res_partner rp_so on rp_so.id = so.partner_id
                    left join account_tax atax on atax.id = sol.task_id
                    left join cu_inventory_group cig on cig.id = pt.inventory_group_id
                    left join res_company_branches rcb on rcb.id = so.company_branch_id
                    left join res_company_branch_group rcbg on rcbg.id = rcb.company_branch_group_id
                    left join res_partner rp_am on rp_am.id = rcb.area_manager_id
                    left join res_users ru_am on ru_am.partner_id = rp_am.id
                    left join res_users ru on ru.id = so.user_id
                    left join res_partner rp_sale on rp_sale.id = ru.partner_id
                    left join CombineTaxesSo cbtso on cbtso.id = sol.id
                    left join sale_purchase_types spt on spt.id = am.sale_purchase_type_id 
                where so.invoice_status in ('to invoice','invoiced','no')
				and so.state in ('done','sale')
                and so.date_order + interval '7 hours' >= '%s'
                and so.date_order + interval '7 hours' <= '%s'%s               
                union all
                select
                    pos.date_order + interval '7 hours' as posting_date,
                    case
                            when pos.state = 'draft' then 'Draft'
                            when pos.state = 'cancel' then 'Cancel'
                            when pos.state = 'paid' then 'Paid'
                            when pos.state = 'done' then 'Posted'
                            when pos.state = 'invoiced' then 'Invoiced'
                            when pos.state = 'quotation' then 'Quotation'
                        end as doc_type,
                    pos.pos_reference  as document_no,
                    am.name as tax_invoice_download,
                    pos.name as external_document_no,
                    rp_pos.name as sell_to_customer_name,
                    rp_pos.street || ' ' || rp_pos.street2 || ' ' || rp_pos.city as sell_to_address,
                    rp_pos.tax_name as bill_to_customer_name,
                    rp_pos.tax_street as e_file_address,
                    rp_pos.tax_street2 as e_file_address_2,
                    rp_pos.vat as tax_id,
                    rp_pos.mobile as phone,
                    spt.name as customer_posting_group,
                    rcb.code as location_code,
                    rcb.name as location_name,
                    rcbg.name as location_group_code,
                    ru_am.login as area_manager,
                    rp_am.name as area_name,
                    ru.login as saleperson_code,
                    rp_sale.name as saleperson_name,
                    pt.default_code as no,
                    pp.product_name as full_description,
                    pb.name as brand,
                    cpm.name as model,
                    case
						when am.move_type in('out_invoice') and sml.qty_done is null then ROUND(pos_line.qty, 3)
						when am.move_type in('out_refund') and sml.qty_done is null then ROUND(pos_line.qty, 3)
						when pos_line.qty != 0 and am.move_type in('out_invoice') and sml.qty_done = 1 then ROUND(pos_line.qty/abs(pos_line.qty), 3)
                   		when pos_line.qty != 0 and am.move_type in('out_refund') and sml.qty_done = 1 then ROUND(pos_line.qty/abs(pos_line.qty), 3)
						when am.id is null and sml.qty_done is null then ROUND(pos_line.qty, 3)
						when pos_line.qty != 0 and am.id is null and sml.qty_done = 1 then ROUND(pos_line.qty/abs(pos_line.qty), 3)
						else ROUND(pos_line.qty, 3)
                    end as quantity,
                    ROUND(pos_line.price_unit, 3) as unit_price,
                    case
					 	when am.move_type in('out_invoice') and sml.qty_done is null then ROUND(pos_line.price_subtotal, 3)
						when am.move_type in('out_refund') and sml.qty_done is null then ROUND(pos_line.price_subtotal, 3)
						when pos_line.qty != 0 and am.move_type in('out_invoice') and sml.qty_done = 1 then ROUND(pos_line.price_subtotal/abs(pos_line.qty), 3)
                   		when pos_line.qty != 0 and am.move_type in('out_refund') and sml.qty_done = 1 then ROUND(pos_line.price_subtotal/abs(pos_line.qty), 3)
						when am.id is null and sml.qty_done is null then ROUND(pos_line.price_subtotal, 3)
						when pos_line.qty != 0 and am.id is null and sml.qty_done = 1 then ROUND(pos_line.price_subtotal/abs(pos_line.qty), 3)
						else ROUND(pos_line.price_subtotal, 3)
                    end as subtotal_wo_tax,
                    case
						when am.move_type in('out_invoice') and sml.qty_done is null then ROUND(pos_line.price_subtotal_incl, 3)
						when am.move_type in('out_refund') and sml.qty_done is null then ROUND(pos_line.price_subtotal_incl, 3)
						when pos_line.qty != 0 and am.move_type in('out_invoice') and sml.qty_done = 1 then ROUND(pos_line.price_subtotal_incl/abs(pos_line.qty), 3)
                   		when pos_line.qty != 0 and am.move_type in('out_refund') and sml.qty_done = 1 then ROUND(pos_line.price_subtotal_incl/abs(pos_line.qty), 3)
						when am.id is null and sml.qty_done is null then ROUND(pos_line.price_subtotal_incl, 3)
						when pos_line.qty != 0 and am.id is null and sml.qty_done = 1 then ROUND(pos_line.price_subtotal_incl/abs(pos_line.qty), 3)
						else ROUND(pos_line.price_subtotal_incl, 3)
				  	end as price_subtotal,
                    0 as unit_cost_lcy,
                    uu.name as unit_of_measure,
                    cbtpo.name as vat_7,
                    cig.name as inventory_posting_group,
                    s_pro_l.name as imei,
                    pos.note as meno,
                    rp_sale.name as user_id,
                    null as payment_methods,
                    null as combined_names,
                    null as card_no,
                    sp.name as picking_number,
                    case
                        when sp.state = 'draft' then 'Draft'
                        when sp.state = 'waiting' then 'Waiting Another Operation'
                        when sp.state = 'confirmed' then 'Waiting'
                        when sp.state = 'assinged' then 'Ready'
                        when sp.state = 'done' then 'Done'
                        when sp.state = 'cancel' then 'Cancelled'
                    end as picking_state,  
                    pos_line.note as note,
                    pos.amount_total as amount_total,                     
                    0 as pos_order_id,
                    '0',
                    '0',
                    am.id as am_id,
                    null as aml_id,
                    sml.id as sml_id,
                    pp.id as product_id,
                    pos.id as pos_id
	                from (
                               SELECT 
                                   pos_line.order_id,pos_line.note,pos_line.product_id,pos_line.id,pos_line.qty,pos_line.price_unit,pos_line.price_subtotal,pos_line.price_subtotal_incl,
                                   ROW_NUMBER() OVER (PARTITION BY pos_line.order_id, pos_line.product_id ORDER BY pos_line.id) AS rn
                               FROM
                                   pos_order_line pos_line
                          ) pos_line
                    left join pos_order pos on pos.id = pos_line.order_id 
                    left join account_move am on am.id = pos.account_move and am.move_type in ('out_invoice','out_refund')
					LEFT JOIN StockPicking sp ON sp.row_num = 1 AND sp.pos_order_id = pos.id and sp.is_picking_combo is not false
                    left join product_product pp on pp.id = pos_line.product_id
                    left join product_template pt on pt.id = pp.product_tmpl_id
                    left join product_category pc on pt.categ_id = pc.id
                    left join product_brand pb on pb.id = pt.cu_product_brand_id
                    LEFT JOIN StockMoveLinePos as sml ON sml.picking_id = sp.id AND sml.product_id = pp.id AND pos_line.rn = 1                  
                    left join stock_production_lot s_pro_l on s_pro_l.id = sml.lot_id
                    left join uom_uom uu on uu.id = pt.uom_id
                    left join cu_product_model cpm on cpm.id = pt.cu_product_model_id
                    left join res_partner rp_pos on rp_pos.id = pos.partner_id
                    left join cu_inventory_group cig on cig.id = pt.inventory_group_id
                    left join res_company_branches rcb on rcb.id = pos.company_branch_id
                    left join res_company_branch_group rcbg on rcbg.id = rcb.company_branch_group_id
                    left join res_partner rp_am on rp_am.id = rcb.area_manager_id
                    left join res_users ru_am on ru_am.partner_id = rp_am.id
                    left join res_users ru on ru.id = pos.user_id
                    left join res_partner rp_sale on rp_sale.id = ru.partner_id
                    left join CombineTaxesPo cbtpo on cbtpo.id = pos_line.id
                    left join stock_location sl on sl.id = sml.location_id
                    left join stock_location sld on sld.id = sml.location_dest_id
                    left join sale_purchase_types spt on spt.id = am.sale_purchase_type_id 
				where pos.state in ('paid','done','invoiced') and pos.amount_paid != 0
                and pos.date_order + interval '7 hours' >= '%s'
                and pos.date_order + interval '7 hours' <=  '%s'%s                       
                    """% (date_from,date_to,search_area,date_from,date_to,search_area)
                # print(sql_query)
                # connection = db.session.connection()  # เปิด Connection
                # result = connection.execute(sql_query)
                cursor.execute(sql_query)
                result = cursor.fetchall()
                data = [{
                            'posting_date': item.posting_date.strftime('%d/%m/%Y'), 
                            'doc_type': item.doc_type, 
                            'document_no': item.document_no,
                            'tax_invoice_download': item.tax_invoice_download,
                            'external_document_no': item.external_document_no,
                            'sell_to_customer_name': item.sell_to_customer_name,
                            'sell_to_address': item.sell_to_address,
                            'bill_to_customer_name': item.bill_to_customer_name,
                            'e_file_address': item.e_file_address,
                            'e_file_address_2': item.e_file_address_2,
                            'tax_id': item.tax_id if item.tax_id is not None or 'None' else '-',
                            'phone': item.phone if item.phone is not None or 'None' else '-',
                            'customer_posting_group': item.customer_posting_group,
                            'location_code': item.location_code,
                            'location_name': item.location_name,
                            'location_group_code': item.location_group_code,
                            'area_manager': item.area_manager,
                            'area_name': item.area_name,
                            'saleperson_code': item.saleperson_code,
                            'saleperson_name': item.saleperson_name,
                            'no': item.no,
                            'full_description': item.full_description,
                            'brand': item.brand,
                            'model': item.model,
                            'quantity': round(float(item.quantity) if item.quantity is not None else 0, 3),
                            'unit_price': round(float(item.unit_price) if item.unit_price is not None else 0, 3),
                            'subtotal_wo_tax': round(float(item.subtotal_wo_tax) if item.subtotal_wo_tax is not None else 0, 3),
                            'price_subtotal': round(float(item.price_subtotal) if item.price_subtotal is not None else 0, 3),
                            'unit_cost_lcy': item.unit_cost_lcy,
                            'unit_of_measure': item.unit_of_measure,
                            'vat_7': item.vat_7,
                            'inventory_posting_group': item.inventory_posting_group,
                            'imei': str(item.imei) if item.imei is not None else '-',
                            'meno': item.meno if item.meno is not None else '-',
                            'user_id': item.user_id,
                            'payment_method': '-',
                            'bank_list': '-',
                            'card_number': '-',
                            'picking_number': item.picking_number,
                            'picking_state': item.picking_state,
                            'note': item.note,
                            'amount_total': item.amount_total,
                            'am_id':item.am_id,
                            'aml_id':item.aml_id,
                            'sml_id':item.sml_id,
                            'product_id':item.product_id,
                            'pos_id':item.pos_id,
                            'po_date_order': None ,
                            'partner_name': None,
                        } for item in result]
                # if data:
                #     global_date_stamp = data[-1]['posting_date']
                # if str(global_date_stamp) == str(date_stamp):
                #     data = []
                print("SO Order การเชื่อมต่อฐานข้อมูลสำเร็จ")
            except Exception as e:
                print("SO Order การเชื่อมต่อฐานข้อมูลไม่สำเร็จ:", str(e))
            finally:
                connection.close()  # ปิด Connection
    return jsonify(data)