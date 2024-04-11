import requests
from bs4 import BeautifulSoup

import os
import json
from pprint import pprint
from datetime import datetime, timedelta

from github_utils import get_github_repo, upload_github_issue

from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

LLM = ChatOpenAI(model_name="gpt-3.5-turbo")

def get_NYT_headline(days_ago = 1):
    yesterday = datetime.now() + timedelta(days=-abs(days_ago))
    print(yesterday)

    url = f'https://messaging-custom-newsletters.nytimes.com/template/todaysheadlines?date={yesterday.date()}'

    print(url)
    response = requests.get(url)
    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')

    result_list_of_title_and_summary = []
    h3_elements = soup.find_all('h3')
    for h3 in h3_elements:
        title = h3.text.strip()
        summary = h3.find_next_siblings()[-1].text.strip()
        if 'Video:' not in title:
            result_list_of_title_and_summary.append( {'title':title, 'summary':summary} )
    return result_list_of_title_and_summary

def get_llm_response_md(news_headlines_json, doc_length = 5, llm = LLM):
    prompt_head = '''넌 지금부터 모국어가 한국어인 영어 초보자에게 영어를 가르쳐주는 아주 친절하고 현명한 선생님이야.'''
    prompt_tail = '''여기 {doc_length}개의 뉴스 헤드라인이 json 형태로 작성되어 있어.
1. 출력 양식은 JSON array 형태로 출력해줘. 각각의 뉴스는
    'korean_title':'',
    'korean_summary':'',
    'words':[
        "english_word (한글 뜻)",
        ...
        ] 형태로 맞춰서 출력해.
2. 개별 뉴스를 양식에 맞춰서 한글로 번역해.
3. 각각의 중요 핵심단어를 3~5개정도 정리해주고, '영어단어(한글뜻)' 형태로 출력해.
4. 무조건 {doc_length}개의 JSON object list 형태로 변환해서 출력해. 출력전에 json spec 에 맞도록 sanitize를 꼭 해야해.
# output : '''
    prompt = ChatPromptTemplate.from_template(prompt_head + '{news_headlines}'+ prompt_tail)

    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({'news_headlines': news_headlines_json , 'doc_length':doc_length})

    return result

def get_markdown_output(result_list):
    result_text = 'No. | news | translated | words\n---|---|---|---\n'
    KEYS = ['title', 'korean_title', 'summary', 'korean_summary', 'words']
    for no, obj in enumerate(result_list):
        origin_text = f"**{obj['title']}** - {obj['summary']}"
        korean_text = f"**{obj['korean_title']}** - {obj['korean_summary']}"
        words_text = ' , '.join(obj['words'])
        result_text = result_text + f'{no+1} | {origin_text} | {korean_text} | {words_text}\n'

    return result_text

def main():
    access_token = os.environ['MY_GITHUB_TOKEN']
    repository_name = "eng_test"
    
    print('crawling from NY Times')
    result_list_of_title_and_summary = get_NYT_headline()
    print(f'total {len(result_list_of_title_and_summary)} headlines')
    
    result_json = []
    step = 8
    for i in range(0, len(result_list_of_title_and_summary), step):
        print(i)
        temp_result = get_llm_response_md(json.dumps(result_list_of_title_and_summary[i:i+step]), len(result_list_of_title_and_summary[i:i+step]))
        temp_result_json = json.loads(temp_result)
        print(len(result_list_of_title_and_summary[i:i+step]), len(temp_result_json))
        temp_merged_list = [ result_list_of_title_and_summary[i+delta] | temp_result_json[delta] for delta in range(len(temp_result_json))]
        result_json = result_json + temp_merged_list
        
    result_md_table = get_markdown_output(result_json)
    current_datetime = datetime.now().strftime("%Y-%m-%d")
    issue_title = f"NYT_{current_datetime}"
    repo = get_github_repo(access_token, repository_name)
    upload_github_issue(repo, issue_title, result_md_table)
    

if __name__ == "__main__":
  main()
