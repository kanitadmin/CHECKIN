# 🧪 Tests

ไฟล์ทดสอบสำหรับระบบลงเวลาเข้า-ออกงาน

## 📋 ประเภทของ Tests

### Unit Tests
- **[test_models.py](test_models.py)** - ทดสอบ Models และ Data structures
- **[test_database.py](test_database.py)** - ทดสอบการเชื่อมต่อฐานข้อมูล
- **[test_security.py](test_security.py)** - ทดสอบระบบความปลอดภัย
- **[test_error_handling_unit.py](test_error_handling_unit.py)** - ทดสอบการจัดการ errors

### Integration Tests
- **[test_models_integration.py](test_models_integration.py)** - ทดสอบ Models กับฐานข้อมูล
- **[test_flask_login_integration.py](test_flask_login_integration.py)** - ทดสอบระบบ Login
- **[test_oauth_authentication.py](test_oauth_authentication.py)** - ทดสอบ Google OAuth
- **[test_security_integration.py](test_security_integration.py)** - ทดสอบความปลอดภัยแบบรวม
- **[test_dashboard_integration.py](test_dashboard_integration.py)** - ทดสอบ Dashboard
- **[test_attendance_integration.py](test_attendance_integration.py)** - ทดสอบระบบลงเวลา

### Feature Tests
- **[test_checkin_logic.py](test_checkin_logic.py)** - ทดสอบ Logic การเข้างาน
- **[test_checkout_logic.py](test_checkout_logic.py)** - ทดสอบ Logic การออกงาน
- **[test_checkin_integration.py](test_checkin_integration.py)** - ทดสอบการเข้างานแบบรวม
- **[test_checkout_integration.py](test_checkout_integration.py)** - ทดสอบการออกงานแบบรวม
- **[test_checkin_edge_cases.py](test_checkin_edge_cases.py)** - ทดสอบกรณีพิเศษ
- **[test_checkout_endpoint.py](test_checkout_endpoint.py)** - ทดสอบ API Endpoint

### End-to-End Tests
- **[test_integration_end_to_end.py](test_integration_end_to_end.py)** - ทดสอบระบบทั้งหมด
- **[test_attendance_repository.py](test_attendance_repository.py)** - ทดสอบ Repository pattern
- **[test_session_expiry.py](test_session_expiry.py)** - ทดสอบการหมดอายุ session

### Error Handling Tests
- **[test_error_handling.py](test_error_handling.py)** - ทดสอบการจัดการข้อผิดพลาด

### Quick Tests
- **[quick_test.py](quick_test.py)** - ทดสอบด่วนสำหรับการตรวจสอบระบบ
- **[test_no_csrf.py](test_no_csrf.py)** - ทดสอบระบบหลังลบ CSRF
- **[test_csrf_simple.py](test_csrf_simple.py)** - ทดสอบ CSRF แบบง่าย
- **[test_csrf_fix.py](test_csrf_fix.py)** - ทดสอบการแก้ไข CSRF
- **[test_javascript_fix.py](test_javascript_fix.py)** - ทดสอบการแก้ไข JavaScript
- **[test_admin_menu.py](test_admin_menu.py)** - ทดสอบเมนู Admin

## 🚀 วิธีการรัน Tests

### รัน Test ทั้งหมด
```bash
python -m pytest tests/ -v
```

### รัน Test เฉพาะไฟล์
```bash
python -m pytest tests/test_models.py -v
```

### รัน Test เฉพาะ function
```bash
python -m pytest tests/test_models.py::TestEmployee::test_employee_creation -v
```

### รัน Integration Tests
```bash
python run_integration_tests.py
```

### รัน Quick Test
```bash
python tests/quick_test.py
```

## 📊 Test Categories

### 🔧 Core Functionality
- Models และ Database operations
- Authentication และ Authorization
- Check-in/Check-out logic
- Session management

### 🛡️ Security
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection (ถูกลบแล้ว)

### 🌐 Integration
- API endpoints
- Database transactions
- OAuth flow
- Error handling

### 🎯 Edge Cases
- Network failures
- Database connection issues
- Invalid inputs
- Concurrent operations

## 📋 Test Requirements

### Environment Setup
```bash
# ติดตั้ง pytest
pip install pytest

# ตั้งค่า environment variables
cp .env.template .env
# แก้ไขค่าในไฟล์ .env
```

### Database Setup
```bash
# สร้างฐานข้อมูลทดสอบ
python database.py
```

### Running Prerequisites
- MySQL server ต้องทำงาน
- Environment variables ต้องตั้งค่าถูกต้อง
- Dependencies ต้องติดตั้งครบ

## 🔍 Test Coverage

### ✅ Covered Areas
- User authentication (Google OAuth)
- Check-in/Check-out functionality
- Database operations
- Error handling
- Security validations
- Admin functions

### ⚠️ Areas for Improvement
- Location-based check-in tests
- Performance tests
- Load testing
- Browser automation tests

## 📝 Writing New Tests

### Test Naming Convention
```python
# Unit tests
def test_function_name_expected_behavior():
    pass

# Integration tests  
def test_integration_feature_scenario():
    pass

# Edge cases
def test_edge_case_description():
    pass
```

### Test Structure
```python
def test_example():
    # Arrange
    setup_test_data()
    
    # Act
    result = perform_action()
    
    # Assert
    assert result == expected_value
    
    # Cleanup (if needed)
    cleanup_test_data()
```

## 🚨 Common Issues

### Database Connection
- ตรวจสอบ MySQL service
- ตรวจสอบ credentials ใน .env
- ตรวจสอบ network connectivity

### Environment Variables
- ตรวจสอบไฟล์ .env
- ตรวจสอบ required variables
- ตรวจสอบ syntax ในไฟล์

### Dependencies
- รัน `pip install -r requirements.txt`
- ตรวจสอบ Python version compatibility
- ตรวจสอบ virtual environment

## 📞 Troubleshooting

หากพบปัญหาในการรัน tests:

1. **ตรวจสอบ Environment**
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('DB_HOST:', os.getenv('DB_HOST'))"
   ```

2. **ทดสอบ Database Connection**
   ```bash
   python debug/debug_database.py
   ```

3. **รัน Quick Test**
   ```bash
   python tests/quick_test.py
   ```

4. **ตรวจสอบ Logs**
   - ดู console output
   - ตรวจสอบ Flask logs
   - ดู MySQL error logs