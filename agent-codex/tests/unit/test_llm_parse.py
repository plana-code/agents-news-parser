from src.llm.openrouter_client import _extract_json_block


def test_extract_json_block_array():
    text = 'Some preface... [ {"title": "A", "description": "B"} ] ... post'
    block = _extract_json_block(text)
    assert block.strip().startswith("[") and block.strip().endswith("]")
