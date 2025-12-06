
from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, Time, Date, Float, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

# Định nghĩa các trạng thái điểm danh (Enum) để tránh gõ sai
class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    LATE = "LATE"
    ABSENT = "ABSENT"

# 1. Bảng Giảng Viên
class GiangVien(Base):
    __tablename__ = "giang_vien"

    gv_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hoten = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255), nullable=False)

    # Quan hệ: Một giảng viên dạy nhiều lớp
    classes = relationship("LopHocPhan", back_populates="teacher")

# 2. Bảng Sinh Viên
class SinhVien(Base):
    __tablename__ = "sinh_vien"

    msv = Column(String(20), primary_key=True, index=True)
    hoten = Column(String(100), nullable=False)
    email = Column(String(100))
    password = Column(String(255), nullable=False)
    #device_id = Column(String(100), nullable=True) # Để null được nếu chưa đăng nhập lần đầu

    # Quan hệ ngược
    enrollments = relationship("DangKy", back_populates="student")
    attendance_logs = relationship("DiemDanh", back_populates="student")
    notifications = relationship("ThongBao", back_populates="student")

# 3. Bảng Lớp Học Phần (Môn học)
class LopHocPhan(Base):
    __tablename__ = "lop_hoc_phan"

    class_id = Column(String(20), primary_key=True, index=True) # VD: IT001
    ten_mon = Column(String(100), nullable=False)
    hoc_ky = Column(String(20))
    gv_id = Column(Integer, ForeignKey("giang_vien.gv_id"))

    # Quan hệ
    teacher = relationship("GiangVien", back_populates="classes")
    students = relationship("DangKy", back_populates="subject") # Danh sách SV trong lớp
    sessions = relationship("BuoiHoc", back_populates="subject")

# 4. Bảng Đăng Ký (Trung gian giữa SV và Lớp)
class DangKy(Base):
    __tablename__ = "dang_ky"

    class_id = Column(String(20), ForeignKey("lop_hoc_phan.class_id"), primary_key=True)
    msv = Column(String(20), ForeignKey("sinh_vien.msv"), primary_key=True)
    ngay_dang_ky = Column(DateTime, default=datetime.datetime.now)

    # Quan hệ
    student = relationship("SinhVien", back_populates="enrollments")
    subject = relationship("LopHocPhan", back_populates="students")

# 5. Bảng Buổi Học (Session) - Đã thêm GPS
class BuoiHoc(Base):
    __tablename__ = "buoi_hoc"

    session_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    class_id = Column(String(20), ForeignKey("lop_hoc_phan.class_id"))
    
    ngay_hoc = Column(Date, default=datetime.date.today)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False) # Thời gian kết thúc
    
    qr_secret = Column(String(255)) # Mã bí mật để tạo QR
    is_active = Column(Boolean, default=False) # Đang mở hay đóng điểm danh
    
    # Thông tin GPS của Giảng viên (Phòng học)
    latitude = Column(DECIMAL(10, 8))  # Vĩ độ
    longitude = Column(DECIMAL(11, 8)) # Kinh độ
    ban_kinh = Column(Integer, default=50) # Bán kính cho phép (mét)

    # Quan hệ
    subject = relationship("LopHocPhan", back_populates="sessions")
    attendance_records = relationship("DiemDanh", back_populates="session")

# 6. Bảng Điểm Danh (Log)
class DiemDanh(Base):
    __tablename__ = "diem_danh"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("buoi_hoc.session_id"))
    msv = Column(String(20), ForeignKey("sinh_vien.msv"))
    
    checkin_time = Column(DateTime, default=datetime.datetime.now)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    
    # Lưu lại vị trí thực tế của SV lúc quét (để hậu kiểm tra gian lận)
    student_lat = Column(DECIMAL(10, 8))
    student_long = Column(DECIMAL(11, 8))
    khoang_cach = Column(Float) # Khoảng cách tính được tới GV (mét)

    # Quan hệ
    session = relationship("BuoiHoc", back_populates="attendance_records")
    student = relationship("SinhVien", back_populates="attendance_logs")

# 7. Bảng Thông Báo
class ThongBao(Base):
    __tablename__ = "thong_bao"

    tb_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    msv = Column(String(20), ForeignKey("sinh_vien.msv"))
    tieu_de = Column(String(100))
    noi_dung = Column(String(500))
    thoi_gian = Column(DateTime, default=datetime.datetime.now)

    student = relationship("SinhVien", back_populates="notifications")