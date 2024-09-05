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
    "Deutsch": "德语",
    "Français": "法语",
    "日本語": "日语",
    "한국어": "韩语",
    "ไทย": "泰语",
    "Tiếng Việt": "越南语",
    "中文(简体)": "简体中文",
    "العربية": "阿拉伯语",
    "हिन्दी": "印地语",
    "Italiano": "意大利语",
    "Português": "葡萄牙语",
    "Русский": "俄语", 
    "Türkçe": "土耳其语",
    "Español": "墨西哥西班牙语",
    "Español (España)": "欧洲西班牙语",
    "中文(繁體)": "繁体中文"
}

# different translate tools
def translate_streaming(model_id, text, target_lang):
    
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

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
        bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

        prompt = f"""translate the <text> to languate {target_lang}。只返回翻译结果不用其他注释。
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

def evalation_claude(target_lang, result_text):   
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

        prompt = f"""假设你是一个{target_lang}语言专家，评估<text>中的三种表达方式。始终用中文回答。
        <text>
        {result_text}
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

    if 'result_text' not in st.session_state:
        st.session_state.result_text = [None, None, None]
    if 'translation_done' not in st.session_state:
        st.session_state.translation_done = False

    button = st.button("翻译", key="translate_button")

    result_container = st.container()

    if st.session_state.translation_done or button:

        with result_container:
            col1, col2, col3 = st.columns(3)
            st.session_state.time_spend = None
            with col1:
                st.markdown("**Claude3 Haiku的翻译结果:**")
                if button:
                    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
                    start_time = time.time()
                    text = translate_with_claude(model_id, target_lang, user_input)
                    end_time = time.time()
                    st.session_state.time_spend = round(end_time - start_time, 2)
                    st.session_state.result_text[0] = text
                    st.session_state.translation_done = True
                    st.write(f"耗时: {st.session_state.time_spend} 秒")
                if st.session_state.result_text[0]:
                    st.write(st.session_state.result_text[0])
                    
    
        
            with col2:
                st.markdown("**Claude3.5 Sonnet翻译结果:**")
                if button:
                    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
                    start_time = time.time()
                    text = translate_with_claude(model_id, target_lang, user_input)
                    end_time = time.time()
                    st.session_state.time_spend = round(end_time - start_time, 2)
                    st.session_state.result_text[1] = text
                    st.write(f"耗时: {st.session_state.time_spend} 秒")
                if st.session_state.result_text[1]:
                    st.write(st.session_state.result_text[1])
                    

            with col3:
                st.markdown("**Amazon Translate翻译结果:**")
                if button:
                    start_time = time.time()
                    text = translatewithtranslate(target_lang, user_input)
                    end_time = time.time()
                    st.session_state.time_spend = round(end_time - start_time, 2)
                    st.session_state.result_text[2] = text
                    st.write(f"耗时: {st.session_state.time_spend} 秒")
                if st.session_state.result_text[2]:   
                    st.write(st.session_state.result_text[2])
                    
        
        button_2 = st.button("对比翻译结果", key="translate_compar_button")
        if button_2:
            res = evalation_claude(target_lang, st.session_state.result_text)
            st.write(res)


if __name__ == "__main__":
    app()
