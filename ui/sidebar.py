import streamlit as st

def render_sidebar():
    st.sidebar.title("🔐 账号与计费")
    
    is_logged_in = st.session_state.get('logged_in', False)
    user_info = st.session_state.get('user_info', {})
    
    if is_logged_in:
        st.sidebar.success("已登录")
        
        # 判断角色并显示不同信息
        card_type = user_info.get('type')
        
        if card_type == 'admin':
            st.sidebar.info("👨‍💻 管理员账户")
            st.sidebar.metric("权限", "无限")
        else:
            # 普通用户显示额度
            quota = user_info.get('quota_left', 0)
            
            if card_type == 'count_sheet':
                st.sidebar.caption("单表翻译剩余次数")
                st.sidebar.subheader(f"{quota} 次")
            elif card_type == 'count_file':
                st.sidebar.caption("全文件翻译剩余次数")
                st.sidebar.subheader(f"{quota} 次")
            elif card_type == 'count':
                st.sidebar.caption("单表翻译剩余次数") # 兼容旧版
                st.sidebar.subheader(f"{quota} 次")
            elif card_type == 'time':
                st.sidebar.caption("今日剩余次数 (全功能)")
                st.sidebar.subheader(f"{quota} 次")
                st.sidebar.caption(f"过期时间: {user_info.get('expire_time')}")
            
        if st.sidebar.button("退出登录"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.api_key = ""
            st.session_state.translated_file = None
            st.session_state.translation_result = None
            st.rerun()
            
    st.sidebar.divider()
    
    # 如果是管理员，隐藏普通用户的翻译配置
    if st.session_state.get('logged_in', False) and st.session_state.get('user_info', {}).get('type') == 'admin':
        st.sidebar.markdown("💡 提示：在右侧控制台生成卡密并管理用户。")
        return
    
    st.sidebar.title("⚙️ 翻译配置")
    target_lang = st.sidebar.selectbox(
        "目标语言",
        ["中文", "English", "日本語", "한국语", "Français", "Deutsch", "Español", "Русский"]
    )
    
    scene = st.sidebar.selectbox(
        "翻译场景 (专属Prompt)",
        ["通用办公", "商务贸易", "IT互联网", "金融财经", "医疗医药", "学术研究", "游戏出海"]
    )
    
    ignore_formulas = st.sidebar.checkbox("忽略公式单元格", value=True)
    ignore_numbers = st.sidebar.checkbox("忽略纯数字单元格", value=True)
    
    ignore_header_rows = st.sidebar.number_input("忽略表头行数", min_value=0, value=0, step=1)
    
    # 将配置保存到 session_state 供其他模块读取
    st.session_state.config = {
        "target_lang": target_lang,
        "scene": scene,
        "ignore_formulas": ignore_formulas,
        "ignore_numbers": ignore_numbers,
        "ignore_header_rows": ignore_header_rows
    }
    
    st.sidebar.info("💡 提示：本工具采用内存级无痕处理，文件绝不保存至服务器，保障您的隐私安全。")
