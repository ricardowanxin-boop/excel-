import streamlit as st
import base64
import os
from auth.db import check_key

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_login_page():
    # 读取背景图片
    try:
        # 获取当前脚本所在的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建相对路径
        img_path = os.path.join(current_dir, "img", "background.png")
        
        bin_str = get_base64_of_bin_file(img_path)
        bg_css = f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """
    except Exception as e:
        bg_css = ""
        st.error(f"加载背景图片失败: {e}")

    # CSS 样式：全屏居中卡片布局
    st.markdown(f"""
        {bg_css}
        <style>
        /* 隐藏顶部工具栏以更沉浸 */
        header {{visibility: hidden;}}
        
        /* 居中主容器 */
        .main .block-container {{
            padding-top: 30vh; /* 将整体内容往下推，放在屏幕中央偏上 */
            max-width: 100%;
        }}
        
        /* 登录卡片样式 */
        .login-card {{
            background: transparent;
            padding: 20px;
            width: 100%;
            margin: 0 auto;
            text-align: center;
            position: relative;
            z-index: 10;
        }}
        
        /* 标题样式 */
        .login-title {{
            color: #ffffff;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5); /* 添加阴影确保在亮色背景下也能看清 */
        }}
        
        /* 按钮覆盖样式 */
        div[data-testid="stButton"] button {{
            width: 100%;
            background-color: #4A90E2;
            color: white;
            border: none;
            padding: 10px 0;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            margin-top: 15px;
            transition: background-color 0.3s;
        }}
        
        div[data-testid="stButton"] button:hover {{
            background-color: #357ABD;
            color: white;
        }}
        
        /* 输入框样式微调 */
        div[data-testid="stTextInput"] label {{
            display: none; /* 隐藏原生的label，用placeholder代替 */
        }}
        
        /* 强制输入框始终显示白色背景，防止鼠标移开后看不清 */
        div[data-testid="stTextInput"] input {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #333333 !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
        }}
        
        div[data-testid="stTextInput"] input::placeholder {{
            color: #666666 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 使用一个居中的列来包裹卡片
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown('<div class="login-title">Excel 智能翻译系统</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        input_key = st.text_input("卡密", type="password", placeholder="🔒 请输入您的卡密 / 管理员密码")
        
        if st.button("登 录"):
            if not input_key:
                st.error("请输入密码/卡密！")
            else:
                result = check_key(input_key)
                if result["valid"]:
                    st.session_state.logged_in = True
                    st.session_state.user_info = result["user"]
                    st.session_state.api_key = input_key
                    st.success("登录成功！即将跳转...")
                    st.rerun()
                else:
                    st.error(result["msg"])
                    
        st.markdown('</div>', unsafe_allow_html=True)