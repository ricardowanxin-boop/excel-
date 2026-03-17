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

    # CSS 样式：仅保留最基础的容器布局调整，移除所有对 Input/Button 的侵入式样式
    st.markdown(f"""
        {bg_css}
        <style>
        /* 隐藏顶部工具栏以更沉浸 */
        header {{visibility: hidden;}}
        
        /* 居中主容器 */
        .main .block-container {{
            padding-top: 20vh; /* 调整垂直位置 */
            max-width: 100%;
        }}
        
        /* 标题样式 - 使用原生 markdown 渲染，仅调整颜色 */
        .login-title {{
            color: #ffffff !important;
            font-size: 32px !important;
            font-weight: bold !important;
            margin-bottom: 20px !important;
            text-align: center !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        </style>
    """, unsafe_allow_html=True)

    # 使用 Streamlit 原生布局
    # 使用 3 列布局将内容居中
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 标题
        st.markdown('<div class="login-title">Excel 智能翻译系统</div>', unsafe_allow_html=True)
        
        # 使用 Streamlit 原生容器作为"卡片"
        # 这里的 border=False 是为了完全透明，如果需要边框可以设为 True
        with st.container():
            # 输入框 - 使用完全原生的 Streamlit 组件
            input_key = st.text_input(
                "请输入您的卡密 / 管理员密码", 
                type="password", 
                placeholder="🔒 请输入您的卡密 / 管理员密码",
                label_visibility="visible" # 恢复 Label 显示，避免布局塌陷，虽然我们可能不需要它
            )
            
            # 登录按钮 - 原生组件
            # use_container_width=True 让按钮充满容器宽度
            if st.button("登 录", type="primary", use_container_width=True):
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
