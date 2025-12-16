import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path to allow direct execution
if __name__ == "__main__":
    # When running directly, add week2 to path
    week2_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(week2_dir.parent))
    from week2.app.services.extract import extract_action_items, extract_action_items_llm
else:
    # When running with pytest, use relative imports
    from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# Tests for extract_action_items_llm()
def test_extract_action_items_llm_empty_input():
    """Test that empty input returns empty list."""
    assert extract_action_items_llm("") == []
    assert extract_action_items_llm("   ") == []
    assert extract_action_items_llm("\n\n") == []


def test_extract_action_items_llm_bullet_lists():
    """Test extraction from bullet lists."""
    text = """
    Meeting notes:
    - Fix the bug in login system
    * Review the PR from John
    • Update documentation
    """.strip()
    
    items = extract_action_items_llm(text)
    assert len(items) > 0
    # Check that action items are extracted (flexible matching)
    item_text = " ".join(items).lower()
    assert "bug" in item_text or "login" in item_text
    assert "review" in item_text or "pr" in item_text
    assert "documentation" in item_text or "update" in item_text


def test_extract_action_items_llm_keyword_prefixed():
    """Test extraction from keyword-prefixed lines."""
    text = """
    TODO: Implement user authentication
    action: Set up database connection
    next: Write unit tests
    """.strip()
    
    items = extract_action_items_llm(text)
    assert len(items) > 0
    item_text = " ".join(items).lower()
    assert "authentication" in item_text or "user" in item_text
    assert "database" in item_text or "connection" in item_text
    assert "test" in item_text or "unit" in item_text


def test_extract_action_items_llm_future_vs_past():
    """Test that only future actions are extracted, not past actions."""
    text = """
    Today I went to Costco and brought some milk. 
    Then I saw a guy buying flowers for his gf. 
    I felt so ashamed. 
    I planning to buy a lambonigi at Stevens Creek and buy flowers. 
    I will put flowers in the trunk to surprise my mom.
    """.strip()
    
    items = extract_action_items_llm(text)
    assert len(items) > 0
    
    # Should NOT extract past actions
    item_text = " ".join(items).lower()
    assert "milk" not in item_text  # Past action: "brought some milk"
    
    # Should extract future actions
    assert "lambonigi" in item_text or "stevens" in item_text or "creek" in item_text
    assert "flowers" in item_text
    assert "trunk" in item_text or "surprise" in item_text or "mom" in item_text


def test_extract_action_items_llm_implicit_tasks():
    """Test extraction of implicit tasks from narrative text."""
    text = """
    We need to refactor the authentication module. 
    The team decided we should implement caching for better performance.
    It's important that we document the API endpoints.
    """.strip()
    
    items = extract_action_items_llm(text)
    assert len(items) > 0
    item_text = " ".join(items).lower()
    assert "refactor" in item_text or "authentication" in item_text
    assert "caching" in item_text or "performance" in item_text or "implement" in item_text
    assert "document" in item_text or "api" in item_text or "endpoint" in item_text


def test_extract_action_items_llm_mixed_format():
    """Test extraction from mixed format text."""
    text = """
    Action items from sprint planning:
    - [ ] Fix critical bug in payment system
    TODO: Add error handling
    We need to update the user interface.
    Next: Review code changes
    I will deploy to production next week.
    """.strip()
    
    items = extract_action_items_llm(text)
    assert len(items) > 0
    item_text = " ".join(items).lower()
    assert "bug" in item_text or "payment" in item_text or "fix" in item_text
    assert "error" in item_text or "handling" in item_text
    assert "interface" in item_text or "user" in item_text or "update" in item_text
    assert "review" in item_text or "code" in item_text or "change" in item_text
    assert "deploy" in item_text or "production" in item_text


def test_extract_action_items_llm_no_action_items():
    """Test text with no action items returns empty or minimal results."""
    text = """
    Today was a beautiful day. 
    The weather was perfect for a walk in the park.
    I enjoyed reading a book and drinking coffee.
    """.strip()
    
    items = extract_action_items_llm(text)
    # Should return empty or very few items since there are no actionable tasks
    assert len(items) <= 1  # Allow for some false positives from LLM


def test_extract_action_items_llm_commitments():
    """Test extraction of commitments and promises."""
    text = """
    I promise to finish the report by Friday.
    We committed to delivering the feature next sprint.
    I will make sure to test everything thoroughly.
    """.strip()
    
    items = extract_action_items_llm(text)
    assert len(items) > 0
    item_text = " ".join(items).lower()
    assert "report" in item_text or "friday" in item_text or "finish" in item_text
    assert "feature" in item_text or "sprint" in item_text or "deliver" in item_text
    assert "test" in item_text or "thoroughly" in item_text


if __name__ == "__main__":
    # Allow direct execution with pytest
    pytest.main([__file__, "-v"])
