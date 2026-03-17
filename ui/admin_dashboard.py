import streamlit as st
import pandas as pd
from auth.db import get_all_users, update_key
import sqlite3
import os

DB_PATH = os.path.join("data", "users.db")

def delete_key(key):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE key = ?", (key,))
    conn.commit()
    conn.close()

def render_admin_dashboard():
    st.title("🛠️ 管理员控制台")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔑 快捷生成卡密")
        with st.form("generate_key_form"):
            card_type = st.selectbox(
                "卡密类型",
                options=['count_sheet', 'count_file', 'time'],
                format_func=lambda x: {
                    'count_sheet': '单Sheet计次卡',
                    'count_file': '全文件计次卡',
                    'time': '时间卡 (包月/包年)'
                }[x]
            )
            
            num_cards = st.number_input("生成数量", min_value=1, max_value=100, value=1)
            
            if card_type in ['count_sheet', 'count_file']:
                quota = st.number_input("包含翻译次数", min_value=1, max_value=10000, value=100)
            else:
                days = st.number_input("有效天数", min_value=1, max_value=365, value=30)
                quota = st.number_input("每日额度", min_value=1, max_value=10000, value=1000)
                
            submitted = st.form_submit_button("立即生成")
            if submitted:
                # 动态导入生成函数
                import sys
                import importlib.util
                # 假设 generate_keys.py 在根目录
                spec = importlib.util.spec_from_file_location("generate_keys", "generate_keys.py")
                if spec and spec.loader:
                    gen_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(gen_module)
                    
                    if card_type in ['count_sheet', 'count_file']:
                        keys = gen_module.create_count_cards(num_cards, quota, card_type)
                    else:
                        keys = gen_module.create_time_cards(num_cards, days, quota)
                        
                    st.success(f"✅ 成功生成 {num_cards} 张卡密！")
                    st.code("\n".join(keys))
                    # 重新加载页面数据
                    st.rerun()

    with col2:
        st.subheader("📊 统计概览")
        users = get_all_users()
        total_keys = len(users)
        admin_keys = sum(1 for u in users if u['type'] == 'admin')
        active_keys = total_keys - admin_keys
        
        st.metric("总发卡数量", active_keys)
        st.metric("单表次卡", sum(1 for u in users if u['type'] == 'count_sheet'))
        st.metric("全文件次卡", sum(1 for u in users if u['type'] == 'count_file'))
        st.metric("时间卡", sum(1 for u in users if u['type'] == 'time'))
        
    st.markdown("---")
    st.subheader("📋 所有卡密列表与使用情况")
    
    if not users:
        st.info("暂无数据")
        return
        
    df = pd.DataFrame(users)
    # 重命名列以提高可读性
    df['type'] = df['type'].map({
        'count_sheet': '单Sheet次卡',
        'count_file': '全文件次卡',
        'time': '时间卡',
        'admin': '管理员'
    })
    df.rename(columns={
        'key': '卡密',
        'type': '类型',
        'quota_left': '剩余额度',
        'expire_time': '过期时间',
        'last_reset_date': '上次重置(时间卡)'
    }, inplace=True)
    
    # 将 DataFrame 转换为字典列表以便于在前端渲染操作按钮
    records = df.to_dict('records')
    
    # 自定义表格显示
    for idx, row in enumerate(records):
        with st.container():
            col_key, col_type, col_quota, col_expire, col_reset, col_action = st.columns([2.5, 1.5, 1, 1.5, 1.5, 2])
            
            # 显示表头
            if idx == 0:
                col_key.markdown("**卡密**")
                col_type.markdown("**类型**")
                col_quota.markdown("**剩余额度**")
                col_expire.markdown("**过期时间**")
                col_reset.markdown("**上次重置**")
                col_action.markdown("**操作**")
                st.markdown("---")
            
            # 显示数据行
            col_key.write(row['卡密'])
            col_type.write(row['类型'])
            col_quota.write(row['剩余额度'])
            col_expire.write(row['过期时间'] if pd.notna(row['过期时间']) else "-")
            col_reset.write(row['上次重置(时间卡)'] if pd.notna(row['上次重置(时间卡)']) else "-")
            
            # 操作按钮区域
            with col_action:
                btn_col1, btn_col2 = st.columns(2)
                
                # 编辑按钮逻辑
                with btn_col1:
                    if st.button("✏️ 编辑", key=f"edit_{row['卡密']}"):
                        st.session_state.editing_key = row['卡密']
                
                # 删除按钮逻辑
                with btn_col2:
                    # 防止删除超级管理员
                    if row['卡密'] == 'admin888':
                        st.button("🗑️ 删除", key=f"del_{row['卡密']}", disabled=True, help="不能删除内置管理员")
                    else:
                        if st.button("🗑️ 删除", key=f"del_{row['卡密']}"):
                            delete_key(row['卡密'])
                            st.success(f"已删除卡密: {row['卡密']}")
                            st.rerun()
            
            # 编辑表单区域
            if st.session_state.get('editing_key') == row['卡密']:
                with st.container(border=True):
                    st.markdown(f"**编辑卡密: `{row['卡密']}`**")
                    
                    # 映射中文类型回内部代码
                    type_mapping = {
                        '单Sheet次卡': 'count_sheet',
                        '全文件次卡': 'count_file',
                        '时间卡': 'time',
                        '管理员': 'admin'
                    }
                    current_type_code = type_mapping.get(row['类型'], 'count_sheet')
                    
                    edit_form_col1, edit_form_col2, edit_form_col3 = st.columns(3)
                    
                    with edit_form_col1:
                        new_type_label = st.selectbox(
                            "修改类型",
                            options=['单Sheet次卡', '全文件次卡', '时间卡', '管理员'],
                            index=['单Sheet次卡', '全文件次卡', '时间卡', '管理员'].index(row['类型']),
                            key=f"edit_type_{row['卡密']}"
                        )
                        new_type_code = type_mapping[new_type_label]
                        
                    with edit_form_col2:
                        new_quota = st.number_input(
                            "修改剩余额度/每日额度",
                            min_value=0,
                            value=int(row['剩余额度']),
                            key=f"edit_quota_{row['卡密']}"
                        )
                        
                    with edit_form_col3:
                        # 只有时间卡才需要编辑过期时间
                        new_expire = None
                        if new_type_code == 'time':
                            current_expire = str(row['过期时间']) if pd.notna(row['过期时间']) and row['过期时间'] != '-' else "2026-12-31 23:59:59"
                            new_expire = st.text_input(
                                "修改过期时间 (YYYY-MM-DD HH:MM:SS)",
                                value=current_expire,
                                key=f"edit_expire_{row['卡密']}"
                            )
                    
                    action_col1, action_col2 = st.columns([1, 4])
                    with action_col1:
                        if st.button("💾 保存修改", type="primary", key=f"save_{row['卡密']}"):
                            if update_key(row['卡密'], new_type_code, new_quota, new_expire):
                                st.success("修改成功！")
                                st.session_state.editing_key = None
                                st.rerun()
                            else:
                                st.error("修改失败，请检查数据库。")
                    with action_col2:
                        if st.button("❌ 取消", key=f"cancel_edit_{row['卡密']}"):
                            st.session_state.editing_key = None
                            st.rerun()
            
            st.divider()

    # 移除底部的旧删除输入框
    # st.markdown("---")
    # st.subheader("🗑️ 删除卡密")
    # delete_key_input = st.text_input("输入要删除的卡密 (慎用)")
    # if st.button("确认删除", type="primary"):
    #     if delete_key_input:
    #         delete_key(delete_key_input)
    #         st.success(f"已删除卡密: {delete_key_input}")
    #         st.rerun()
