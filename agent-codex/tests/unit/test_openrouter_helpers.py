from src.llm.openrouter_client import _truncate_html, _build_prompt, _extract_json_block


def test_truncate_html_keeps_edges():
    s = "a" * 1000
    html = s + "MIDDLE" + s
    t = _truncate_html(html, max_chars=100)
    assert "MIDDLE" not in t
    assert len(t) <= 120
    assert "truncated" in t


def test_build_prompt_structure():
    msgs = _build_prompt("<html>text</html>")
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_extract_json_block_picks_array():
    s = 'prefix [ {"title": "T", "description": "D"} ] suffix'
    b = _extract_json_block(s)
    assert b.strip().startswith("[")
