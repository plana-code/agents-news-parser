"""LLM Integration Module

This module handles integration with OpenRouter API for extracting
structured news data from HTML content.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import json
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """Represents a single news item extracted from a webpage."""

    title: str
    description: str = ""
    publication_date: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert news item to dictionary format."""
        return {
            "title": self.title,
            "description": self.description,
            "publication_date": self.publication_date
        }


class OpenRouterService:
    """Service for extracting structured news data using OpenRouter LLM API.

    Features:
    - Prompt engineering for news extraction
    - Token management
    - Error handling and retries
    - Response validation
    - Uses FREE models only (no API costs)

    Recommended FREE models (with minimal censorship):
    - qwen/qwen3-coder:free (default - excellent for structured data extraction)
    - nvidia/nemotron-nano-9b-v2:free (fast and efficient)
    - openai/gpt-oss-20b:free (open-source OpenAI model)
    - meituan/longcat-flash-chat:free (good for chat/text processing)
    - z-ai/glm-4.5-air:free (general purpose)

    Note: Free models have rate limits (~50-1000 requests/day depending on credits)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen3-coder:free",
        max_retries: int = 3,
        timeout: int = 120
    ):
        """Initialize the OpenRouter service.

        Args:
            api_key: OpenRouter API key
            model: Model identifier to use for extraction
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds

        Raises:
            ValueError: If API key is invalid or missing
        """
        # Validate API key
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required but not provided")

        if not api_key.startswith("sk-or-v1-"):
            raise ValueError(
                "Invalid OPENROUTER_API_KEY format. "
                "Expected format: sk-or-v1-xxxxx... "
                "Get your key from https://openrouter.ai/"
            )

        if len(api_key) < 50:
            raise ValueError(
                "OPENROUTER_API_KEY appears to be incomplete or invalid. "
                "OpenRouter keys are typically 60+ characters. "
                "Please check your key at https://openrouter.ai/"
            )

        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.max_retries = max_retries
        self.timeout = timeout
        logger.info(f"OpenRouterService initialized with model: {model}")

    def extract_news(self, html_content: str, url: str) -> List[NewsItem]:
        """Extract news items from HTML content using LLM.

        Args:
            html_content: Raw HTML content from the webpage
            url: Source URL (for context)

        Returns:
            List of NewsItem objects extracted from the content

        Raises:
            ValueError: If HTML content is empty or invalid
            RuntimeError: If API request fails after all retries
        """
        if not html_content or not html_content.strip():
            raise ValueError("HTML content is empty")

        logger.info(f"Extracting news from URL: {url} (HTML length: {len(html_content)} chars)")

        # Clean and prepare HTML
        cleaned_html = self._clean_html(html_content)
        logger.debug(f"Cleaned HTML length: {len(cleaned_html)} chars")

        # Build extraction prompt
        prompt = self._build_extraction_prompt(cleaned_html, url)

        # Call LLM API with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                response_data = self._call_llm_api(prompt, attempt)
                news_items = self._parse_llm_response(response_data)
                logger.info(f"Successfully extracted {len(news_items)} news items")
                return news_items
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"Failed to extract news after {self.max_retries} attempts: {str(e)}")
                # Exponential backoff
                wait_time = min(2 ** attempt, 30)
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        return []  # Should not reach here

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML to reduce token usage and improve extraction.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned HTML with main content only
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'meta', 'link', 'noscript', 'iframe', 'svg']):
                tag.decompose()

            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
                comment.extract()

            # Remove form elements and inputs (often have malformed data)
            for tag in soup(['form', 'input', 'button', 'select', 'textarea']):
                tag.decompose()

            # Get text with some structure preserved
            # Try to find main content areas - prioritize news/article containers
            main_content = None
            for selector in [
                'main',
                'div[class*="news"]',
                'div[class*="article"]',
                'section[class*="news"]',
                'div[id*="news"]',
                'div[class*="content"]',
                'body'
            ]:
                main_content = soup.select_one(selector)
                if main_content:
                    logger.debug(f"Found main content using selector: {selector}")
                    break

            if main_content:
                # Get text with line breaks preserved
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)

            # Sanitize text to prevent JSON parsing issues
            # Remove control characters except newline and tab
            import re
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)

            # Normalize whitespace
            text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

            # Increased limit to capture more news articles (free models support up to ~100k tokens)
            # Gazeta.ru and similar sites may have 10-30+ articles on main page
            max_chars = 80000
            if len(text) > max_chars:
                logger.info(f"Text truncated from {len(text)} to {max_chars} chars to fit LLM limits")
                text = text[:max_chars] + "\n\n[Content truncated - showing first 80000 characters]"
            else:
                logger.debug(f"Text length: {len(text)} chars (within {max_chars} limit)")

            return text

        except Exception as e:
            logger.warning(f"Error cleaning HTML: {str(e)}, using original content")
            # Fallback to simple text extraction
            return html_content[:20000]

    def _build_extraction_prompt(self, cleaned_html: str, url: str) -> str:
        """Build the prompt for news extraction.

        Args:
            cleaned_html: Cleaned HTML/text content
            url: Source URL

        Returns:
            Formatted prompt string
        """
        system_prompt = """You are a news extraction assistant. Your task is to extract ONLY real news articles from the provided web page content.

