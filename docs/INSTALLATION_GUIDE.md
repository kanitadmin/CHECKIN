# คู่มือการติดตั้งระบบลงเวลาเข้า-ออกงาน

## ข้อกำหนดของระบบ

### ซอฟต์แวร์ที่จำเป็น
- Python 3.8 หรือสูงกว่า
- MySQL 5.7 หรือสูงกว่า (หรือ MariaDB 10.2+)
- Git (สำหรับดาวน์โหลดโค้ด)

### บัญชี Google OAuth
- Google Cloud Console Project
- OAuth 2.0 Client ID และ Client Secret

## ขั้นตอนการติดตั้ง

### 1. ดาวน์โหลดโค้ด

```bash
git clone <repository-url>
cd attendance-system
```

### 2. ติดตั้ง Python Dependencies

```bash
# สร้าง virtual environment (แนะนำ)
python -m venv venv

# เปิดใช้งาน virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# ติดตั้ง packages
pip install -r requirements.txt
```

### 3. ตั้งค่าฐานข้อมูล MySQL

#### สร้างฐานข้อมูลและผู้ใช้

```sql
-- เข้าสู่ MySQL ด้วยสิทธิ์ root
mysql -u root -p

-- สร้างฐานข้อมูล
CREATE DATABASE checkin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้างผู้ใช้สำหรับแอปพลิเคชัน
CREATE USER 'checkin'@'localhost' IDENTIFIED BY 'your_secure_password';

-- ให้สิทธิ์เข้าถึงฐานข้อมูล
GRANT ALL PRIVILEGES ON checkin.* TO 'checkin'@'localhost';
FLUSH PRIVILEGES;

-- ออกจาก MySQL
EXIT;
```

### 4. ตั้งค่า Google OAuth

#### สร้าง Google Cloud Project
1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้าง Project ใหม่หรือเลือก Project ที่มีอยู่
3. เปิดใช้งาน Google+ API

#### ตั้งค่า OAuth 2.0
1. ไปที่ **APIs & Services > Credentials**
2. คลิก **Create Credentials > OAuth 2.0 Client IDs**
3. เลือก **Web application**
4. ตั้งค่า:
   - **Authorized JavaScript origins**: `http://localhost:5000`
   - **Authorized redirect URIs**: `http://localhost:5000/auth/callback`
5. บันทึก Client ID และ Client Secret

### 5. ตั้งค่าไฟล์ Environment

```bash
# คัดลอกไฟล์ template
cp .env.template .env
```

แก้ไขไฟล์ `.env`:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=development

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=checkin
DB_USER=checkin
DB_PASSWORD=your_secure_password

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
HOSTED_DOMAIN=your-company-domain.com

# Application Configuration
REDIRECT_URI=http://localhost:5000/auth/callback
```

### 6. เริ่มต้นฐานข้อมูล

```bash
python database.py
```

สคริปต์นี้จะ:
- สร้างตารางที่จำเป็นทั้งหมด
- ตั้งค่า indexes และ constraints
- ตรวจสอบการเชื่อมต่อฐานข้อมูล

### 7. สร้างผู้ดูแลระบบ (Admin)

```bash
python create_admin.py
```

ทำตามขั้นตอนในสคริปต์เพื่อ:
- ดูรายชื่อผู้ใช้ที่มีอยู่
- เลือกผู้ใช้ที่จะให้สิทธิ์ admin

### 8. ทดสอบการติดตั้ง

```bash
# รันแอปพลิเคชัน
python app.py
```

เปิดเบราว์เซอร์ไปที่: `http://localhost:5000`

## การตั้งค่าสำหรับ Production

### 1. ตั้งค่า Environment Variables

```env
FLASK_ENV=production
FLASK_SECRET_KEY=very-secure-production-key
```

### 2. ตั้งค่า Web Server

#### ใช้ Gunicorn (แนะนำ)

```bash
# ติดตั้ง Gunicorn
pip install gunicorn

# รันแอปพลิเคชัน
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### ตั้งค่า Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. ตั้งค่า SSL Certificate

```bash
# ใช้ Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 4. ตั้งค่า Systemd Service

สร้างไฟล์ `/etc/systemd/system/attendance.service`:

```ini
[Unit]
Description=Attendance System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/attendance-system
Environment=PATH=/path/to/attendance-system/venv/bin
ExecStart=/path/to/attendance-system/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

เปิดใช้งาน service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance
sudo systemctl start attendance
```

## การแก้ไขปัญหาที่พบบ่อย

### ปัญหาการเชื่อมต่อฐานข้อมูล

```bash
# ตรวจสอบการเชื่อมต่อ
python -c "from database import test_connection; test_connection()"
```

**แก้ไข:**
- ตรวจสอบ username/password ในไฟล์ `.env`
- ตรวจสอบว่า MySQL service ทำงานอยู่
- ตรวจสอบ firewall settings

### ปัญหา Google OAuth

**Error: redirect_uri_mismatch**
- ตรวจสอบ redirect URI ใน Google Console
- ตรวจสอบ domain ใน `.env`

**Error: access_denied**
- ตรวจสอบ HOSTED_DOMAIN ใน `.env`
- ตรวจสอบว่าอีเมลผู้ใช้อยู่ใน domain ที่กำหนด

### ปัญหา Permission

```bash
# ตั้งค่า permissions สำหรับ production
sudo chown -R www-data:www-data /path/to/attendance-system
sudo chmod -R 755 /path/to/attendance-system
```

## การสำรองข้อมูล

### สำรองฐานข้อมูล

```bash
# สำรองข้อมูลรายวัน
mysqldump -u checkin -p checkin > backup_$(date +%Y%m%d).sql

# สำรองข้อมูลแบบอัตโนมัติ (crontab)
0 2 * * * mysqldump -u checkin -p'password' checkin > /backup/attendance_$(date +\%Y\%m\%d).sql
```

### สำรองไฟล์ระบบ

```bash
# สำรองไฟล์ configuration
tar -czf config_backup.tar.gz .env static/ templates/
```

## การอัปเดตระบบ

```bash
# ดึงโค้ดใหม่
git pull origin main

# อัปเดต dependencies
pip install -r requirements.txt

# รัน database migration (ถ้ามี)
python database.py

# รีสตาร์ท service
sudo systemctl restart attendance
```

## การตรวจสอบ Logs

```bash
# ดู application logs
tail -f /var/log/attendance/app.log

# ดู system service logs
sudo journalctl -u attendance -f

# ดู nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## การติดต่อสำหรับความช่วยเหลือ

หากพบปัญหาในการติดตั้ง กรุณาตรวจสอบ:
1. Log files สำหรับข้อผิดพลาด
2. การตั้งค่าในไฟล์ `.env`
3. การเชื่อมต่อฐานข้อมูลและ Google OAuth

สำหรับปัญหาที่ซับซ้อน กรุณาติดต่อทีมพัฒนาระบบพร้อมแนบ log files และรายละเอียดข้อผิดพลาด