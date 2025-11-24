# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd # type: ignore
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File lưu trữ danh bạ
DATA_FILE = 'contacts.xlsx'

# Tạo file Excel mẫu nếu chưa có
def init_db():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=['Tên', 'Số điện thoại', 'Email'])
        df.to_excel(DATA_FILE, index=False)

# Đọc danh bạ
# Đọc danh bạ – phiên bản chống lỗi 100%
def load_contacts():
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        df = pd.read_excel(DATA_FILE)
        # Ép tất cả về chuỗi, thay NaN bằng chuỗi rỗng
        df = df.fillna('')
        df = df.astype(str)
        
        # Đảm bảo có đủ 3 cột
        for col in ['Tên', 'Số điện thoại', 'Email']:
            if col not in df.columns:
                df[col] = ''
        
        contacts = df[['Tên', 'Số điện thoại', 'Email']].to_dict('records')
        return contacts
    except:
        # Nếu file hỏng hoàn toàn thì trả về danh bạ rỗng
        return []

# Lưu danh bạ
def save_contacts(contacts):
    df = pd.DataFrame(contacts)
    df.to_excel(DATA_FILE, index=False)

@app.route('/')
def index():
    raw_query = request.args.get('q', '')
    query = raw_query.strip().lower()
    contacts = load_contacts()
    
    if query:
        contacts = [c for c in contacts if (
            query in (c.get('Tên') or '').lower() or
            query in c.get('Số điện thoại', '') or
            query in (c.get('Email') or '').lower()
        )]
    
    return render_template('index.html', contacts=contacts, query=raw_query)

@app.route('/add', methods=['POST'])
def add():
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    email = request.form['email'].strip().lower()

    if not name or not phone:
        flash('Tên và số điện thoại là bắt buộc!', 'danger')
    else:
        contacts = load_contacts()
        # Kiểm tra trùng số điện thoại
        if any(c['Số điện thoại'] == phone for c in contacts):
            flash('Số điện thoại đã tồn tại!', 'warning')
        else:
            contacts.append({'Tên': name, 'Số điện thoại': phone, 'Email': email})
            save_contacts(contacts)
            flash('Thêm liên hệ thành công!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<phone>')
def delete(phone):
    contacts = load_contacts()
    contacts = [c for c in contacts if c['Số điện thoại'] != phone]
    save_contacts(contacts)
    flash('Đã xóa liên hệ!', 'info')
    return redirect(url_for('index'))

@app.route('/edit/<phone>', methods=['GET', 'POST'])
def edit(phone):
    contacts = load_contacts()
    contact = next((c for c in contacts if c['Số điện thoại'] == phone), None)

    if request.method == 'POST':
        new_name = request.form['name'].strip()
        new_phone = request.form['phone'].strip()
        new_email = request.form['email'].strip().lower()

        if not new_name or not new_phone:
            flash('Tên và số điện thoại không được để trống!', 'danger')
        elif new_phone != phone and any(c['Số điện thoại'] == new_phone for c in contacts):
            flash('Số điện thoại mới đã tồn tại!', 'warning')
        else:
            # Cập nhật
            for c in contacts:
                if c['Số điện thoại'] == phone:
                    c['Tên'] = new_name
                    c['Số điện thoại'] = new_phone
                    c['Email'] = new_email
            save_contacts(contacts)
            flash('Cập nhật thành công!', 'success')
            return redirect(url_for('index'))

    return render_template('edit.html', contact=contact)

@app.route('/export')
def export():
    return send_file(DATA_FILE, as_attachment=True, download_name=f"DanhBa_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)