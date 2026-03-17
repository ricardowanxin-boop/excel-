import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

PROMPTS = {
    "通用办公": "你是一个专业的Excel表格翻译助手。请将给定的文本列表准确翻译为{target_lang}。注意保持原文的专业术语，如果是表头请保持简练。",
    "商务贸易": "你是一个资深的跨境贸易和商务翻译专家。请将给定的文本列表翻译为{target_lang}，要求符合国际贸易术语、商务合同及报表规范。",
    "IT互联网": "你是一个资深的IT互联网产品和技术翻译专家。请将给定的文本列表翻译为{target_lang}，要求符合互联网行业黑话、技术文档及UI文案规范。"
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
def translate_batch(texts: List[str], target_lang: str, scene: str = "通用办公") -> List[str]:
    """
    批量翻译文本，使用JSON模式确保返回格式一致，并带有重试机制
    """
    if not texts:
        return []

    # 构造系统提示词
    system_prompt = PROMPTS.get(scene, PROMPTS["通用办公"]).format(target_lang=target_lang)
    system_prompt += "\n请严格返回JSON格式，结构必须为：{\"result\": [\"翻译后的文本1\", \"翻译后的文本2\", ...]}。数组长度必须与输入的文本列表长度完全一致。不要返回任何其他内容。"

    # 将文本列表转为JSON字符串
    user_content = json.dumps(texts, ensure_ascii=False)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"待翻译文本列表：\n{user_content}"}
            ],
            temperature=0.3
            # 注意：移除 response_format 参数，因为 ModelScope 的 Qwen 模型可能不支持严格的 json_object 模式
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 尝试清理可能出现的 Markdown JSON 标记
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        try:
            # 解析结果：如果返回的是对象 {"result": [...] } 或直接是数组 [...]
            parsed = json.loads(result_text)
            if isinstance(parsed, dict):
                # 寻找字典中第一个列表类型的值
                for v in parsed.values():
                    if isinstance(v, list):
                        translated_list = v
                        break
                else:
                    raise ValueError("JSON响应中没有找到数组")
            elif isinstance(parsed, list):
                translated_list = parsed
            else:
                raise ValueError("JSON格式不正确")
                
            if len(translated_list) != len(texts):
                # 降级处理：如果长度不一致，记录日志或重试（这里简单抛出异常触发tenacity重试）
                raise ValueError(f"返回数组长度({len(translated_list)})与输入长度({len(texts)})不一致")
                
            return [str(item) for item in translated_list]
            
        except json.JSONDecodeError:
            raise ValueError(f"无法解析LLM返回的JSON：{result_text}")
            
    except Exception as e:
        print(f"翻译请求失败: {str(e)}")
        # 抛出原始异常，这样可以让我们在前端看到具体的错误信息，而不仅仅是 RetryError
        raise
