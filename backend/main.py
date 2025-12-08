from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, database
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt # Yêu cầu: pip install pyjwt

# 1. TẠO BẢNG TỰ ĐỘNG
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# 2. CẤU HÌNH BẢO MẬT (JWT)
# Bạn có thể đổi chuỗi này thành bất cứ gì
SECRET_KEY = "doan_tot_nghiep_bi_mat_khong_duoc_tiet_lo"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Đường dẫn để lấy token (Login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Cấu hình mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- HÀM HỖ TRỢ ---
def create_access_token(data: dict):
    """Hàm tạo JWT Token khi đăng nhập thành công"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ==========================================
# PHẦN 1: API ĐĂNG NHẬP (QUAN TRỌNG NHẤT)
# ==========================================
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    API này dùng cho cả App Desktop (GV) và Web (SV).
    Nó sẽ kiểm tra tài khoản ở cả 2 bảng.
    """
    # 1. Tìm trong bảng GIẢNG VIÊN trước
    gv = db.query(models.GiangVien).filter(models.GiangVien.email == form_data.username).first()
    if gv and verify_password(form_data.password, gv.password):
        # Nếu đúng là GV, cấp token quyền 'teacher'
        access_token = create_access_token(data={"sub": gv.email, "role": "teacher", "id": gv.gv_id})
        return {"access_token": access_token, "token_type": "bearer"}
    
    # 2. Nếu không phải GV, tìm trong bảng SINH VIÊN
    sv = db.query(models.SinhVien).filter(models.SinhVien.msv == form_data.username).first()
    if sv and verify_password(form_data.password, sv.password):
        # Nếu đúng là SV, cấp token quyền 'student'
        access_token = create_access_token(data={"sub": sv.msv, "role": "student"})
        return {"access_token": access_token, "token_type": "bearer"}
        
    # 3. Không tìm thấy ai
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sai tài khoản hoặc mật khẩu",
        headers={"WWW-Authenticate": "Bearer"},
    )

# ==========================================
# PHẦN 2: API QUẢN LÝ SINH VIÊN
# ==========================================
@app.post("/sinhvien/", response_model=schemas.SinhVienResponse)
def create_sinh_vien(sv: schemas.SinhVienCreate, db: Session = Depends(database.get_db)):
    # Kiểm tra trùng MSV
    db_sv = db.query(models.SinhVien).filter(models.SinhVien.msv == sv.msv).first()
    if db_sv:
        raise HTTPException(status_code=400, detail="Mã sinh viên đã tồn tại")
    
    hashed_password = get_password_hash(sv.password)
    new_sv = models.SinhVien(
        msv=sv.msv, 
        hoten=sv.hoten, 
        password=hashed_password,
        email=sv.email
        # device_id=sv.device_id (Bỏ comment nếu dùng)
    )
    
    try:
        db.add(new_sv)
        db.commit()      
        db.refresh(new_sv) 
        return new_sv
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sinhvien/")
def read_sinh_vien(db: Session = Depends(database.get_db)):
    return db.query(models.SinhVien).all()

# ==========================================
# PHẦN 3: API QUẢN LÝ GIẢNG VIÊN (MỚI)
# ==========================================
@app.post("/giangvien/", response_model=schemas.GiangVienResponse)
def create_giang_vien(gv: schemas.GiangVienCreate, db: Session = Depends(database.get_db)):
    # Kiểm tra trùng Email
    db_gv = db.query(models.GiangVien).filter(models.GiangVien.email == gv.email).first()
    if db_gv:
        raise HTTPException(status_code=400, detail="Email giảng viên đã tồn tại")

    hashed_password = get_password_hash(gv.password)
    new_gv = models.GiangVien(
        hoten=gv.hoten,
        email=gv.email,
        password=hashed_password
    )
    
    db.add(new_gv)
    db.commit()
    db.refresh(new_gv)
    return new_gv

@app.get("/giangvien/")
def read_giang_vien(db: Session = Depends(database.get_db)):
    return db.query(models.GiangVien).all()

# ==========================================
# PHẦN 4: API LỚP HỌC & BUỔI HỌC (Cho Desktop App)
# ==========================================

# Tạo lớp học phần
@app.post("/lophocphan/", response_model=schemas.LopHocPhanResponse)
def create_lop(lop: schemas.LopHocPhanCreate, db: Session = Depends(database.get_db)):
    db_lop = models.LopHocPhan(**lop.dict())
    try:
        db.add(db_lop)
        db.commit()
        db.refresh(db_lop)
        return db_lop
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Mã lớp đã tồn tại hoặc lỗi")

