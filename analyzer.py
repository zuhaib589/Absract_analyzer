import re

AIM_INDICATORS = [
    r"this study aims",
    r"we propose",
    r"this paper focuses",
    r"our objective",
    r"the aim of",
    r"purpose of this",
    r"we present",
    r"this research aims"
]

METHOD_INDICATORS = [
    r"we used",
    r"we applied",
    r"data was collected",
    r"method",
    r"methodology",
    r"we conducted",
    r"was performed",
    r"experiments were"
]

RESULT_INDICATORS = [
    r"results show",
    r"we found",
    r"the study reveals",
    r"significant improvement",
    r"demonstrates",
    r"results indicate",
    r"our findings"
]

HEDGING_WORDS = [
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bsuggests\b",
    r"\bpossibly\b",
    r"\blikely\b",
    r"\bperhaps\b",
    r"\bprobably\b"
]

def compile_regex_list(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]

AIM_REGEX = compile_regex_list(AIM_INDICATORS)
METHOD_REGEX = compile_regex_list(METHOD_INDICATORS)
RESULT_REGEX = compile_regex_list(RESULT_INDICATORS)
HEDGING_REGEX = compile_regex_list(HEDGING_WORDS)

def detect_move(sentence: str) -> str:
    """Classifies a sentence into Aim, Method, Result, or Other."""
    for pattern in AIM_REGEX:
        if pattern.search(sentence):
            return "Aim"
            
    for pattern in METHOD_REGEX:
        if pattern.search(sentence):
            return "Method"
            
    for pattern in RESULT_REGEX:
        if pattern.search(sentence):
            return "Result"
            
    return "Other"

def detect_hedging(sentence: str) -> list[str]:
    """Detects uncertainty words in a sentence."""
    hedging_words_found = []
    for i, pattern in enumerate(HEDGING_REGEX):
        if pattern.search(sentence):
            # Extract the actual word without word boundaries
            word = HEDGING_WORDS[i].replace(r"\b", "")
            hedging_words_found.append(word)
    return hedging_words_found
