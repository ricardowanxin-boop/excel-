import sqlite3
import os
import random
import string
from datetime import datetime, date, timedelta

DB_PATH = os.path.join("data", "users.db")

def generate_random_key(length=12):
    """生成随机卡密：大写字母+数字"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_count_cards(num_cards, quota, card_type='count_sheet'):
    """
    生成计次卡密
    :param num_cards: 生成的卡密数量
    :param quota: 每张卡的翻译次数
    :param card_type: 'count_sheet' (按单表) 或 'count_file' (按文件)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    prefix = "SHT-" if card_type == 'count_sheet' else "FILE-"
    
    generated_keys = []
    for _ in range(num_cards):
        key = f"{prefix}{generate_random_key()}"
        cursor.execute("INSERT INTO users (key, type, quota_left) VALUES (?, ?, ?)", (key, card_type, quota))
        generated_keys.append(key)
        
    conn.commit()
    conn.close()
    
    type_name = "【单Sheet计次卡】" if card_type == 'count_sheet' else "【全文件计次卡】"
    print(f"\n✅ 成功生成 {num_cards} 张{type_name} (每张包含 {quota} 次翻译额度):")
    for k in generated_keys:
        print(f"  {k}")
    return generated_keys

def create_time_cards(num_cards, days_valid, daily_quota=1000):
    """
    生成时间卡密（例如月卡、季卡）
    :param num_cards: 生成的卡密数量
    :param days_valid: 有效天数 (如 30 代表月卡)
    :param daily_quota: 每日限制翻译次数
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    expire_date = datetime.now() + timedelta(days=days_valid)
    expire_str = expire_date.strftime('%Y-%m-%d %H:%M:%S')
    today_str = date.today().strftime('%Y-%m-%d')
    
    generated_keys = []
    for _ in range(num_cards):
        key = f"TIME-{generate_random_key()}"
        cursor.execute("""
            INSERT INTO users (key, type, quota_left, expire_time, last_reset_date) 
            VALUES (?, 'time', ?, ?, ?)
        """, (key, daily_quota, expire_str, today_str))
        generated_keys.append(key)
        
    conn.commit()
    conn.close()
    
    print(f"\n✅ 成功生成 {num_cards} 张【时间卡】 (有效期 {days_valid} 天, 每日额度 {daily_quota} 次):")
    print(f"  (过期时间: {expire_str})")
    for k in generated_keys:
        print(f"  {k}")
    return generated_keys

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("错误：数据库文件不存在，请先运行一次 app.py 初始化系统。")
        exit(1)
        
    print("="*40)
    print("🛠️ 卡密生成管理脚本")
    print("="*40)
    print("1. 生成【单Sheet计次卡】 (按单表扣费，不过期)")
    print("2. 生成【全文件计次卡】 (按文件扣费，不过期)")
    print("3. 生成【时间卡】 (包月/包年，全功能，每日刷新)")
    
    choice = input("\n请选择生成的卡密类型 (1, 2 或 3): ").strip()
    
    if choice == '1':
        num = int(input("请输入要生成的卡密数量: "))
        quota = int(input("请输入每张卡包含的翻译次数 (例如 100): "))
        create_count_cards(num, quota, 'count_sheet')
        
    elif choice == '2':
        num = int(input("请输入要生成的卡密数量: "))
        quota = int(input("请输入每张卡包含的翻译次数 (例如 100): "))
        create_count_cards(num, quota, 'count_file')
        
    elif choice == '3':
        num = int(input("请输入要生成的卡密数量: "))
        days = int(input("请输入有效天数 (例如 30 代表包月): "))
        quota = int(input("请输入每日翻译次数限制 (例如 1000): "))
        create_time_cards(num, days, quota)
        
    else:
        print("无效的选择，脚本退出。")
