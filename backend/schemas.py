from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional, List
from decimal import Decimal

class Token(BaseModel):
    access_token:str
    token_type:str

class TokenData(BaseModel):
    username:str|None=None

#schemas cho sinh vien
class SinhVienBase(BaseModel):
    msv: str
    hoten: str
    email: str | None = None
    lop_hanh_chinh: str | None = None
    #device_id: str | None = None

class SinhVienCreate(SinhVienBase):
    password:str

class SinhVienResponse(SinhVienBase):
    class Config:
        orm_mode=True

# Schemas cho giang vien
class GiangVienBase(BaseModel):
    hoten:str
    email:str

class GiangVienCreate(GiangVienBase):
    password:str

class GiangVienResponse(GiangVienBase):
    gv_id:int

    class Config:
        orm_mode=True

# schemas cho lớp học phần
class LopHocPhanBase(BaseModel):
    class_id: str
    ten_mon: str
    hoc_ky: str | None = None
    gv_id: int 

class LopHocPhanCreate(LopHocPhanBase):
    pass

class LopHocPhanResponse(LopHocPhanBase):
    class Config:
        orm_mode = True

# schemas cho buổi học

class BuoiHocBase(BaseModel):
    class_id: str
    ngay_hoc: date
    start_time: time
    end_time: time
    latitude: float 
    longitude: float
    ban_kinh: int = 50

class BuoiHocCreate(BuoiHocBase):
    pass 

class BuoiHocResponse(BuoiHocBase):
    session_id: int
    qr_secret: str | None = None
    is_active: bool
    
    class Config:
        orm_mode = True

# schemas cho diem danh
class CheckInRequest(BaseModel):
    latitude: float
    longitude: float

# Dữ liệu Server trả về sau khi điểm danh xong
class DiemDanhResponse(BaseModel):
    id: int
    session_id: int
    msv: str
    checkin_time: datetime
    status: str
    khoang_cach: float | None = None

    class Config:
        orm_mode = True

# schemas đăng kí học
class DangKyBase(BaseModel):
    class_id: str
    msv: str
class DangKyResponse(DangKyBase):
    ngay_dang_ky: datetime
    class Config:
        orm_mode = True