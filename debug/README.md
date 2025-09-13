# 🔍 Debug Tools

เครื่องมือสำหรับการ debug และแก้ไขปัญหาในระบบลงเวลาเข้า-ออกงาน

## 🛠️ Debug Files

### Database Debugging
- **[debug_database.py](debug_database.py)** - ทดสอบการเชื่อมต่อฐานข้อมูล
  - ตรวจสอบ environment variables
  - ทดสอบการเชื่อมต่อ MySQL
  - ตรวจสอบโครงสร้างตาราง
  - แสดงคำแนะนำการแก้ไขปัญหา

### JavaScript Debugging
- **[debug_admin_js.html](debug_admin_js.html)** - ทดสอบ JavaScript ในหน้า Admin
  - ตรวจสอบ JavaScript functions
  - ทดสอบ DOM elements
  - ตรวจสอบ Event listeners
  - แสดงวิธีแก้ไขปัญหา JavaScript

### Modal Testing
- **[test_modal.html](test_modal.html)** - ทดสอบ Modal functionality
  - ทดสอบการเปิด/ปิด Modal
  - ทดสอบ JavaScript functions
  - ทดสอบ Geolocation API
  - ทดสอบ Form submission

### Image Debugging
- **[debug_images.html](debug_images.html)** - ทดสอบการโหลดรูปภาพ
  - ทดสอบ Google profile images
  - ตรวจสอบ CORS issues
  - ทดสอบ fallback mechanisms
  - แสดงวิธีแก้ไขปัญหารูปภาพ

## 🚀 วิธีการใช้งาน

### Database Debug
```bash
# รัน database debug script
python debug/debug_database.py

# ผลลัพธ์ที่คาดหวัง:
# ✅ Database connection successful
# ✅ All required tables exist
# ✅ Table structures are correct
```

### JavaScript Debug
1. เปิดไฟล์ `debug/debug_admin_js.html` ในเบราว์เซอร์
2. คลิกปุ่ม "Test Modal Functions"
3. ตรวจสอบผลลัพธ์ใน log area
4. ทดสอบ Modal popup

### Modal Testing
1. เปิดไฟล์ `debug/test_modal.html` ในเบราว์เซอร์
2. คลิกปุ่ม "เพิ่มตำแหน่งใหม่"
3. ทดสอบ Geolocation API
4. ตรวจสอบ Form functionality

### Image Debug
1. เปิดไฟล์ `debug/debug_images.html` ในเบราว์เซอร์
2. ใส่ URL รูปภาพจาก Google
3. ทดสอบการโหลดรูปภาพ
4. ดูวิธีแก้ไขปัญหา

## 🔧 Common Debug Scenarios

### Database Connection Issues
```bash
# ทดสอบการเชื่อมต่อ
python debug/debug_database.py

# ปัญหาที่พบบ่อย:
# - MySQL server ไม่ทำงาน
# - Credentials ผิด
# - Network connectivity issues
# - Firewall blocking connection
```

### JavaScript Not Working
```html
<!-- เปิด debug_admin_js.html และตรวจสอบ -->
<!-- 1. Function definitions -->
<!-- 2. DOM element availability -->
<!-- 3. Event listener setup -->
<!-- 4. Console errors -->
```

### Modal Not Opening
```html
<!-- เปิด test_modal.html และทดสอบ -->
<!-- 1. Modal HTML structure -->
<!-- 2. CSS display properties -->
<!-- 3. JavaScript function calls -->
<!-- 4. Event handlers -->
```

### Images Not Loading
```html
<!-- เปิด debug_images.html และทดสอบ -->
<!-- 1. Image URL validity -->
<!-- 2. CORS policies -->
<!-- 3. Network connectivity -->
<!-- 4. Fallback mechanisms -->
```

## 📊 Debug Checklist

### ✅ Database Issues
- [ ] MySQL service running
- [ ] Environment variables set
- [ ] Network connectivity
- [ ] User permissions
- [ ] Database exists
- [ ] Tables created

### ✅ JavaScript Issues
- [ ] Functions defined
- [ ] DOM elements exist
- [ ] Event handlers attached
- [ ] No console errors
- [ ] Proper syntax
- [ ] Dependencies loaded

### ✅ Modal Issues
- [ ] HTML structure correct
- [ ] CSS styles applied
- [ ] JavaScript functions work
- [ ] Event handlers respond
- [ ] No blocking elements
- [ ] Z-index correct

### ✅ Image Issues
- [ ] URLs are valid
- [ ] CORS headers set
- [ ] Network accessible
- [ ] Fallback images work
- [ ] Proxy functioning
- [ ] Cache cleared

## 🚨 Troubleshooting Steps

### Step 1: Identify the Problem
1. ตรวจสอบ error messages
2. ดู browser console
3. ตรวจสอบ network tab
4. ดู server logs

### Step 2: Use Debug Tools
1. รัน appropriate debug script
2. ตรวจสอบผลลัพธ์
3. ทำตามคำแนะนำ
4. ทดสอบอีกครั้ง

### Step 3: Verify Fix
1. ทดสอบ functionality
2. ตรวจสอบ error logs
3. ทดสอบ edge cases
4. รัน integration tests

## 📝 Debug Log Analysis

### Database Logs
```
✅ Connection successful (0.05s)
✅ MySQL Version: 11.4.3-MariaDB
✅ Table 'employees' exists (7 columns)
✅ Table 'attendances' exists (6 columns)
✅ Table 'location_settings' exists (9 columns)
```

### JavaScript Logs
```
✅ openAddLocationModal function exists
✅ Modal element found
✅ Event handlers attached
✅ No console errors
```

### Modal Logs
```
✅ Modal opened successfully
✅ Form validation working
✅ Geolocation API available
✅ Event listeners responding
```

### Image Logs
```
✅ Image URL valid
✅ Network request successful
✅ CORS headers present
✅ Fallback mechanism working
```

## 🔄 Continuous Debugging

### Regular Checks
- รัน debug scripts เป็นประจำ
- ตรวจสอบ logs สำหรับ warnings
- ทดสอบ functionality หลังการเปลี่ยนแปลง
- อัปเดต debug tools ตามความจำเป็น

### Performance Monitoring
- ตรวจสอบ response times
- ดู memory usage
- ตรวจสอบ database query performance
- วิเคราะห์ network requests

### Error Tracking
- บันทึก error patterns
- ติดตาม recurring issues
- อัปเดต debug tools
- ปรับปรุงการจัดการ errors

## 📞 Getting Help

หากเครื่องมือ debug ไม่สามารถแก้ไขปัญหาได้:

1. **ตรวจสอบ Documentation**
   - ดู `/docs` folder สำหรับคู่มือ
   - อ่าน troubleshooting guides
   - ตรวจสอบ known issues

2. **รัน Integration Tests**
   - ใช้ `/tests` folder
   - รัน comprehensive tests
   - ตรวจสอบ test results

3. **Collect Debug Information**
   - รัน debug scripts ทั้งหมด
   - เก็บ error messages
   - บันทึก steps to reproduce
   - รวบรวม system information