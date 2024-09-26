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
    prefix = "output/" + video_name
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return 'Contents' in response

def main():
    st.set_page_config(
    page_title="Subtitle Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    )

    st.title("视频字幕翻译")
    #st.title("Subtitle Translation with Amazon Bedrock and Severless service")
    st.write("Amazon Bedrock 提供多种成熟的大语言模型，LLM为翻译带来更大想象空间以及更高性价比。")

    S3_BUCKET = st.text_input("输入S3桶名", "your-bucket-name")

    st.write("## 视频带字幕文件")
    #st.title("Subtitle Translation with Amazon Bedrock and Severless service")
    st.write("同时上传视频和字幕文件，视频和字幕需要同名，比如视频名称为sucai.mp4,字幕文件为sucai.srt")
    uploaded_mp4_with_srt= st.file_uploader("视频文件", type=['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'mpeg'])
    uploaded_srt= st.file_uploader("字幕文件，应与视频文件同名", type=['srt'])

    if uploaded_mp4_with_srt is not  None and uploaded_srt is not None:
        if st.button("上传视频和字幕到s3"):
            with st.spinner('正在上传...'):
                movies_with_srt_folder = "movies_with_srt/"
                movies_with_srt_folder_object_key = movies_with_srt_folder + uploaded_mp4_with_srt.name
                srt_folder = "input/"
                srt_folder_object_key = srt_folder + uploaded_srt.name
                if upload_to_s3(uploaded_mp4_with_srt,S3_BUCKET,movies_with_srt_folder_object_key) and upload_to_s3(uploaded_srt,S3_BUCKET,srt_folder_object_key):
                    st.success(f"视频文件成功上传到{S3_BUCKET}的{movies_with_srt_folder}文件夹!字幕文件成功上传到{S3_BUCKET}的{srt_folder}")
                else:
                    st.error("上传失败")

            
    st.write("## 视频不带字幕文件")
    # 文件上传
    uploaded_file = st.file_uploader("选择视频文件", type=['mp4', 'avi', 'mov', 'wmv'])
    if uploaded_file is not None:
        if st.button('上传到S3'):
            with st.spinner('正在上传...'):
                movies_without_srt_folder = "movies_without_srt/"
                s3_object_key = movies_without_srt_folder + uploaded_file.name
                if upload_to_s3(uploaded_file, S3_BUCKET, s3_object_key):
                    st.success(f"文件成功上传到{S3_BUCKET}的{movies_without_srt_folder}文件夹!")
                else:
                    st.error("上传失败")

        input_file_name = uploaded_file.name
        new_key_name = input_file_name.replace('.srt', '_translated.srt')
        folder_path = 'output/'
        new_key = folder_path + new_key_name

        if check_subtitles(S3_BUCKET, new_key):
            st.success("多语言字幕已生成!")

            # 下载按钮
            if st.download_button(
                label="下载",
                data=s3.get_object(Bucket=S3_BUCKET, Key=new_key)['Body'].read(),
                file_name= new_key_name
            ):
                st.success("字幕文件下载成功!")

    # 语言选择

    #st.markdown("#### 选择目标语言")
    #selected_languages = st.multiselect(
        #"选择要翻译的目标语言",
        #options=list(languages.keys()),
        #format_func=lambda x: f"{x} - {languages[x]}"
    #)


    # 进度查询
    # st.markdown("#### 翻译进度查询")
    # video_name = st.text_input("输入视频文件名")

    # 进度查询
    st.subheader("翻译进度查询")
    video_name = st.text_input("输入视频文件名").split('.')[0]+"_translated"+".srt"
    if st.button('查询进度'):
        if check_subtitles(S3_BUCKET, video_name):
            st.success("多语言字幕已生成!")

            # 下载按钮
            if st.download_button(
                label="下载多语言字幕",
                data=s3.get_object(Bucket=S3_BUCKET, Key="output/"+video_name)['Body'].read(),
                file_name=video_name,
                mime="text/plain"
            ):
                st.success("字幕文件下载成功!")
        else:
            st.info("多语言字幕尚未生成,请稍后再试")




if __name__ == "__main__":
    main()
