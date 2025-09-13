# 📚 Documentation

เอกสารประกอบและคู่มือสำหรับระบบลงเวลาเข้า-ออกงาน

## 📋 เอกสารหลัก

### การติดตั้งและตั้งค่า
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - คู่มือการติดตั้งระบบ
- **[ADMIN_SETUP.md](ADMIN_SETUP.md)** - การตั้งค่าผู้ดูแลระบบ
- **[ADMIN_MENU_GUIDE.md](ADMIN_MENU_GUIDE.md)** - คู่มือการใช้งานเมนู Admin

### ระบบตรวจสอบตำแหน่ง
- **[LOCATION_SYSTEM_SUMMARY.md](LOCATION_SYSTEM_SUMMARY.md)** - ภาพรวมระบบตรวจสอบตำแหน่ง
- **[LOCATION_SETUP_COMPLETE.md](LOCATION_SETUP_COMPLETE.md)** - การติดตั้งระบบตำแหน่งเสร็จสิ้น

### การตั้งค่าเวลาทำงาน
- **[WORK_TIME_SETTINGS.md](WORK_TIME_SETTINGS.md)** - 🆕 การตั้งค่าเวลาเข้า-ออกงานและเวลาพัก

### ความปลอดภัย
- **[SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)** - การใช้งานระบบความปลอดภัย
- **[CSRF_TROUBLESHOOTING.md](CSRF_TROUBLESHOOTING.md)** - แก้ไขปัญหา CSRF
- **[CSRF_REMOVAL_SUMMARY.md](CSRF_REMOVAL_SUMMARY.md)** - สรุปการลบ CSRF Protection

### การแก้ไขปัญหา
- **[JAVASCRIPT_DEBUG_GUIDE.md](JAVASCRIPT_DEBUG_GUIDE.md)** - คู่มือแก้ไขปัญหา JavaScript
- **[JAVASCRIPT_FIX_SUMMARY.md](JAVASCRIPT_FIX_SUMMARY.md)** - สรุปการแก้ไข JavaScript
- **[TEMPLATE_BLOCK_FIX.md](TEMPLATE_BLOCK_FIX.md)** - แก้ไขปัญหา Template Block
- **[TEMPLATE_CONTENT_BLOCK_FIX.md](TEMPLATE_CONTENT_BLOCK_FIX.md)** - แก้ไขปัญหา Content Block
- **[IMAGE_FIX_SUMMARY.md](IMAGE_FIX_SUMMARY.md)** - แก้ไขปัญหารูปภาพ

### UI และ UX
- **[UI_MODERNIZATION_SUMMARY.md](UI_MODERNIZATION_SUMMARY.md)** - การปรับปรุง UI สมัยใหม่
- **[UI_THAI_LOCALIZATION_SUMMARY.md](UI_THAI_LOCALIZATION_SUMMARY.md)** - การแปลเป็นภาษาไทย

### สรุปผลงาน
- **[SUCCESS_SUMMARY.md](SUCCESS_SUMMARY.md)** - สรุปความสำเร็จของโปรเจกต์
- **[INTEGRATION_TEST_SUMMARY.md](INTEGRATION_TEST_SUMMARY.md)** - สรุปการทดสอบระบบ

## 🎯 การใช้งานเอกสาร

### สำหรับผู้ติดตั้งใหม่
1. เริ่มจาก [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. ตั้งค่า Admin ด้วย [ADMIN_SETUP.md](ADMIN_SETUP.md)
3. ศึกษาระบบตำแหน่งจาก [LOCATION_SYSTEM_SUMMARY.md](LOCATION_SYSTEM_SUMMARY.md)

### สำหรับผู้ดูแลระบบ
1. ดู [ADMIN_MENU_GUIDE.md](ADMIN_MENU_GUIDE.md) สำหรับการใช้งาน
2. ตั้งค่าตำแหน่งตาม [LOCATION_SETUP_COMPLETE.md](LOCATION_SETUP_COMPLETE.md)
3. ตั้งค่าเวลาทำงานด้วย [WORK_TIME_SETTINGS.md](WORK_TIME_SETTINGS.md) 🆕

### สำหรับนักพัฒนา
1. ศึกษา [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)
2. ดูการแก้ไขปัญหาใน JavaScript และ Template files
3. ใช้ Integration Tests เป็นแนวทาง

### สำหรับการแก้ไขปัญหา
1. JavaScript Issues → [JAVASCRIPT_DEBUG_GUIDE.md](JAVASCRIPT_DEBUG_GUIDE.md)
2. CSRF Issues → [CSRF_TROUBLESHOOTING.md](CSRF_TROUBLESHOOTING.md)
3. Template Issues → [TEMPLATE_BLOCK_FIX.md](TEMPLATE_BLOCK_FIX.md)
4. Image Issues → [IMAGE_FIX_SUMMARY.md](IMAGE_FIX_SUMMARY.md)

## 📞 การขอความช่วยเหลือ

หากพบปัญหาที่ไม่มีในเอกสาร:
1. ตรวจสอบ logs ของระบบ
2. ดู error messages ใน browser console
3. ทดสอบด้วย debug tools ใน `/debug` folder
4. รัน integration tests ใน `/tests` folder