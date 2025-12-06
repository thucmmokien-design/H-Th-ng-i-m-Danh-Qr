from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv # Import thư viện

# Load biến môi trường từ file .env
load_dotenv()

# Lấy URL từ file .env
# Nếu không tìm thấy, nó sẽ trả về None hoặc chuỗi mặc định (nếu bạn set)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Kiểm tra xem có lấy được không (để debug)
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("Chưa cấu hình DATABASE_URL trong file .env")

# Phần code cũ của bạn giữ nguyên
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()