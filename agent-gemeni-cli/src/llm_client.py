
import requests
import json

OPENROUTER_API_KEY = "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"
MODEL_NAME = "nousresearch/hermes-2-pro-llama-3-8b"

def extract_news_with_llm(html_content: str) -> dict:
    """
    Extracts news from HTML content using the OpenRouter API.
    """
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        data=json.dumps({
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a news extraction expert. From the following text, identify and extract only the news articles. Ignore all navigation menus, headers, footers, and other non-news content. For each news article, extract the title, a brief description, and the publication date. Return the result as a JSON object with a key 'articles' which is a list of these news articles. Each article in the list should be a dictionary with the keys 'title', 'description', and 'publication_date'. If no news articles are found, return an empty list."
                },
                {
                    "role": "user",
                    "content": html_content[:4000]
                }
            ]
        })
    )
    response.raise_for_status()
    return response.json()
