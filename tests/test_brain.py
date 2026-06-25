import sys
from render_studio import brain

def test_build_prompt_mentions_knobs_and_text():
    p = brain.build_prompt("brushed aluminium on dark")
    assert "brushed aluminium on dark" in p
    assert "material" in p and "background" in p

def test_parse_knobs_extracts_json_from_prose():
    raw = 'Sure!\n{"material": "metal", "background": "dark"}\nHope that helps'
    assert brain.parse_knobs(raw) == {"material": "metal", "background": "dark"}

def test_nl_to_knobs_with_injected_cmd():
    fake = [sys.executable, "-c", 'print("{\\"material\\": \\"metal\\"}")']
    assert brain.nl_to_knobs("anything", claude_cmd=fake) == {"material": "metal"}

def test_nl_to_knobs_missing_binary_returns_empty():
    # I1: nonexistent binary must not raise; should return {}
    result = brain.nl_to_knobs("anything", claude_cmd=["/nonexistent-binary-xyz-123"])
    assert result == {}
