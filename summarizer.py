import re
from collections import Counter
from difflib import SequenceMatcher


# ======================================================
# COMMON WORDS TO IGNORE
# ======================================================

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but",
    "is", "are", "was", "were", "be", "been",
    "being", "to", "of", "in", "on", "at",
    "for", "from", "with", "by", "as",
    "it", "its", "this", "that", "these",
    "those", "they", "them", "their",
    "he", "she", "we", "you", "your",
    "i", "me", "my", "our", "us",
    "has", "have", "had", "do", "does",
    "did", "can", "could", "would", "should",
    "may", "might", "will", "shall",
    "not", "no", "so", "if", "then",
    "than", "into", "through", "about",
    "because", "while", "when", "where",
    "which", "who", "what", "how"
}


# ======================================================
# WEBSITE JUNK TO REMOVE
# ======================================================

JUNK_PHRASES = [
    "official websites use .gov",
    "secure .gov websites use https",
    "privacy policy",
    "cookie policy",
    "accept cookies",
    "terms of use",
    "all rights reserved",
    "sign up",
    "subscribe",
    "newsletter",
    "advertisement",
    "skip to main content",
    "share sensitive information",
    "this website uses cookies",
    "enable javascript"
]


# ======================================================
# CLEAN A SENTENCE
# ======================================================

def clean_sentence(sentence):

    # Remove citation numbers:
    # [1], [ 10 ], [25]
    sentence = re.sub(
        r"\[\s*\d+\s*\]",
        "",
        sentence
    )

    # Remove [citation needed]
    sentence = re.sub(
        r"\[\s*citation needed\s*\]",
        "",
        sentence,
        flags=re.IGNORECASE
    )

    # Remove some unnecessary opening phrases
    sentence = re.sub(
        r"^(in conclusion|overall|therefore|thus),?\s*",
        "",
        sentence,
        flags=re.IGNORECASE
    )

    # Remove repeated spaces
    sentence = re.sub(
        r"\s+",
        " ",
        sentence
    ).strip()

    return sentence


# ======================================================
# GET WORDS
# ======================================================

def get_words(text):

    return re.findall(
        r"[A-Za-z][A-Za-z'-]*",
        text.lower()
    )


# ======================================================
# IMPORTANT WORDS ONLY
# ======================================================

def important_words(text):

    words = get_words(text)

    return [
        word
        for word in words
        if (
            word not in STOP_WORDS
            and len(word) > 2
        )
    ]


# ======================================================
# SPLIT TEXT INTO SENTENCES
# ======================================================

