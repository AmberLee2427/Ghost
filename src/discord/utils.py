# utils.py
import datetime
import re
import json

def log_message(bot_name, message_text):
    """A simple logger to print messages with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {bot_name} - {message_text}")

def check_keyword_trigger(content, triggers):
    """
    Checks for trigger words, ignoring them if they are preceded by '!'.
    """
    content_lower = content.lower()
    for trigger in triggers:
        start_index = 0
        while True:
            index = content_lower.find(trigger, start_index)
            if index == -1:
                break  # Trigger not found in the rest of the string.

            if index > 0 and content_lower[index - 1] == '!':
                # This is an escaped trigger. Continue searching from after this point.
                start_index = index + len(trigger)
                continue
            else:
                # A valid, un-escaped trigger was found.
                return True
    return False

def parse_llm_response_robustly(raw_response, logger=None):
    """
    Attempts to parse the LLM's raw response, handling potential formatting issues
    like Markdown code blocks. If JSON parsing fails, it falls back to
    treating the entire raw_response as the 'response_to_user'.

    Returns a dictionary with 'response_to_user' and 'reasoning'.
    """
    original_response_for_fallback = raw_response # Keep original for fallback

    # 1. Try to extract JSON from a Markdown code block
    json_match = re.search(r"```json\n(.*)```", raw_response, re.DOTALL)
    if json_match:
        extracted_json_string = json_match.group(1).strip()
        if logger:
            logger(f"DEBUG: Extracted JSON from markdown block. Attempting to parse: '{extracted_json_string}'")
    else:
        # If no markdown block, assume the raw_response itself is the JSON string
        extracted_json_string = raw_response.strip()
        if logger:
            logger(f"DEBUG: No markdown block found. Attempting to parse raw response as JSON: '{extracted_json_string}'")

    # 2. Attempt to parse as JSON
    try:
        data = json.loads(extracted_json_string)
        response_to_user = data.get('response_to_user')
        reasoning = data.get('reasoning', 'No reasoning provided by LLM.')

        if response_to_user is None:
            if logger:
                logger(f"WARNING: JSON parsed but 'response_to_user' key missing or None. Data: {data}")
            # Fallback to plain text if response_to_user is explicitly missing/None
            return {
                'response_to_user': original_response_for_fallback.strip(),
                'reasoning': 'JSON parsed but response_to_user key was missing.'
            }

        return {
            'response_to_user': response_to_user,
            'reasoning': reasoning
        }
    except json.JSONDecodeError as e:
        if logger:
            logger(f"WARNING: Failed to parse as JSON: {e}. Attempted to parse: '{extracted_json_string}'. Falling back to plain text.")
        # Fallback to plain text if JSON parsing fails
        return {
            'response_to_user': original_response_for_fallback.strip(),
            'reasoning': 'LLM response was not valid JSON.'
        }
    except KeyError as e:
        if logger:
            logger(f"WARNING: KeyError during JSON parsing: {e}. Falling back to plain text. Data: {data if 'data' in locals() else 'N/A'}")
        # Fallback to plain text if a KeyError occurs (e.g., trying to access mandatory key without .get())
        return {
            'response_to_user': original_response_for_fallback.strip(),
            'reasoning': 'Key error in LLM JSON response.'
        }