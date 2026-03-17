import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join("data", "users.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # type: 'count' (次卡), 'time' (时间卡)
    # quota_left: 剩余额度（次卡为总剩余次数，时间卡为当日剩余次数）
    # expire_time: 到期时间（时间卡）
    # last_reset_date: 上次重置额度的日期（用于时间卡每日刷新）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            key TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            quota_left INTEGER NOT NULL,
            expire_time DATETIME,
            last_reset_date DATE
        )
    ''')
    
    # 插入一些测试卡密
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # 管理员专属密码
        cursor.execute("INSERT INTO users (key, type, quota_left) VALUES ('admin888', 'admin', 999999)")
        # 单表次卡，剩余100次
        cursor.execute("INSERT INTO users (key, type, quota_left) VALUES ('TEST-SHEET-100', 'count_sheet', 100)")
        # 全文件次卡，剩余100次
        cursor.execute("INSERT INTO users (key, type, quota_left) VALUES ('TEST-FILE-100', 'count_file', 100)")
        # 月卡，每日1000次，一个月后过期
        expire = datetime.now() + timedelta(days=30)
        cursor.execute("INSERT INTO users (key, type, quota_left, expire_time, last_reset_date) VALUES (?, 'time', 1000, ?, ?)",
                       ('TEST-MONTH-1', expire.strftime('%Y-%m-%d %H:%M:%S'), date.today().strftime('%Y-%m-%d')))
    else:
        # 兜底：如果数据库已经有数据了，但没有 admin 账号，强行补上
        cursor.execute("SELECT COUNT(*) FROM users WHERE key = 'admin888'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (key, type, quota_left) VALUES ('admin888', 'admin', 999999)")
            
    conn.commit()
    conn.close()

def get_all_users() -> list:
    """获取所有用户信息（仅管理员可用）"""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY type, key")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_key(key: str, new_type: str, new_quota: int, new_expire: str = None) -> bool:
    """更新卡密信息"""
    if not os.path.exists(DB_PATH):
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users 
            SET type = ?, quota_left = ?, expire_time = ?
            WHERE key = ?
        """, (new_type, new_quota, new_expire, key))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        print(f"Update failed: {e}")
        success = False
    finally:
        conn.close()
    return success

def check_key(key: str) -> dict:
    """验证卡密并返回信息，如果无效返回None"""
    # 确保数据库文件存在
    if not os.path.exists(DB_PATH):
        init_db()
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 强制去除首尾空格进行比对，防止用户复制时带了空格
    cursor.execute("SELECT * FROM users WHERE TRIM(key) = ?", (key.strip(),))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {"valid": False, "msg": "卡密不存在"}
        
    user = dict(row)
    
    # 处理时间卡逻辑
    if user['type'] == 'time':
        if not user['expire_time']:
            conn.close()
            return {"valid": False, "msg": "卡密信息异常"}
            
        expire_time = datetime.strptime(user['expire_time'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expire_time:
            conn.close()
            return {"valid": False, "msg": "卡密已过期"}
            
        # 每日重置额度
        today_str = date.today().strftime('%Y-%m-%d')
        if user['last_reset_date'] != today_str:
            user['quota_left'] = 1000 # 假设时间卡每日额度为1000
            user['last_reset_date'] = today_str
            cursor.execute("UPDATE users SET quota_left = ?, last_reset_date = ? WHERE key = ?", 
                           (1000, today_str, key))
            conn.commit()
            
    conn.close()
    
    # 管理员卡不限制额度
    if user['type'] != 'admin' and user['quota_left'] <= 0:
        return {"valid": False, "msg": "额度已用尽"}
        
    return {"valid": True, "user": user}

def consume_quota(key: str, amount: int = 1) -> bool:
    """扣减额度"""
    if not os.path.exists(DB_PATH):
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT quota_left, type, expire_time FROM users WHERE TRIM(key) = ?", (key.strip(),))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
        
    quota_left, card_type, expire_time = row
    
    # 管理员不扣费
    if card_type == 'admin':
        conn.close()
        return True
    
    # 检查时间卡是否过期
    if card_type == 'time':
        if not expire_time or datetime.now() > datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S'):
            conn.close()
            return False
            
    if quota_left < amount:
        conn.close()
        return False
        
    cursor.execute("UPDATE users SET quota_left = quota_left - ? WHERE TRIM(key) = ?", (amount, key.strip()))
    conn.commit()
    conn.close()
    return True