For each news article you find, extract:
1. **title**: The headline or title of the news article (required)
2. **description**: A brief summary or the first few sentences of the article (if available)
3. **publication_date**: The publication date in YYYY-MM-DD format if found (or empty string if not found)

**Important instructions:**
- Extract ONLY actual news articles with full content, NOT navigation menus or section headers
- SKIP short menu items, category names, and navigation links
- Focus on articles that have substantial description or content
- If a title appears to be just a menu item or section name, DO NOT include it
- If a field is not available, use an empty string ""
- Return ONLY valid JSON, no other text
- The response must be a JSON array of objects
- Each object must have: title, description, publication_date

**Example output format:**
```json
[
  {
    "title": "First News Article Title",
    "description": "Brief description or first sentences of the article",
    "publication_date": "2025-10-07"
  },
  {
    "title": "Second News Article Title",
    "description": "Another article description",
    "publication_date": ""
  }
]
```"""

        user_prompt = f"""Extract ALL news articles from this webpage: {url}

IMPORTANT: There may be 10-30 or more news articles on this page. Extract EVERY SINGLE ONE you can find.
Do not stop after finding just a few articles - continue scanning the entire content.

Web page content:
{cleaned_html}

Return ALL the news articles as a JSON array following the format specified. Remember to include ALL articles, not just the first few."""

        return json.dumps({
            "system": system_prompt,
            "user": user_prompt
        })

    def _call_llm_api(self, prompt: str, attempt: int) -> Dict[str, Any]:
        """Call OpenRouter LLM API.

        Args:
            prompt: JSON string with system and user prompts
            attempt: Current attempt number

        Returns:
            API response data

        Raises:
            RuntimeError: If API call fails
        """
        logger.debug(f"Calling OpenRouter API (attempt {attempt})")

        prompt_data = json.loads(prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/smart-news-aggregator",
            "X-Title": "Smart News Aggregator"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": prompt_data["system"]
                },
                {
                    "role": "user",
                    "content": prompt_data["user"]
                }
            ],
            "temperature": 0.1,  # Low temperature for more consistent extraction
            "max_tokens": 4000
        }

        try:
            logger.debug(f"Sending request to {self.api_url}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            logger.debug(f"API response status: {response.status_code}")

            # Handle different status codes
            if response.status_code == 401:
                raise RuntimeError("Authentication failed - invalid API key")
            elif response.status_code == 429:
                raise RuntimeError("Rate limit exceeded - too many requests")
            elif response.status_code >= 500:
                raise RuntimeError(f"Server error: {response.status_code}")
            elif response.status_code != 200:
                error_detail = response.text[:200] if response.text else "No error details"
                raise RuntimeError(f"API request failed with status {response.status_code}: {error_detail}")

            response_data = response.json()

            # Validate response structure
            if not self._validate_response(response_data):
                raise RuntimeError("Invalid API response structure")

            return response_data

        except requests.exceptions.Timeout:
            raise RuntimeError(f"API request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Failed to connect to OpenRouter API")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request error: {str(e)}")
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse API response as JSON")

    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate LLM API response format.

        Args:
            response: API response dictionary

        Returns:
            True if response is valid, False otherwise
        """
        try:
            if not isinstance(response, dict):
                logger.error("Response is not a dictionary")
                return False

            if "choices" not in response:
                logger.error("Response missing 'choices' field")
                return False

            if not response["choices"] or len(response["choices"]) == 0:
                logger.error("Response has empty 'choices' array")
                return False

            first_choice = response["choices"][0]
            if "message" not in first_choice:
                logger.error("First choice missing 'message' field")
                return False

            if "content" not in first_choice["message"]:
                logger.error("Message missing 'content' field")
                return False

            logger.debug("Response validation successful")
            return True

        except Exception as e:
            logger.error(f"Response validation error: {str(e)}")
            return False

    def _parse_llm_response(self, response_data: Dict[str, Any]) -> List[NewsItem]:
        """Parse LLM response and extract news items.

        Args:
            response_data: API response data

        Returns:
            List of NewsItem objects

        Raises:
            RuntimeError: If parsing fails
        """
        try:
            # Extract content from response
            content = response_data["choices"][0]["message"]["content"]
            logger.debug(f"LLM response content length: {len(content)} chars")

            # Try to extract JSON from the content
            # Sometimes LLM returns markdown code blocks
            json_str = content.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                # Find the actual JSON content
                lines = json_str.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or not line.strip().startswith("```"):
                        json_lines.append(line)
                json_str = "\n".join(json_lines).strip()

            # Parse JSON - with better error handling
            try:
                news_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                logger.debug(f"Problematic JSON (first 1000 chars): {json_str[:1000]}")

                # Try to extract JSON array using regex as fallback
                import re
                json_array_pattern = r'\[\s*\{.*?\}\s*\]'
                matches = re.findall(json_array_pattern, json_str, re.DOTALL)
                if matches:
                    logger.info("Attempting to extract JSON array using regex fallback")
                    try:
                        news_data = json.loads(matches[0])
                    except json.JSONDecodeError:
                        raise RuntimeError(f"Could not parse LLM response as valid JSON: {str(e)}")
                else:
                    raise RuntimeError(f"Could not parse LLM response as valid JSON: {str(e)}")

            if not isinstance(news_data, list):
                logger.warning("LLM returned non-list response, attempting to extract array")
                # Try to find array in response
                if isinstance(news_data, dict) and "news" in news_data:
                    news_data = news_data["news"]
                elif isinstance(news_data, dict) and "articles" in news_data:
                    news_data = news_data["articles"]
                else:
                    raise RuntimeError("Expected array of news items")

            # Convert to NewsItem objects
            news_items = []
            for item in news_data:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item: {item}")
                    continue

                # Validate required field
                if "title" not in item or not item["title"]:
                    logger.warning(f"Skipping item without title: {item}")
                    continue

                news_item = NewsItem(
                    title=str(item.get("title", "")).strip(),
                    description=str(item.get("description", "")).strip(),
                    publication_date=str(item.get("publication_date", "")).strip()
                )

                # Skip if title is empty after stripping
                if not news_item.title:
                    continue

                news_items.append(news_item)
                logger.debug(f"Extracted: {news_item.title[:50]}...")

            if not news_items:
                logger.warning("No valid news items extracted from LLM response")

            return news_items

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.debug(f"Content: {content[:500]}...")
            raise RuntimeError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            raise RuntimeError(f"Error parsing LLM response: {str(e)}")
