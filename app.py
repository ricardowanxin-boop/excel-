import streamlit as st
import os
from dotenv import load_dotenv

# 必须在最开始设置页面配置
st.set_page_config(
    page_title="Excel 大模型无损翻译器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed" # 默认折叠侧边栏
)

# 加载环境变量 (这必须在实例化 OpenAI client 之前运行)
load_dotenv()

# 初始化配置到 Session State，确保云端 Secrets 也能被正确读取
if 'api_key' not in st.session_state:
    # 优先从 Streamlit Secrets 读取，其次从环境变量读取
    st.session_state.api_key_config = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    st.session_state.api_base_url = st.secrets.get("OPENAI_BASE_URL", os.getenv("OPENAI_BASE_URL", ""))
    st.session_state.model_name = st.secrets.get("MODEL_NAME", os.getenv("MODEL_NAME", "gpt-3.5-turbo"))

# 为了让 core.translator 能拿到最新配置，我们需要将其写入环境变量（或者修改 translator 的实现）
os.environ["OPENAI_API_KEY"] = st.session_state.api_key_config
os.environ["OPENAI_BASE_URL"] = st.session_state.api_base_url
os.environ["MODEL_NAME"] = st.session_state.model_name

# 初始化数据库
from auth.db import init_db
init_db()

from ui.login import render_login_page
from ui.sidebar import render_sidebar
from ui.main_content import render_main
from ui.admin_dashboard import render_admin_dashboard

def main():
    # 重新从 session_state 获取最新状态，防止渲染延迟
    is_logged_in = st.session_state.get('logged_in', False)
    user_info = st.session_state.get('user_info', {})
    
    # 1. 如果未登录，只渲染全屏登录页面
    if not is_logged_in:
        # 强制隐藏侧边栏
        st.markdown(
            """
            <style>
                [data-testid="collapsedControl"] {
                    display: none;
                }
                [data-testid="stSidebar"] {
                    display: none;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        render_login_page()
        return

    # 2. 如果已登录，根据角色渲染不同页面
    # 恢复侧边栏显示（覆盖隐藏样式）
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {
                display: block;
            }
            [data-testid="stSidebar"] {
                display: block;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # 渲染侧边栏（包含登出功能和普通用户的配置）
    render_sidebar()
    
    if user_info.get('type') == 'admin':
        # 管理员界面
        render_admin_dashboard()
    else:
        # 普通用户翻译界面
        render_main()

if __name__ == "__main__":
    main()
