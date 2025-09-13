# 🕐 ระบบลงเวลาเข้า-ออกงาน (Employee Check-in System)

ระบบลงเวลาทำงานสำหรับพนักงาน พร้อมระบบตรวจสอบตำแหน่ง GPS และการจัดการผ่านหน้า Admin

## ✨ ฟีเจอร์หลัก

### 👤 สำหรับพนักงาน
- 🔐 เข้าสู่ระบบด้วย Google OAuth
- ⏰ ลงเวลาเข้า-ออกงานด้วยปุ่มเดียว
- 📍 ตรวจสอบตำแหน่ง GPS อัตโนมัติ
- 📊 ดูประวัติการลงเวลา 14 วันล่าสุด
- 📱 รองรับการใช้งานบนมือถือ

### 👑 สำหรับ Admin
- 🛡️ จัดการสิทธิ์ผู้ใช้ (Employee/Admin)
- 📍 ตั้งค่าตำแหน่งที่อนุญาตให้ลงเวลา
- 🕐 **ตั้งค่าเวลาทำงาน** - กำหนดเวลาเข้า-ออกงานและเวลาพัก
- 👥 ดูข้อมูลพนักงานและสถิติการลงเวลา
- 📈 แดชบอร์ดสำหรับติดตามระบบ
- 🗺️ จัดการรัศมีและพิกัดตำแหน่ง

### 🔒 ความปลอดภัย
- 🛡️ Google OAuth Authentication
- 🔐 Session Management
- 🌐 HTTPS Support (Production)
- 🚫 Input Sanitization
- 📊 Security Headers

## 📁 โครงสร้างโปรเจกต์

```
📦 Employee Check-in System
├── 📂 docs/                    # 📚 เอกสารและคู่มือ
│   ├── INSTALLATION_GUIDE.md   # คู่มือการติดตั้ง
│   ├── ADMIN_SETUP.md          # การตั้งค่า Admin
│   ├── LOCATION_SYSTEM_SUMMARY.md # ระบบตรวจสอบตำแหน่ง
│   └── README.md               # ดัชนีเอกสาร
├── 📂 tests/                   # 🧪 ไฟล์ทดสอบ
│   ├── test_*.py               # Unit & Integration tests
│   ├── quick_test.py           # ทดสอบด่วน
│   └── README.md               # คู่มือการทดสอบ
├── 📂 debug/                   # 🔍 เครื่องมือ Debug
│   ├── debug_database.py       # ทดสอบฐานข้อมูล
│   ├── test_modal.html         # ทดสอบ Modal
│   └── README.md               # คู่มือ Debug
├── 📂 templates/               # 🎨 HTML Templates
│   ├── admin/                  # หน้า Admin
│   ├── index.html              # หน้าหลัก
│   └── layout.html             # Layout หลัก
├── 📂 static/                  # 🎯 Static Files
│   └── default-avatar.svg      # รูป Avatar เริ่มต้น
├── 🐍 app.py                   # แอปพลิเคชันหลัก
├── 🗄️ database.py              # การจัดการฐานข้อมูล
├── 👤 models.py                # Data Models
├── 📍 location_models.py       # Location Models
├── 🔒 security_utils.py        # Security Utilities
├── ⚙️ .env                     # Environment Variables
└── 📋 requirements.txt         # Python Dependencies
```

## 🚀 การติดตั้งด่วน

### 1. Clone Repository
```bash
git clone <repository-url>
cd attendance-system
```

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Environment
```bash
cp .env.template .env
# แก้ไขค่าใน .env ตามความเหมาะสม
```

### 4. ตั้งค่าฐานข้อมูล
```bash
python database.py
```

### 5. สร้าง Admin User
```bash
python create_admin.py
```

### 6. เริ่มระบบ
```bash
python app.py
```

เปิดเบราว์เซอร์ไปที่: `http://localhost:5000`

## 📖 เอกสารประกอบ

### 📚 คู่มือหลัก
- **[การติดตั้งระบบ](docs/INSTALLATION_GUIDE.md)** - คู่มือการติดตั้งแบบละเอียด
- **[การตั้งค่า Admin](docs/ADMIN_SETUP.md)** - วิธีสร้างและจัดการ Admin
- **[ระบบตรวจสอบตำแหน่ง](docs/LOCATION_SYSTEM_SUMMARY.md)** - การใช้งาน GPS
- **[การตั้งค่าเวลาทำงาน](docs/WORK_TIME_SETTINGS.md)** - 🆕 กำหนดเวลาเข้า-ออกงาน

### 🔧 การแก้ไขปัญหา
- **[JavaScript Issues](docs/JAVASCRIPT_DEBUG_GUIDE.md)** - แก้ไขปัญหา JavaScript
- **[Template Issues](docs/TEMPLATE_BLOCK_FIX.md)** - แก้ไขปัญหา Template
- **[Image Issues](docs/IMAGE_FIX_SUMMARY.md)** - แก้ไขปัญหารูปภาพ

