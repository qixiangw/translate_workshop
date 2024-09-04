import streamlit as st
import boto3
import langcodes
import json
import time
import logging
from botocore.exceptions import ClientError




st.set_page_config(
    page_title="Translator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("实时翻译对比")
st.write("Amazon Bedrock 提供多种成熟的大语言模型，LLM为翻译带来更大想象空间以及更高性价比。")

languages = {
    "English": "英语",
    "العربية": "阿拉伯语",
    "Deutsch": "德语",
    "Español": "墨西哥西班牙语",
    "Español (España)": "欧洲西班牙语",
    "Français": "法语",
    "हिन्दी": "印地语",
    "Italiano": "意大利语",
    "日本語": "日语",
    "한국어": "韩语",
    "Português": "葡萄牙语",
    "Русский": "俄语",
    "ไทย": "泰语",
    "Türkçe": "土耳其语",
    "Tiếng Việt": "越南语",
    "中文(简体)": "简体中文",
    "中文(繁體)": "繁体中文"
}
# different translate tools
def translate(model_id, text, target_lang):
    # 配置日志记录器
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    # 创建Amazon Bedrock Runtime客户端
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Set the model ID, e.g., Claude 3 Haiku.

    # Define the prompt for the model.
    prompt = f"translate the text {text} to languate {target_lang}"

    # Format the request payload using the model's native structure.
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    request = json.dumps(native_request)

    # 调用模型并获取响应流
    streaming_response = client.invoke_model_with_response_stream(
        modelId=model_id, body=request
    )

    for event in streaming_response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk["type"] == "content_block_delta":
            chunk_text = chunk["delta"].get("text", "")
            yield chunk_text

def translate_with_claude(model_id, target_lang, user_input):   
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

        prompt = f"""假设你是一个英语翻译助手，帮我把<text>中的文本翻译为口语地道的{target_lang}表达。只用返回翻译结果不用其他注释。
        <text>
        {user_input}
        </text>
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ]
        }
        response = bedrock.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        generated_text = response_body['content'][0]['text']
        return generated_text

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occurred: " + format(message))

def translatewithtranslate(target_lang, user_input):
    translate = boto3.client('translate')
    s_code = "auto"
    t_code = get_language_code(target_lang)
    response = translate.translate_text(
        Text=user_input,
        SourceLanguageCode=s_code,
        TargetLanguageCode=t_code
    )
    response_body = response.get('TranslatedText')
    return response_body

def get_language_code(language):
    try:
        return langcodes.find(language).language
    except LookupError:
        return 'zh'

# todo: custom prompt / evaluation module
# Streamlit application
def app():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)    

    user_input = st.text_area("输入要翻译的文本:", key="text_area")
    #target_lang = st.selectbox("选择目标语言", ["中文", "英语", "日语", "法语","韩语","西班牙语","德语"], key="target_lang")
    st.subheader("选择目标语言")
    target_lang = st.selectbox(
        "选择要翻译的目标语言",
        options=list(languages.keys()),
        format_func=lambda x: f"{x} - {languages[x]}"
    )
    button = st.button("翻译", key="translate_button")

    result_container = st.container()
    if button:
        with result_container:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Claude3 Haiku的翻译结果:**")
                model_id = "anthropic.claude-3-haiku-20240307-v1:0"
                start_time = time.time()
                text = translate_with_claude(model_id, target_lang, user_input)
                end_time = time.time()
                st.write(text)
                st.write(f"耗时: {end_time - start_time:.2f} 秒")
        
            with col2:
                st.markdown("**Claude3.5 Sonnet翻译结果:**")
                model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
                start_time = time.time()
                text = translate_with_claude(model_id, target_lang, user_input)
                end_time = time.time()
                st.write(text)
                st.write(f"耗时: {end_time - start_time:.2f} 秒")

            with col3:
                st.markdown("**Amazon Translate翻译结果:**")
                start_time = time.time()
                text = translatewithtranslate(target_lang, user_input)
                end_time = time.time()
                st.write(text)
                st.write(f"耗时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    app()
