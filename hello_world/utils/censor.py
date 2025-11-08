import re
from better_profanity import profanity

# load default English words
profanity.load_censor_words()

# Add some Romanian words (extend this list as needed)
ROMANIAN_BADWORDS = {
    "pula",
    "pizda",
    "dracu",
    "dracu'",  # variants if you want
    "futu-te",
    "futute",
}
ROMANIAN_BADWORDS = {w.lower() for w in ROMANIAN_BADWORDS}


# Optionally let better_profanity also know about the Romanian words
profanity.add_censor_words(list(ROMANIAN_BADWORDS))

PLACEHOLDER = "<Porfanity>"


def censor_en_ro(text: str) -> str:
    """
    Replace English + Romanian profanity with <Porfanity>, ignoring case.
    """
    # Split, but keep whitespace as separate tokens so we can join back perfectly
    tokens = re.split(r'(\s+)', text)

    censored_tokens = []
    for tok in tokens:
        if not tok or tok.isspace():
            censored_tokens.append(tok)
            continue

        # Strip leading/trailing punctuation to find the "core" word
        leading = re.match(r'^\W*', tok).group(0)
        trailing = re.match(r'.*?(\W*)$', tok).group(1)
        core = tok[len(leading):len(tok) - len(trailing)] or tok

        core_lower = core.lower()

        is_profane = (
            profanity.contains_profanity(core_lower)  # English, case-insensitive
            or core_lower in ROMANIAN_BADWORDS        # Romanian, case-insensitive
        )

        if is_profane:
            censored_tokens.append(leading + PLACEHOLDER + trailing)
        else:
            censored_tokens.append(tok)

    return "".join(censored_tokens)
    

if __name__ == "__main__":
    text_en = "What the hell is going on?"
    print(censor_en_ro(text_en))
    # e.g. "What the <Porfanity> is going on?"

    text_ro = "Bagami-as pula in traficul asta."
    print(censor_en_ro(text_ro))
    
    text = "Pula ica spatarul"
    print(censor_en_ro(text))
    # "Bagami-as <Porfanity> in traficul asta."