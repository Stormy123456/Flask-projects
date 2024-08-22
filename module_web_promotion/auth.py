import requests
import json
from flask import session, redirect, url_for, flash, request, render_template

class AuthModule:
    def __init__(self, api_url):
        self.api_url = api_url

    def login(self, employee_code, password):
    # เตรียม payload สำหรับ API request
        payload = {
            "employee_code": employee_code,
            "pass_user": password
        }
        headers = {
            'Content-Type': 'application/json'
        }

        # ส่ง request ไปที่ API
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            print(response.status_code)
            print(response.text)  # ใช้ text หาก JSON ไม่สามารถแปลงได้
            if response.status_code == 200:
            # รับข้อมูลผู้ใช้จาก API
                user_data = response.json()
                
                # ตรวจสอบสถานะความสำเร็จ
                if user_data.get('status') == 'success':
                    # ตรวจสอบ type_status ของผู้ใช้
                    if user_data.get('type_status') != '3':
                        flash('Access denied: insufficient permissions.')
                        return False
                
                    # เก็บข้อมูลผู้ใช้ใน session
                    session['employee_code'] = user_data.get('employee_code')
                    session['name_user'] = user_data.get('name_user')
                    session['brance_code'] = user_data.get('brance_code')
                    session['brance_name'] = user_data.get('brance_name')
                    session['type_status'] = user_data.get('type_status')
                    return True
                
                else:
                        flash('Login failed: ' + user_data.get('message', 'Unknown error'))
                        return False

            else:
                flash('Login failed. Please check your credentials.')
                return False

        except requests.exceptions.RequestException as e:
            flash(f"An error occurred: {str(e)}")
            return False

    def logout(self):
        # ลบข้อมูล session เมื่อผู้ใช้ทำการออกจากระบบ
        session.pop('employee_code', None)
        session.pop('name_user', None)
        session.pop('brance_code', None)
        session.pop('brance_name', None)
        session.pop('type_status', None)
        return redirect(url_for('login'))