def split_sentences(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return re.split(
        r"(?<=[.!?])\s+",
        text
    )


# ======================================================
# SPLIT LONG SENTENCES
# ======================================================

def split_long_sentence(sentence):

    words = get_words(sentence)

    # If already short enough, keep it
    if len(words) <= 28:
        return [sentence]


    # Try splitting at commas, semicolons,
    # or some connecting words
    parts = re.split(
        r",\s+|;\s+|\s+and\s+|\s+but\s+|\s+while\s+",
        sentence
    )


    results = []


    for part in parts:

        part = clean_sentence(part)

        word_count = len(
            get_words(part)
        )


        if 7 <= word_count <= 28:

            if not part.endswith(
                (".", "!", "?")
            ):
                part += "."

            results.append(part)


    # If splitting failed, return original sentence
    if not results:
        return [sentence]


    return results


# ======================================================
# CHECK WHETHER SENTENCE IS USEFUL
# ======================================================

def is_useful_sentence(sentence):

    sentence_lower = sentence.lower()

    words = get_words(sentence)

    word_count = len(words)


    # Too short
    if word_count < 7:
        return False


    # Too long
    if word_count > 32:
        return False


    # Remove website navigation/junk text
    for phrase in JUNK_PHRASES:

        if phrase in sentence_lower:
            return False


    return True


# ======================================================
# SENTENCE SIMILARITY
# ======================================================

def sentence_similarity(sentence1, sentence2):

    words1 = set(
        important_words(sentence1)
    )

    words2 = set(
        important_words(sentence2)
    )


    if not words1 or not words2:
        return 0


    shared = words1 & words2

    union = words1 | words2


    # Jaccard similarity
    jaccard = (
        len(shared)
        /
        len(union)
    )


    # How much of the smaller sentence is repeated
    overlap = (
        len(shared)
        /
        min(
            len(words1),
            len(words2)
        )
    )


    # Compare sentence structure
    sequence = SequenceMatcher(
        None,
        sentence1.lower(),
        sentence2.lower()
    ).ratio()


    return max(
        jaccard,
        overlap,
        sequence
    )


# ======================================================
# MAIN SUMMARIZER
# ======================================================

def summarize_research(
    research_results,
    question="",
    max_sentences=3
):

    candidates = []

    seen_sentences = set()


    # ==================================================
    # COLLECT SENTENCES FROM ALL WEBSITES
    # ==================================================

    for source_number, result in enumerate(
        research_results
    ):

        text = result.get(
            "text",
            ""
        )


        sentences = split_sentences(
            text
        )


        for original_sentence in sentences:

            smaller_sentences = split_long_sentence(
                original_sentence
            )


            for sentence in smaller_sentences:

                sentence = clean_sentence(
                    sentence
                )


                if not is_useful_sentence(
                    sentence
                ):
                    continue


                normalized = re.sub(
                    r"[^a-z0-9 ]",
                    "",
                    sentence.lower()
                )


                normalized = re.sub(
                    r"\s+",
                    " ",
                    normalized
                ).strip()


                if normalized in seen_sentences:
                    continue


                seen_sentences.add(
                    normalized
                )


                candidates.append(
                    {
                        "sentence": sentence,
                        "source": source_number
                    }
                )


    # If nothing useful was found
    if not candidates:

        return (
            "Not enough useful information "
            "was found."
        )


    # ==================================================
    # COUNT IMPORTANT WORD FREQUENCIES
    # ==================================================

    all_words = []


    for candidate in candidates:

        all_words.extend(
            important_words(
                candidate["sentence"]
            )
        )


    frequencies = Counter(
        all_words
    )


    # ==================================================
    # QUESTION WORDS
    # ==================================================

    question_words = set(
        important_words(question)
    )


    # ==================================================
    # SCORE EACH SENTENCE
    # ==================================================

    for candidate in candidates:

        sentence = candidate[
            "sentence"
        ]


        words = important_words(
            sentence
        )


        word_set = set(words)


        score = 0


        # --------------------------------------------------
        # GENERAL IMPORTANCE
        # --------------------------------------------------

        if words:

            score += (
                sum(
                    frequencies[word]
                    for word in words
                )
                /
                len(words)
            )


        # --------------------------------------------------
        # QUESTION RELEVANCE
        # --------------------------------------------------

        matching_question_words = (
            question_words
            &
            word_set
        )


        # Strong bonus for words
        # that appear in the user's question
        score += (
            len(
                matching_question_words
            )
            * 35
        )


        # Bonus for covering more of the question
        if question_words:

            coverage = (
                len(
                    matching_question_words
                )
                /
                len(
                    question_words
                )
            )

            score += (
                coverage
                * 50
            )


        # --------------------------------------------------
        # PREFERRED SENTENCE LENGTH
        # --------------------------------------------------

        word_count = len(
            get_words(sentence)
        )


        if 10 <= word_count <= 22:

            score += 20


        elif 23 <= word_count <= 26:

            score += 10


        elif word_count > 28:

            score -= 15


        # --------------------------------------------------
        # PENALTY FOR OFF-TOPIC SENTENCES
        # --------------------------------------------------

        if (
            question_words
            and
            len(
                matching_question_words
            ) == 0
        ):

            score -= 20


        candidate["score"] = score


    # ==================================================
    # RANK SENTENCES
    # ==================================================

    ranked = sorted(

        candidates,

        key=lambda item:
        item["score"],

        reverse=True
    )


    # ==================================================
    # SELECT UP TO 3 DIFFERENT IDEAS
    # ==================================================

    selected = []


    for candidate in ranked:

        duplicate_idea = False


        for chosen in selected:

            similarity = sentence_similarity(
                candidate["sentence"],
                chosen["sentence"]
            )


            # Skip sentences that repeat
            # nearly the same idea
            if similarity > 0.50:

                duplicate_idea = True

                break


        if not duplicate_idea:

            selected.append(
                candidate
            )


        if len(selected) >= max_sentences:
            break


    # ==================================================
    # FINAL 3-LINE SUMMARY
    # ==================================================

    summary_lines = []


    for item in selected:

        sentence = item[
            "sentence"
        ].strip()


        if not sentence.endswith(
            (".", "!", "?")
        ):

            sentence += "."


        summary_lines.append(
            sentence
        )


    return "\n".join(
        summary_lines
    )