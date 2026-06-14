import re

# Swales CARS Model Lexical Indicators
MOVE1_INDICATORS = [
    r"\b(recent years|recently)\b",
    r"\b(widely used|widely recognized)\b",
    r"\b(has become|is becoming)\b",
    r"\b(important|crucial|essential)\b",
    r"\b(increasing interest|growing attention)\b",
    r"\b(play(s)? an? important role)\b",
    r"\b(is well known)\b",
    r"\b(background)\b",
    r"\b(context)\b"
]

MOVE2_INDICATORS = [
    r"\b(however|nevertheless|yet)\b",
    r"\b(little attention|few studies|little research)\b",
    r"\b(remains unclear|remains unknown)\b",
    r"\b(not well understood)\b",
    r"\b(lack(s)? of)\b",
    r"\b(gap|limitation|shortcoming)\b",
    r"\b(although|despite)\b",
    r"\b(challenges?)\b",
    r"\b(fail(s)? to)\b"
]

MOVE3_INDICATORS = [
    r"\b(this study aims|aims to|objective of this)\b",
    r"\b(we propose|we present|proposes)\b",
    r"\b(this paper focuses)\b",
    r"\b(in this study|in this paper)\b",
    r"\b(we investigate|investigated)\b",
    r"\b(we use|we applied|method|approach)\b",
    r"\b(results show|findings indicate)\b",
    r"\b(demonstrate|reveal)\b",
    r"\b(conclude|conclusion)\b",
    r"\b(outperform)\b"
]

HEDGING_WORDS = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bsuggests?\b",
    r"\bpossibly\b", r"\blikely\b", r"\bperhaps\b", r"\bprobably\b",
    r"\btends? to\b", r"\bappears? to\b", r"\barguably\b",
    r"\brelatively\b", r"\bseems? to\b", r"\bwe believe\b",
    r"\bpotential\b", r"\bindicates?\b"
]

def compile_regex_list(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]

MOVE1_REGEX = compile_regex_list(MOVE1_INDICATORS)
MOVE2_REGEX = compile_regex_list(MOVE2_INDICATORS)
MOVE3_REGEX = compile_regex_list(MOVE3_INDICATORS)
HEDGING_REGEX = compile_regex_list(HEDGING_WORDS)

def detect_move(sentence: str, sentence_idx: int = -1, total_sentences: int = -1) -> dict:
    """
    Classifies a sentence into Swales' CARS Moves using a hybrid scoring system.
    Returns a dict with 'move', 'confidence', and 'interpretation'.
    """
    rel_pos = -1.0
    if sentence_idx >= 0 and total_sentences > 0:
        rel_pos = sentence_idx / total_sentences
        
    scores = {"Move 1: Territory": 0.0, "Move 2: Gap": 0.0, "Move 3: Niche": 0.0}
    
    # Lexical Matches
    for pattern in MOVE1_REGEX:
        if pattern.search(sentence): scores["Move 1: Territory"] += 1.0
    for pattern in MOVE2_REGEX:
        if pattern.search(sentence): scores["Move 2: Gap"] += 1.5 # Gap words are strong indicators
    for pattern in MOVE3_REGEX:
        if pattern.search(sentence): scores["Move 3: Niche"] += 1.0
            
    # Positional Heuristics
    if rel_pos != -1.0:
        if rel_pos < 0.25:
            scores["Move 1: Territory"] += 0.5
        elif 0.25 <= rel_pos < 0.5:
            scores["Move 2: Gap"] += 0.3
        elif rel_pos >= 0.5:
            scores["Move 3: Niche"] += 0.6
            
    # Discourse Markers Boost
    if re.search(r"^(however|nevertheless|yet)\b", sentence, re.IGNORECASE):
        scores["Move 2: Gap"] += 2.0
    if re.search(r"^(in this|this study|we)\b", sentence, re.IGNORECASE):
        scores["Move 3: Niche"] += 1.5

    best_move = max(scores.items(), key=lambda x: x[1])
    
    # Calculate confidence (normalize score)
    confidence = min(round(best_move[1] / 3.0, 2), 1.0)
    
    if best_move[1] < 0.5:
        return {
            "move": "Other", 
            "confidence": 0.0, 
            "interpretation": "Sentence does not strongly map to CARS moves."
        }
        
    # Generate Interpretations
    interp = ""
    if best_move[0] == "Move 1: Territory":
        interp = "Establishes research background or significance."
    elif best_move[0] == "Move 2: Gap":
        interp = "Identifies a limitation, gap, or challenge in current knowledge."
    elif best_move[0] == "Move 3: Niche":
        interp = "Occupies the niche by stating aims, methods, or results."

    return {
        "move": best_move[0],
        "confidence": confidence,
        "interpretation": interp
    }

def detect_hedging(sentence: str) -> dict:
    """Detects uncertainty words in a sentence. Returns count and matched words."""
    hedging_words_found = []
    for i, pattern in enumerate(HEDGING_REGEX):
        if pattern.search(sentence):
            word = HEDGING_WORDS[i].replace(r"\b", "").replace(r"\b", "")
            hedging_words_found.append(word.replace("?", ""))
    
    return {
        "count": len(hedging_words_found),
        "words": hedging_words_found
    }
