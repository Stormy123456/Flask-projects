from flask import Flask, render_template, request, redirect, Response, jsonify, send_file
from config_db import connection_string
from pyexcelerate import Workbook
import pyodbc 
import pandas as pd
import json


def print_gi_data_report():
    data = []
    min_date = request.args.get('date_from')
    max_date = request.args.get('date_to')
    category = request.args.get('category')
    min_date = min_date + ' ' + '00:00:00'
    max_date = max_date + ' ' + '23:59:59'
    if min_date and max_date:
        # SQL 
        try:
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            ############################################################ So query ############################################################
            sql_query = f"""select
                                 aa.code as code,
                                 am.id as order_id,
                                 am.date  + interval '7 hours' as date ,
                                 rc.name as company,
                                 rcb.name as branch,
                                 am.name as journal_entry,
                                 rp.name as partner,
                                 aml.name as label_name,
                                 aml.matching_number as matching,
                                 aaa.name as analytic_account,
                                 aml.debit as debit,
                                 aml.credit as credit,
                                 aml.balance as balance,
                                 aml.amount_currency as amount_in_currency,
                                 am.state as state
                                from account_move_line aml
                                join account_move am on am.id = aml.move_id 
                                left join account_analytic_account aaa on aaa.id = aml.analytic_account_id 
                                left join res_company rc on rc.id = aml.company_id 
                                left join res_company_branches rcb on rcb.id = aml.company_branch_id 
                                left join res_partner rp on rp.id = aml.partner_id 
                                left join account_account aa on aa.id = aml.account_id
                                where am.state = 'posted'
                                and aa.code like '{category}%'
                                and am."date" + interval '7 hours' >= '{min_date}'
                                and am."date" + interval '7 hours' <= '{max_date}'
                                order by  aa.code ASC
                        """
            cursor.execute(sql_query)
            result = cursor.fetchall()
            data = [{
                        'code': item.code,
                        'order_id': item.order_id,
                        'date': item.date,
                        'company': item.company,
                        'branch': item.branch,
                        'journal_entry': item.journal_entry,
                        'partner': item.partner,
                        'label_name': item.label_name,
                        'matching': item.matching,
                        'analytic_account': item.analytic_account,
                        'debit': item.debit,
                        'credit': item.credit,
                        'balance': item.balance,
                        'amount_in_currency': item.amount_in_currency,
                        'state': item.state
                    } for item in result]
            print("GI is Success")
        except Exception as e:
            print("GI Error:", str(e))
        finally:
            connection.close()  # ปิด Connection   
            
    return jsonify({
        'data_gi': data
    })