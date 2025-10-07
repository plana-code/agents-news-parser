from src.utils.common import slugify, first_json


def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  русский текст  ") == "export"  # non-ascii removed, fallback name


def test_first_json_extracts():
    text = 'prefix {"a": 1} suffix'
    assert first_json(text) == {"a": 1}
