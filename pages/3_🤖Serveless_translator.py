import streamlit as st
import boto3
import os
import langcodes
import json
from botocore.exceptions import ClientError
import logging
import time
from botocore.exceptions import NoCredentialsError



# env
# S3_BUCKET = 'YOUR_S3_BUCKET_NAME'

# init
s3 = boto3.client('s3')

# lang
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

def upload_to_s3(file, bucket, s3_file):
    try:
        s3.upload_fileobj(file, bucket, s3_file)
        return True
    except NoCredentialsError:
        st.error("AWS凭证无效")
        return False

def check_subtitles(bucket, video_name):
    prefix = f"{os.path.splitext(video_name)[0]}_"
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return 'Contents' in response

def main():
    st.set_page_config(
    page_title="Subtitle Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    )

    st.title("离线视频翻译系统")
    #st.title("Subtitle Translation with Amazon Bedrock and Severless service")
    st.write("Amazon Bedrock 提供多种成熟的大语言模型，LLM为翻译带来更大想象空间以及更高性价比。")
    
    S3_BUCKET = st.text_input("输入S3桶名", "your-bucket-name")

    # 文件上传
    uploaded_file = st.file_uploader("选择带字幕的视频文件，或者字幕文件", type=['mp4', 'avi', 'mov'])
    if uploaded_file is not None:
        if st.button('上传到S3'):
            with st.spinner('正在上传...'):
                if upload_to_s3(uploaded_file, S3_BUCKET, uploaded_file.name):
                    st.success("文件成功上传到S3!")
                else:
                    st.error("上传失败")

    # 语言选择
    st.subheader("选择目标语言")
    selected_languages = st.multiselect(
        "选择要翻译的目标语言",
        options=list(languages.keys()),
        format_func=lambda x: f"{x} - {languages[x]}"
    )

    # 进度查询
    st.subheader("翻译进度查询")
    video_name = st.text_input("输入视频文件名")
    if st.button('查询进度'):
        if check_subtitles(S3_BUCKET, video_name):
            st.success("多语言字幕已生成!")
            
            # 下载按钮
            if st.download_button(
                label="下载多语言字幕",
                data=s3.get_object(Bucket=S3_BUCKET, Key=f"{os.path.splitext(video_name)[0]}_subtitles.zip")['Body'].read(),
                file_name=f"{os.path.splitext(video_name)[0]}_subtitles.zip",
                mime="application/zip"
            ):
                st.success("字幕文件下载成功!")
        else:
            st.info("多语言字幕尚未生成,请稍后再试")

if __name__ == "__main__":
    main()
