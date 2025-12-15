from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from dotenv import load_dotenv

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def extract_action_items_llm(text: str) -> List[str]:
    """
    Extract action items from text using LLM semantic understanding.
    
    This function uses Ollama to identify action items based on their semantic meaning,
    rather than relying on hard-coded patterns. It understands tasks, todos, and
    actionable items regardless of formatting.
    
    Args:
        text: The input text to extract action items from.
        
    Returns:
        A list of extracted action items as strings.
    """
    if not text or not text.strip():
        return []
    
    # Define JSON schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "action_items": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of action items extracted from the text"
            }
        },
        "required": ["action_items"]
    }
    
    system_prompt = """You are an expert at identifying FUTURE action items and tasks from text.
An action item is a task, todo, or actionable item that needs to be done in the FUTURE.

CRITICAL RULES:
1. ONLY extract FUTURE actions - things that still need to be done
2. DO NOT extract PAST actions - things that have already been completed
3. Pay attention to verb tenses:
   - Past tense (went, bought, brought, saw) = ALREADY DONE, do NOT extract
   - Future tense (will, planning to, going to, need to) = TO BE DONE, extract these
   - Present tense plans/intentions (I planning to, I will) = TO BE DONE, extract these
4. Extract explicit future plans, intentions, and commitments
5. Extract implicit future tasks inferred from context (e.g., "I planning to buy X" means extract "Buy X")

Examples:
- "I went to the store and bought milk" → NO action item (past, already done)
- "I will buy flowers" → Extract "Buy flowers" (future action)
- "I planning to buy a lambonigi" → Extract "Buy a lambonigi" (future plan)
- "I will put flowers in the trunk" → Extract "Put flowers in the trunk" (future action)

Return them as a JSON object with an "action_items" array of strings.
Each action item should be a clear, concise description of what needs to be done in the future."""
    
    user_prompt = f"""Extract all FUTURE action items from the following text.
IMPORTANT: Only extract actions that still need to be done. Do NOT extract actions that have already been completed (past tense).

Text:
{text}

Return a JSON object with an "action_items" array containing all FUTURE action items that need to be done.
Exclude any actions that are described in past tense (already completed)."""
    
    response = None
    try:
        # Use a small model for efficiency - try common model names
        # Users can set OLLAMA_MODEL env var to override, otherwise try common models
        model_name = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        # Use a small model for efficiency (llama3.1:8b is commonly available)
        # Users should pull the model first: ollama pull llama3.1:8b
        response = chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            format=json_schema,
            options={"temperature": 0.3},  # Lower temperature for more consistent extraction
        )
        
        # Parse the JSON response
        if not response or not response.message or not response.message.content:
            return []
        
        content = response.message.content.strip()
        print(f"Raw response: {content}")
        
        # Handle cases where the model wraps JSON in code fences
        if content.startswith("```"):
            # Extract JSON from code fence
            lines = content.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```json") or (line.strip() == "```" and not in_json):
                    in_json = True
                    continue
                if line.strip() == "```" and in_json:
                    break
                if in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)
        
        # Parse JSON
        result = json.loads(content)
        action_items = result.get("action_items", [])
        
        # Validate and clean the results
        if not isinstance(action_items, list):
            return []
        
        # Filter out empty strings and normalize
        cleaned_items = []
        for item in action_items:
            if isinstance(item, str) and item.strip():
                cleaned_items.append(item.strip())
        
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_items: List[str] = []
        for item in cleaned_items:
            lowered = item.lower()
            if lowered not in seen:
                seen.add(lowered)
                unique_items.append(item)
        
        return unique_items
        
    except json.JSONDecodeError as e:
        # Fallback: try to extract action items from raw response
        print(f"Failed to parse JSON response: {e}")
        raw_content = response.message.content if response and response.message and response.message.content else "No response"
        print(f"Raw response: {raw_content}")
        return []
    except Exception as e:
        # Graceful error handling - return empty list on any error
        print(f"Error in LLM extraction: {e}")
        return []