import json

from src.llm import openrouter_client as oc


class DummyResp:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("http error")

    def json(self):
        return self._data


class DummySession:
    def __init__(self, models):
        self.models = models
        self.post_calls = 0

    def get(self, url, headers=None, timeout=10):
        if url.endswith("/models"):
            data = {
                "data": [
                    {"id": m, "pricing": {"prompt": 0, "completion": 0}}
                    for m in self.models
                ]
            }
            return DummyResp(data)
        return DummyResp({}, 404)

    def post(self, url, headers=None, json=None, timeout=30):
        self.post_calls += 1
        # Return a valid OpenRouter-ish completion payload
        completion = {
            "choices": [
                {
                    "message": {
                        "content": json_dumps(
                            [
                                {
                                    "title": "A",
                                    "description": "B",
                                    "publication_date": None,
                                }
                            ]
                        )
                    }
                }
            ]
        }
        return DummyResp(completion)


def json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False)


def test_discover_free_models_uses_list():
    session = DummySession(["meta-llama/llama-3.1-8b-instruct:free"])
    free = oc.discover_free_models(session)
    assert any("llama" in m for m in free)


def test_extract_news_from_html_with_dummy_session():
    session = DummySession(["meta-llama/llama-3.1-8b-instruct:free"])
    items = oc.extract_news_from_html("<html>hello</html>", session=session)
    assert len(items) == 1
    assert items[0].title == "A"
    assert items[0].description == "B"