### 🧪 การทดสอบ
- **[คู่มือการทดสอบ](tests/README.md)** - วิธีรัน Tests
- **[Debug Tools](debug/README.md)** - เครื่องมือ Debug

## 🌐 การใช้งาน

### สำหรับพนักงาน
1. เข้าสู่ระบบด้วย Google
2. คลิก "เข้างานตอนนี้" เมื่อมาถึงที่ทำงาน
3. คลิก "ออกงานตอนนี้" เมื่อเลิกงาน
4. ดูประวัติการลงเวลาในหน้าหลัก

### สำหรับ Admin
1. เข้าสู่ระบบด้วยบัญชี Admin
2. คลิก "จัดการระบบ" หรือไปที่ `/admin`
3. จัดการตำแหน่งใน "จัดการตำแหน่ง"
4. **ตั้งค่าเวลาทำงานใน "ตั้งค่าเวลาทำงาน"** 🆕
5. ดูข้อมูลพนักงานใน "จัดการพนักงาน"

## 🔧 การพัฒนา

### ติดตั้ง Development Environment
```bash
# Clone และติดตั้ง
git clone <repository-url>
cd attendance-system
pip install -r requirements.txt

# ตั้งค่า development
cp .env.template .env
# แก้ไข FLASK_ENV=development

# รัน tests
python -m pytest tests/ -v

# รัน debug tools
python debug/debug_database.py
```

### โครงสร้าง Code
- **Models**: `models.py`, `location_models.py`
- **Views**: `app.py` (Flask routes)
- **Templates**: `templates/` (Jinja2)
- **Database**: `database.py` (MySQL)
- **Security**: `security_utils.py`

### การเพิ่มฟีเจอร์ใหม่
1. เขียน tests ใน `tests/`
2. เพิ่ม models ใน `models.py`
3. เพิ่ม routes ใน `app.py`
4. สร้าง templates ใน `templates/`
5. อัปเดตเอกสารใน `docs/`

## 🚨 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### 1. ไม่สามารถเข้าสู่ระบบได้
```bash
# ตรวจสอบ Google OAuth settings
# ดูไฟล์ .env สำหรับ GOOGLE_CLIENT_ID และ GOOGLE_CLIENT_SECRET
```

#### 2. ปุ่มเข้างานไม่ทำงาน
```bash
# ตรวจสอบ JavaScript errors
# เปิด Developer Tools (F12) → Console
# ดู docs/JAVASCRIPT_DEBUG_GUIDE.md
```

#### 3. ฐานข้อมูลเชื่อมต่อไม่ได้
```bash
# ทดสอบการเชื่อมต่อ
python debug/debug_database.py
```

#### 4. รูปภาพไม่แสดง
```bash
# ดู docs/IMAGE_FIX_SUMMARY.md
# ทดสอบด้วย debug/debug_images.html
```

### Quick Debug Commands
```bash
# ทดสอบระบบโดยรวม
python tests/quick_test.py

# ทดสอบฐานข้อมูล
python debug/debug_database.py

# ทดสอบ JavaScript (เปิดในเบราว์เซอร์)
open debug/test_modal.html
```

## 📊 สถิติโปรเจกต์

- **ภาษา**: Python (Flask), HTML, CSS, JavaScript
- **ฐานข้อมูล**: MySQL/MariaDB
- **Authentication**: Google OAuth 2.0
- **Frontend**: Bootstrap-inspired CSS, Vanilla JavaScript
- **Testing**: pytest, Integration tests
- **Security**: Input sanitization, HTTPS support

## 🤝 การมีส่วนร่วม

### การรายงานปัญหา
1. ตรวจสอบ [เอกสารการแก้ไขปัญหา](docs/)
2. รัน debug tools ใน `debug/`
3. รวบรวมข้อมูล error logs
4. สร้าง issue พร้อมรายละเอียด

### การพัฒนา
1. Fork repository
2. สร้าง feature branch
3. เขียน tests สำหรับฟีเจอร์ใหม่
4. ทดสอบให้ผ่านทั้งหมด
5. อัปเดตเอกสาร
6. สร้าง Pull Request

## 📄 License

MIT License - ดูไฟล์ LICENSE สำหรับรายละเอียด

## 📞 การติดต่อ

- 📧 Email: [ติดต่อผู้พัฒนา]
- 📖 Documentation: `/docs` folder
- 🐛 Bug Reports: GitHub Issues
- 💡 Feature Requests: GitHub Discussions

---

**🎉 ขอบคุณที่ใช้ระบบลงเวลาเข้า-ออกงาน!**

สำหรับคำถามหรือความช่วยเหลือ กรุณาดูเอกสารใน `docs/` folder หรือใช้เครื่องมือ debug ใน `debug/` folder