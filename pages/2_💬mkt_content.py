import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import logging
from botocore.exceptions import ClientError
import boto3
import streamlit as st
import boto3
import langcodes
import json
import time
import logging
from botocore.exceptions import ClientError

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

def find_keywords(listings):
    ##############################################################################
    #############llm做词聚类######################################################
    ##############################################################################
    words = []
    for listing in listings:
        words.extend(listing['title'].split())
    word_counts = Counter(words)
    common_words = word_counts.most_common(10)
    keywords = [word for word, count in common_words]
    return keywords


def translate_text(user_input,target_lang,model_id= "anthropic.claude-3-5-sonnet-20240620-v1:0"):   
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

        ##############################################################################
        #############system pe / {tone}{keyword}{example} listing output 格式prefill###
        ##############################################################################

        prompt = f"""把<text>中的文本翻译为{target_lang}表达。注意扩写内容为amazon listing 格式，只用返回翻译结果不用其他注释。
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


    


def main():
    st.title("亚马逊Listing优化工具")
    st.write("使用LLM进行翻译可以更加灵活地适应风格化需求。")
    ###################？？？？？####st.write("xxx 营销翻译的说明")
    col1, col2 = st.columns(2)

    with col1:
        st.header("关键词生成")
        region = st.selectbox("选择站点", ['US', 'DE', 'JP'])
        category = st.text_input("输入品类", "flashlight")
        
        if st.button("获取产品列表"):
            scraper = AmazonScraper(region, category)
            listings = scraper.get_top_listings()
            ################################################title和listing没分开
            if listings:
                df = pd.DataFrame(listings)
                df['bullet_points'] = df['bullet_points'].apply(lambda x: "; ".join(x))
                st.write("前5个产品列表:")
                st.dataframe(df[['title', 'bullet_points']].head(5))
                keywords = find_keywords(listings)
                st.write("前10个关键词:")
                st.write(", ".join(keywords))
            else:
                st.write("未找到任何产品，请检查站点和品类。")

    with col2:
        st.header("翻译工具")
        product_description = st.text_area("输入产品描述")
        brand_name = st.text_input("输入品牌名")
        tone = st.selectbox("文本风格", ['正式', '促销'])

        if st.button("生成Listing"):
            if product_description and brand_name:
                target_language = 'en' if region == 'US' else 'de' if region == 'DE' else 'ja'
                translated_description = translate_text(product_description, target_language)

                ###########################################################
                title = " ".join(product_description.split()[:7])
                bullet_points = [f"- {point}" for point in product_description.split(". ")]
                translated_title = translate_text(title, target_language)
                translated_bullet_points = [translate_text(point, target_language) for point in bullet_points]
                ##########################################################
                st.write("## 生成的Listing")
                st.write(f"### 标题: {translated_title}")
                st.write("### Bulletpoints:")
                for point in translated_bullet_points:
                    st.write(point)
            else:
                st.write("请输入产品描述和品牌名。")

if __name__ == '__main__':
    main()