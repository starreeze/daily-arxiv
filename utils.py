def find_first_json_block(text: str) -> tuple[str, str]:
    """Find the first complete JSON block in the text.

    Args:
        text (str): Input text containing JSON block(s)

    Returns:
        tuple[str, str]: (matched JSON block, remaining text)

    Raises:
        ValueError: If no valid JSON block is found or text is malformed
    """
    stack = []
    start = -1

    for i, char in enumerate(text):
        if char in "[{":
            if not stack:  # First opening bracket
                start = i
            stack.append(char)
        elif char in "]}":
            if not stack:
                raise ValueError("Unmatched closing bracket")

            # Check if brackets match
            if (char == "]" and stack[-1] == "[") or (char == "}" and stack[-1] == "{"):
                stack.pop()
                if not stack:  # Found complete block
                    return text[start : i + 1], text[i + 1 :]
            else:
                raise ValueError("Mismatched brackets")

    if stack:
        raise ValueError("Unclosed brackets")
    raise ValueError("No JSON block found")
