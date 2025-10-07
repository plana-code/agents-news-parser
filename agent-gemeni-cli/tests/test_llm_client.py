
from src.llm_client import extract_news_with_llm

def test_extract_news_with_llm():
    """Tests if the extract_news_with_llm function returns a valid JSON response."""
    html_content = """
    <html>
        <body>
            <h1>Test Title</h1>
            <p>Test Description</p>
            <span>2025-10-07</span>
        </body>
    </html>
    """
    response = extract_news_with_llm(html_content)
    assert isinstance(response, dict)
    assert "choices" in response
