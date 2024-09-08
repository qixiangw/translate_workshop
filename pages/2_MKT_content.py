import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import logging
from botocore.exceptions import ClientError
import boto3

import langcodes
import json
import time

# import streamlit as st

st.set_page_config(
    page_title="MKT_translator",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class AmazonScraper:
    def __init__(self, region, category):
        self.region = region
        self.category = category
        self.base_urls = {
            'US': 'https://www.amazon.com/s?k=',
            'DE': 'https://www.amazon.de/s?k=',
            'JP': 'https://www.amazon.co.jp/s?k='
        }
        self.base_url = self.base_urls.get(region)
    

    def get_top_listings(self):
        if not self.base_url:
            return []

        search_url = self.base_url + self.category.replace(' ', '+')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        listings = []
        results = soup.find_all('div', {'data-component-type': 's-search-result'})
        for item in results[:10]:
            title = item.h2.get_text(strip=True)
            bullet_points = item.find_all('span', {'class': 'a-text-bullet'})
            bullet_list = [bullet.get_text(strip=True) for bullet in bullet_points]
            listings.append({'title': title, 'bullet_points': bullet_list})
        return listings
    def get_top_kw(self):
        keywords_dict = {
        "flashlight": {
            "US": [
                "rechargeable flashlights",
                "flashlights high lumens",
                "streamlight flashlight",
                "uv flashlight",
                "tactical flashlight"
            ],
            "DE": [
                "wiederaufladbare Taschenlampen",
                "Taschenlampe",
                "taktische Taschenlampe",
                "Streamlight-Taschenlampe",
                "Taschenlampen mit hoher Lumenleistung"
            ],
            "JP": [
                "じゅうでんしきかいちゅうでんとう",
                "こうきどかいちゅうでんとう",
                "ストリームライトかいちゅうでんとう",
                "ユーブイかいちゅうでんとう",
                "タクティカルかいちゅうでんとう"
            ]
        },
        "power bank": {
            "US": [
                "solar power bank",
                "portale charger power bank",
                "power bank for iphone",
                "power bank fast charging"
            ],
            "DE": [
                "Powerbank mit hoher Kapazität",
                "Leichte und kompakte Powerbank",
                "Solar-Powerbank"
            ],
            "JP": [
                "モバイルバッテリー 大容量",
                "モバイルバッテリー 軽量 小型",
                "ソーラーモバイルバッテリー"
            ]
        }}
        category = self.category
        region = self.region
        print(category,region)
        kw = keywords_dict[category][region]
        return kw

    

def keyword_aggregation(category, terms):
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )

    # Define the model ID for Claude 3.5 Sonnet
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    aspects = category

    prompt = f"""Given the following list of terms in <term> with products belongs to {aspects}. Find 10 representative term. Return the term names in JSON format list. With out any Explanation and Format tag.
    - Terms with similar or the same meaning should be merged into one term, while preserving the original intent.
    - The each terms you summarized must be simplified between 2 and 3 words with its corresponding detailed description.
    <term>{terms}</term>
    """
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}, {"role": "assistant", "content": [
        {"type": "text",
         "text": 'Based on the given review and rules, here is reslut in the requested JSON format:'}]}]

    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": messages
    }
    )

    response = bedrock.invoke_model(body=request_body, modelId=model_id)
    response_body = json.loads(response.get('body').read())
    response_text = response_body['content'][0]['text']

    return response_text

def find_keywords(listings):
    words = []
    for listing in listings:
        words.extend(listing['title'].split())
    word_counts = Counter(words)
    common_words = word_counts.most_common(20)
    keywords = [word for word, count in common_words]
    # keywords = keyword_aggregation(category, terms)
    

    return keywords


