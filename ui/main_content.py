import streamlit as st
import pandas as pd
from core.excel_parser import get_sheet_names, extract_texts, apply_translations
from core.translator import translate_batch
from auth.db import consume_quota

def render_main():
    st.title("📊 Excel 大模型无损翻译器")
    st.markdown("基于大模型的智能Excel翻译工具。支持保持原格式无损翻译，内存级处理保障隐私。")
    
    # 状态初始化
    if 'translated_file' not in st.session_state:
        st.session_state.translated_file = None
    if 'translation_result' not in st.session_state:
        st.session_state.translation_result = None
        
    is_logged_in = st.session_state.get('logged_in', False)
    
    if not is_logged_in:
        st.warning("⚠️ 请先在左侧侧边栏输入卡密登录后，才能使用上传和翻译功能。")
        
    # 如果未登录，禁用文件上传组件
    uploaded_file = st.file_uploader(
        "📂 请上传需要翻译的 Excel 文件 (.xlsx)", 
        type=["xlsx"],
        disabled=not is_logged_in
    )
    
    if uploaded_file and is_logged_in:
        file_bytes = uploaded_file.read()
        
        try:
            sheet_names = get_sheet_names(file_bytes)
        except Exception as e:
            st.error(f"解析文件失败，请确保是有效的 Excel 文件: {e}")
            return
            
        card_type = st.session_state.user_info.get('type', 'count_sheet')
        if card_type == 'count':
            card_type = 'count_sheet' # 兼容旧数据
            
        if card_type == 'count_file':
            st.info("💎 当前为【全文件计次卡】，将自动扫描并翻译所有工作表。")
            selected_sheets = sheet_names
        else:
            options = sheet_names
            if card_type == 'time':
                options = ["全部工作表 (All Sheets)"] + sheet_names
                
            selected_option = st.selectbox("请选择要翻译的工作表", options)
            if selected_option == "全部工作表 (All Sheets)":
                selected_sheets = sheet_names
            else:
                selected_sheets = [selected_option]
        
        # 使用两列布局，左边是翻译按钮，右边是可能出现的取消按钮
        col1, col2 = st.columns([1, 1])
        
        with col1:
            start_btn = st.button("🚀 开始解析与翻译", type="primary")
            
        # 如果点击了开始，或者之前已经开始了但未完成（通常在 streamlit 中点击内部按钮会重载）
        if start_btn or st.session_state.get('is_translating', False):
            # 开始前先检查额度是否足够，如果不够直接退出，给出友好提示
            from auth.db import check_key
            check_result = check_key(st.session_state.api_key)
            if not check_result["valid"] or check_result["user"]["quota_left"] < 1:
                st.error("⚠️ 您的翻译额度已用尽！系统即将退出登录。如需继续使用服务，请购买新的额度卡密。")
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.session_state.api_key = ""
                st.session_state.is_translating = False
                st.stop() # 使用 st.stop() 立即停止执行，让用户看清提示，而不是立刻 rerun 刷掉页面
            
            # 标记正在翻译中
            st.session_state.is_translating = True
            
            if not st.session_state.get('logged_in', False):
                st.error("请先在左侧侧边栏登录或激活卡密！")
                st.session_state.is_translating = False
                return
                
            config = st.session_state.config
            
            # 在右侧列显示取消按钮
            with col2:
                cancel_btn = st.button("❌ 取消翻译", type="secondary")
                if cancel_btn:
                    st.session_state.is_translating = False
                    st.warning("用户已中断翻译，本次未扣除卡密额度。")
                    st.rerun()
            
            with st.status("正在处理中...", expanded=True) as status:
                st.write("1️⃣ 正在解析 Excel 内容...")
                global_original_map = {}
                try:
                    for sheet in selected_sheets:
                        texts_dict = extract_texts(
                            file_bytes, 
                            sheet,
                            ignore_formulas=config['ignore_formulas'],
                            ignore_numbers=config['ignore_numbers'],
                            ignore_header_rows=config['ignore_header_rows']
                        )
                        if texts_dict:
                            for coord, text in texts_dict.items():
                                global_original_map[(sheet, coord)] = text
                except Exception as e:
                    status.update(label="解析失败", state="error")
                    st.error(f"提取文本失败: {e}")
                    st.session_state.is_translating = False
                    return
                    
                if not global_original_map:
                    status.update(label="处理完成", state="complete")
                    st.warning("未找到需要翻译的文本！")
                    st.session_state.is_translating = False
                    return
                    
                unique_strings = list(set(global_original_map.values()))
                st.write(f"共提取到 {len(global_original_map)} 个有效单元格，去重后共有 {len(unique_strings)} 条独立文本待翻译。")
                
                st.write(f"2️⃣ 正在调用大模型进行批量翻译 (目标语言: {config['target_lang']})...")
                
                # 为了防止请求过大，可以分批处理
                batch_size = 50
                translated_unique_texts = []
                
                progress_bar = st.progress(0)
                try:
                    for i in range(0, len(unique_strings), batch_size):
                        # 检查是否点击了取消
                        if cancel_button:
                            status.update(label="已取消翻译", state="error")
                            st.warning("用户已中断翻译，本次未扣除卡密额度。")
                            return
                            
                        batch = unique_strings[i:i+batch_size]
                        res = translate_batch(batch, config['target_lang'], config['scene'])
                        translated_unique_texts.extend(res)
                        progress = min((i + batch_size) / len(unique_strings), 1.0)
                        progress_bar.progress(progress)
                        
                    if len(translated_unique_texts) != len(unique_strings):
                        raise ValueError("翻译结果数量与原文数量不匹配")
                        
                except Exception as e:
                    # 尝试从 RetryError 中提取真实的错误信息
                    error_msg = str(e)
                    if hasattr(e, 'last_attempt') and e.last_attempt:
                        error_msg = str(e.last_attempt.exception())
                    
                    status.update(label="翻译失败", state="error")
                    st.error(f"翻译过程中发生错误:\n {error_msg}")
                    st.session_state.is_translating = False
                    return
                    
                string_trans_map = dict(zip(unique_strings, translated_unique_texts))
                
                st.write("3️⃣ 正在将翻译结果无损写回 Excel...")
                new_file_bytes = file_bytes
                
                try:
                    for sheet in selected_sheets:
                        sheet_translations = {}
                        sheet_original_map = {}
                        for (s, coord), orig_text in global_original_map.items():
                            if s == sheet:
                                sheet_translations[coord] = string_trans_map[orig_text]
                                sheet_original_map[coord] = orig_text
                        
                        if sheet_translations:
                            new_file_bytes = apply_translations(new_file_bytes, sheet, sheet_translations, sheet_original_map)
                except Exception as e:
                    status.update(label="生成文件失败", state="error")
                    st.error(f"写回Excel时发生错误: {e}")
                    st.session_state.is_translating = False
                    return
                    
                # 保存状态以供展示
                st.session_state.translated_file = new_file_bytes
                
                # 构建预览数据
                preview_data = []
                preview_count = 0
                for (sheet, coord), orig_text in global_original_map.items():
                    if preview_count >= 100:
                        break
                    preview_data.append({
                        "工作表": sheet,
                        "单元格": coord,
                        "原文": orig_text,
                        "译文": string_trans_map[orig_text]
                    })
                    preview_count += 1
                st.session_state.translation_result = preview_data
                
                # 翻译成功后扣除额度
                if not consume_quota(st.session_state.api_key, 1):
                    # 理论上不应该走到这里，因为前面拦截了
                    st.error("卡密额度扣除失败。")
                else:
                    status.update(label="翻译完成！已扣除 1 次额度。", state="complete")
                
                # 更新 session_state 中的 user_info 以便侧边栏实时显示最新额度
                check_result = check_key(st.session_state.api_key)
                if check_result["valid"]:
                    st.session_state.user_info = check_result["user"]
                
                # 重置翻译状态
                st.session_state.is_translating = False
                
        # 展示预览和下载
        if st.session_state.translation_result:
            st.success("翻译成功！您可以预览部分结果，或直接下载文件。")
            
            st.download_button(
                label="📥 下载翻译后的 Excel 文件",
                data=st.session_state.translated_file,
                file_name=f"translated_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
            
            st.subheader("👀 翻译预览 (最多显示100条)")
            df = pd.DataFrame(st.session_state.translation_result)
            st.dataframe(df, use_container_width=True)
