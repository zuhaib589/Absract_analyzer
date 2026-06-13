import re

def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using simple punctuation rules.
    """
    # Simple regex to split by ., !, or ? followed by whitespace or end of string
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out any empty strings
    return [s for s in sentences if s]