def translate_text(user_input,target_lang,tone,brand,model_id= "anthropic.claude-3-5-sonnet-20240620-v1:0"):   
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

        system_prompt = """You are an experienced e-commerce listing writer for amazon.com."""

        prompt = f"""任务是把<text>中的文本翻译并润色为{target_lang}表达。首先理解<text>中的原文，再结合SEO热门关键词<keywords>，语气风格是{tone}，然后翻译扩写<text>中的文本内容，品牌名是{brand},最后整理为amazon listing 格式，一个标题，五条bullet point，参考<output>输出Json格式。只用返回翻译结果不用其他注释。
        <text>
        {user_input}
        </text>
        <output>
            <title>
            Runstar Smart Scale for Body Weight and Fat Percentage, High Accuracy Digital Bathroom Scale FSA or HSA Eligible with LCD Display for BMI 13 Body Composition Analyzer Sync with Fitness App
            </title>
            <Aboutthisitem>
            1. Large LCD Screen Display: Instead of normal LCD display scales, the Runstar scale features a large display screen that shows 6 key measurements, including weight, body fat rate, BMI, muscle mass, body water rate and bone mass. You can completely free your hands to read these measurements at a glance without having to open your APP for every measurements.
            2. Three Guarantees for High Accuracy: This ultra-precision body fat scale, adopting the advanced BIA technology, is equipped with 4 high sensitive electrodes and 4 high precision G-shape sensors that have passed 100,000 times sensor performance tests to enhance accuracy.The scale ensures accurate measurement results to within 0.2lb/100g and has a maximum weight capacity of 400lb/180kg.
            3. 13 Essential Body Composition data Analyzer: Runstar Scale utilizes electrical Bio-Impedance Measurement Technology to calculate including Weight, BMI, Body Fat, Fat-free Body Weight, Subcutaneous Fat, Visceral Fat, Water, Muscle Mass, Bone Mass, Protein, BMR and Body Age. You can monitor and track your body data over time periods (by weeks, months or even years) on Starfit App anytime anywhere, which can help guide you towards a healthier lifestyle or track your fitness progress
            4. User-friendly APP: You can download the Starfit app from App Store or Google Play. The smart scale supports offline measurement, which allows the data be measured and automatically synced onto the APP after connecting the app to complete the first measurement. The app also syncs easily with other fitness apps like Apple Health, Google Fit and so on.
            5. Family Health Guardian: With the ability to create up to 24 user profiles and identify the user instantly when one steps on, the RunSTAR Scale is perfect for families and friends who want to track their body data for health. (Baby Mode supported.) The scale is great for bodybuilders, weight loss enthusiasts, and anyone who wants to maintain a healthy lifestyle.
            </Aboutthisitem>
        </output>
        """
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}, {"role": "assistant", "content": [
        {"type": "text",
         "text": 'Here is reslut in the requested JSON format:'}]}] 
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.1,
            "messages": messages
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


    


def main():
    st.title("电商营销素材翻译")
    st.write("使用LLM进行翻译可以更加灵活地适应风格化需求,以Amazon List的内容为例。")

    st.markdown("**1. 根据站点和品类搜索对应的最新关键词，可以由第三方Keywords tool获取，也可以从亚马逊后台品牌分析功能（ABA）获取**")
    st.markdown("**2. 在翻译产品名称和描述的时候，结合目标站点最新的热搜关键词。**")
    # st.image("./mkt_content_translate.jpg", caption="local")

    
    st.header("关键词生成")
    region = st.selectbox("选择站点", ['US', 'DE', 'JP'])
    category = st.selectbox("输入品类", ["flashlight","power bank"])
    
    if st.button("获取热门关键词"):
        scraper = AmazonScraper(region, category)
        #listings = scraper.get_top_listings()
        
        keywords = scraper.get_top_kw()

        if keywords:
            # df = pd.DataFrame(listings)
            # df['bullet_points'] = df['bullet_points'].apply(lambda x: "; ".join(x))
            # st.write("前5个产品列表:")
            # st.dataframe(df[['title', 'bullet_points']].head(5))
            # keywords = find_keywords(listings)
            st.write("对应站点的最新的热门关键词:（* 本搜索词排名数据来源于亚马逊后台品牌分析功能（ABA）截止0830）")
            for kw in keywords:
                    st.write(kw)
        else:
            st.write("未找到任何产品，请检查站点和品类。")

    
    st.header("翻译工具")
    product_description = st.text_area("输入产品描述")
    brand_name = st.text_input("输入品牌名")
    tone = st.selectbox("文本风格", ['正式', '促销'])

    if st.button("生成Listing"):
        if product_description and brand_name:
            target_language = 'en' if region == 'US' else 'de' if region == 'DE' else 'ja'

            translated_description = translate_text(product_description,target_language,tone,brand_name,model_id= "anthropic.claude-3-5-sonnet-20240620-v1:0")
            
            # title = " ".join(product_description.split()[:7])
            # bullet_points = [f"- {point}" for point in product_description.split(". ")]
            # translated_title = translate_text(title, target_language)
            # translated_bullet_points = [translate_text(point, target_language) for point in bullet_points]
            

            try:
                data = json.loads(translated_description)

                # st.write("## ")

                # 显示标题
                st.write("### Title:")
                st.write(data['title'])

                # 显示要点
                st.write("### About this item:")
                for point in data['Aboutthisitem']:
                    st.write(point)

            except json.JSONDecodeError:
                st.error("internal error")
        else:
            st.write("请输入产品描述和品牌名。")

if __name__ == '__main__':
    main()
