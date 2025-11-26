import nextcord
import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env เข้าสู่ environment variables
load_dotenv()

OWNERS = [1333335390181920771]

# ดึงค่า BOT_TOKEN จาก environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("ไม่พบ BOT_TOKEN ในไฟล์ .env! กรุณาตั้งค่าตัวแปร BOT_TOKEN")

TRUEMONEY_PHONE = "0630102037"
LOG_CHANNEL_ID = 1307037622509502505

loading = nextcord.Embed(description="🔃 กำลังตรวจสอบ...")