# Tạo buổi học (Session) - App GV sẽ gọi cái này để lấy session_id
@app.post("/buoihoc/", response_model=schemas.BuoiHocResponse)
def create_session(ss: schemas.BuoiHocCreate, db: Session = Depends(database.get_db)):
    # Tự động sinh mã bí mật cho QR
    import secrets
    secret_code = secrets.token_urlsafe(16) # VD: aJ7s8_kL9...
    
    new_session = models.BuoiHoc(
        class_id=ss.class_id,
        ngay_hoc=ss.ngay_hoc,
        start_time=ss.start_time,
        end_time=ss.end_time,
        latitude=ss.latitude,
        longitude=ss.longitude,
        ban_kinh=ss.ban_kinh,
        qr_secret=secret_code, 
        is_active=True # Mặc định tạo xong là mở điểm danh luôn
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


# ==========================================
# PHẦN 5: XỬ LÝ ĐIỂM DANH & GPS (PHẦN CUỐI CÙNG)
# ==========================================
import math
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Cấu hình thư mục chứa file giao diện web (HTML)
# Bạn nhớ tạo thư mục tên là "templates" cùng cấp với main.py nhé
templates = Jinja2Templates(directory="templates")

# 1. Hàm toán học tính khoảng cách giữa 2 tọa độ (Công thức Haversine)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 # Bán kính trái đất (mét)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance # Trả về số mét

# 2. API GET: Trả về giao diện Web khi Sinh viên quét QR
@app.get("/checkin", response_class=HTMLResponse)
def get_checkin_page(request: Request, s: int, c: str):
    """
    Khi quét QR, link sẽ là: http://domain/checkin?s=1&c=xyz
    s: session_id
    c: qr_secret
    """
    return templates.TemplateResponse("checkin.html", {
        "request": request,
        "session_id": s,
        "qr_secret": c
    })

# 3. API POST: Nhận tọa độ GPS từ điện thoại và Xử lý
@app.post("/api/process-checkin")
def process_checkin(
    data: schemas.CheckInRequest, 
    session_id: int, 
    qr_secret: str,
    current_user_token: str = Depends(oauth2_scheme), # Bắt buộc phải có Token
    db: Session = Depends(database.get_db)
):
    # A. Giải mã Token để lấy mã sinh viên (MSV)
    try:
        # Lưu ý: Cần import jwt và các biến cấu hình SECRET_KEY từ bên trên
        payload = jwt.decode(current_user_token, SECRET_KEY, algorithms=[ALGORITHM])
        msv = payload.get("sub")
        role = payload.get("role")
        if role != "student":
            raise HTTPException(status_code=400, detail="Giảng viên không được tự điểm danh!")
    except Exception:
        raise HTTPException(status_code=401, detail="Token lỗi hoặc hết hạn. Vui lòng đăng nhập lại.")

    # B. Kiểm tra Buổi học (Session)
    session = db.query(models.BuoiHoc).filter(models.BuoiHoc.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Buổi học không tồn tại")
    
    # C. Kiểm tra Mã bí mật (Chống sinh viên tự mò số session_id để điểm danh bừa)
    if session.qr_secret != qr_secret:
        raise HTTPException(status_code=400, detail="Mã QR không hợp lệ (Có thể là mã giả)")

    if not session.is_active:
        raise HTTPException(status_code=400, detail="Điểm danh đã đóng")

    # D. Kiểm tra xem đã điểm danh trước đó chưa?
    existing_log = db.query(models.DiemDanh).filter(
        models.DiemDanh.session_id == session_id,
        models.DiemDanh.msv == msv
    ).first()
    if existing_log:
        return {"status": "info", "message": "Bạn đã điểm danh rồi, không cần quét lại!"}

    # E. TÍNH KHOẢNG CÁCH GPS (QUAN TRỌNG)
    # Tọa độ GV (Lấy từ DB)
    gv_lat = float(session.latitude)
    gv_lon = float(session.longitude)
    
    # Tọa độ SV (Gửi lên từ điện thoại)
    sv_lat = data.latitude
    sv_lon = data.longitude
    
    dist = calculate_distance(gv_lat, gv_lon, sv_lat, sv_lon)
    
    # F. So sánh với bán kính cho phép
    attendance_status = "PRESENT" # Mặc định là Có mặt
    
    # Nếu xa quá bán kính cho phép -> Báo lỗi
    if dist > session.ban_kinh:
         raise HTTPException(
             status_code=400, 
             detail=f"Bạn đang ở quá xa lớp học! Khoảng cách: {int(dist)}m (Cho phép: {session.ban_kinh}m)"
         )
    
    # G. Lưu vào Database
    new_log = models.DiemDanh(
        session_id=session_id,
        msv=msv,
        status=attendance_status,
        lat_sv=sv_lat,
        long_sv=sv_lon,
        khoang_cach=dist
    )
    db.add(new_log)
    db.commit()
    
    return {"status": "success", "message": "Điểm danh thành công!", "distance": dist}