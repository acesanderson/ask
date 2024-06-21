"""
This module scrapes articles from the web.
"""

import sys
from newspaper import Article

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}


def is_url(url):
    if url.startswith('http') and len(url) > 10:
        return 'URL'
    elif url.startswith('[') and url.endswith(')'):
        return 'MARKDOWN_LINK'
    else:
        return 'NOT_A_URL'

def validate_url(url):
    status = is_url(url)
    match status:
        case 'URL':
            return url
        case 'MARKDOWN_LINK':
            return convert_markdown_link(url)
        case 'NOT_A_URL':
            return ValueError("Invalid URL")

def convert_markdown_link(link):
    cleaned_link = link
    if cleaned_link[-1] == ',':
        cleaned_link = cleaned_link[:-1]
    cleaned_link = cleaned_link.replace('[', '')
    cleaned_link = cleaned_link.replace(')', '')
    cleaned_link = cleaned_link.split('](')
    return cleaned_link

def download_article(url):
    """
    Feed this a url for an article, and it will return the text of the article.
    """
    url = validate_url(url)
    try:
        article = Article(url, request_headers=headers)
        article.download()
        article.parse()
        return article.text
    except:
        return f"Error with request: {url}."

if __name__ == "__main__":
    url = "https://link.springer.com/article/10.1007/s00146-023-01740-y"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    result = download_article(url)
    print(result)
