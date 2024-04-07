import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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
            result_list_of_title_and_summary.append( (title, summary) )
    return result_list_of_title_and_summary

def main():
    print('crawling from NY Times')
    result_list_of_title_and_summary = get_NYT_headline()
    print(f'total {len(result_list_of_title_and_summary)} headlines')
    table_text = '| title | ko_title | summary | ko_summary | words |\n|-------|----------|---------|------------|-------|\n'
    table_content = [f'| {title} |   | {summary} |    |    |' for title,summary in result_list_of_title_and_summary]
    table_text = table_text+'\n'.join(table_content)
    print(table_text)

if __name__ == "__main__":
  main()
