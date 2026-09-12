import re
import requests

from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse, urljoin

from summarizer import summarize_research


# ======================================================
# AI POCKET SCIENTIST
# TRUSTED-WEBSITE RESEARCH ENGINE
# ======================================================
#
# 125 trusted websites are available.
#
# We DO NOT contact all 125 for every question.
# That would be too slow/heavy for Render.
#
# Question
#    ↓
# Detect science category
#    ↓
# Choose relevant trusted websites
#    ↓
# Collect several candidate pages
#    ↓
# Balanced relevance filter
#    ↓
# Read useful pages
#    ↓
# summarizer.py
#    ↓
# 3-line answer
#
# ======================================================


# ======================================================
# SETTINGS
# ======================================================

# Final number of GOOD webpages used for one answer.
MAX_GOOD_WEBSITES = 5


# Maximum number of trusted sites searched per question.
MAX_SOURCE_SEARCHES = 12


# Maximum candidate results collected from each website.
MAX_RESULTS_PER_SOURCE = 3


# Maximum candidate pages before page-reading starts.
MAX_CANDIDATES = 15


# Maximum search URL formats attempted per website.
MAX_SEARCH_ATTEMPTS_PER_SOURCE = 2


# Search-result HTML memory limit.
MAX_SEARCH_HTML_BYTES = 250000


# Actual article-page download limit.
MAX_DOWNLOAD_BYTES = 400000


# Maximum useful article text kept from one page.
MAX_TEXT_CHARS = 7000


# Request timeout.
REQUEST_TIMEOUT = 6


# Very long questions are reduced before searching.
MAX_SEARCH_QUERY_LENGTH = 180


# Balanced search-result threshold.
#
# Lower = more loose
# Higher = more strict
#
# 7 works well as a middle value.
MIN_RESULT_SCORE = 7


# ======================================================
# 125 TRUSTED WEBSITES
# ======================================================

SOURCE_GROUPS = {

    # ==================================================
    # GENERAL SCIENCE - 19
    # ==================================================

    "general": [

        "wikipedia.org",
        "britannica.com",
        "si.edu",
        "smithsonianmag.com",
        "nationalgeographic.com",
        "science.org",
        "nature.com",
        "pnas.org",
        "royalsociety.org",
        "sciencenews.org",
        "scientificamerican.com",
        "livescience.com",
        "aaas.org",
        "nsf.gov",
        "nasonline.org",
        "nationalacademies.org",
        "khanacademy.org",
        "openstax.org",
        "libretexts.org",

    ],


    # ==================================================
    # SPACE / ASTRONOMY - 9
    # ==================================================

    "space": [

        "nasa.gov",
        "science.nasa.gov",
        "jpl.nasa.gov",
        "esa.int",
        "skyandtelescope.org",
        "iau.org",
        "noirlab.edu",
        "stsci.edu",
        "planetary.org",

    ],


    # ==================================================
    # ANIMALS / WILDLIFE - 28
    # ==================================================

    "animals": [

        "animaldiversity.org",
        "eol.org",
        "gbif.org",
        "iucnredlist.org",
        "mammaldiversity.org",

        "allaboutbirds.org",
        "ebird.org",
        "audubon.org",

        "bugguide.net",
        "butterfliesandmoths.org",
        "xerces.org",
        "butterfly-conservation.org",
        "monarchjointventure.org",

        "fishbase.se",
        "marinespecies.org",

        "reptile-database.reptarium.cz",
        "amphibiaweb.org",

        "inaturalist.org",
        "worldwildlife.org",
        "sandiegozoowildlifealliance.org",

        "aza.org",
        "oceana.org",
        "birdlife.org",

        "nhm.ac.uk",
        "amnh.org",

        "ocean.si.edu",
        "fisheries.noaa.gov",
        "oceanservice.noaa.gov",

    ],


    # ==================================================
    # HEALTH / HUMAN BODY - 20
    # ==================================================

    "health": [

        "nih.gov",
        "ncbi.nlm.nih.gov",
        "medlineplus.gov",
        "cdc.gov",
        "who.int",

        "mayoclinic.org",
        "clevelandclinic.org",
        "kidshealth.org",
        "nhs.uk",

        "health.harvard.edu",
        "hopkinsmedicine.org",
        "stanfordhealthcare.org",

        "msdmanuals.com",
        "merckmanuals.com",

        "cancer.gov",
        "heart.org",
        "lung.org",
        "diabetes.org",

        "ninds.nih.gov",
        "niaid.nih.gov",

    ],


    # ==================================================
    # EARTH / ENVIRONMENT - 19
    # ==================================================

    "earth": [

        "usgs.gov",
        "noaa.gov",
        "epa.gov",

        "usda.gov",
        "fs.usda.gov",

        "nps.gov",
        "usbr.gov",

        "weather.gov",
        "climate.gov",

        "earthobservatory.nasa.gov",

        "agu.org",
        "eos.org",

        "wmo.int",
        "ipcc.ch",
        "unep.org",

        "earthdata.nasa.gov",
        "oceanexplorer.noaa.gov",

        "volcano.si.edu",
        "iris.edu",

    ],


    # ==================================================
    # PHYSICS - 14
    # ==================================================

    "physics": [

        "cern.ch",
        "aps.org",
        "aip.org",

        "physicsworld.com",
        "physicsclassroom.com",

        "fnal.gov",
        "slac.stanford.edu",

        "lanl.gov",
        "lbl.gov",

        "energy.gov",
        "nist.gov",

        "iop.org",

        "quantamagazine.org",
        "symmetrymagazine.org",

    ],


    # ==================================================
    # CHEMISTRY - 7
    # ==================================================

    "chemistry": [

        "acs.org",
        "rsc.org",

        "pubchem.ncbi.nlm.nih.gov",

        "iupac.org",

        "chem.libretexts.org",
        "periodic-table.rsc.org",

        "chemguide.co.uk",

    ],


    # ==================================================
    # PLANTS / BOTANY - 9
    # ==================================================

    "plants": [

        "plants.usda.gov",
        "kew.org",
        "missouribotanicalgarden.org",
        "mobot.org",

        "powo.science.kew.org",
        "plantscience.psu.edu",

        "botany.org",
        "ucmp.berkeley.edu",

        "catalogueoflife.org",

    ],

}


# ======================================================
# BUILD COMPLETE TRUSTED LIST
# ======================================================

TRUSTED_DOMAINS = [

    domain

    for group in SOURCE_GROUPS.values()

    for domain in group

]


# Make sure it ALWAYS stays exactly 125.
assert len(TRUSTED_DOMAINS) == 125, (
    f"Expected 125 trusted websites, "
    f"found {len(TRUSTED_DOMAINS)}"
)


# Also make sure there are no duplicates.
assert len(set(TRUSTED_DOMAINS)) == 125, (
    "Trusted website list contains duplicates"
)


# ======================================================
# QUESTION CATEGORY KEYWORDS
# ======================================================

CATEGORY_KEYWORDS = {

    "space": {

        "space",
        "planet",
        "planets",
        "moon",
        "sun",
        "star",
        "stars",
        "galaxy",
        "galaxies",
        "universe",
        "astronomy",
        "asteroid",
        "comet",
        "mars",
        "venus",
        "jupiter",
        "saturn",
        "orbit",
        "rocket",
        "telescope",
        "black hole",
        "nebula",

    },


    "animals": {

        "animal",
        "animals",
        "wildlife",
        "species",

        "mammal",
        "mammals",

        "bird",
        "birds",

        "fish",

        "insect",
        "insects",

        "butterfly",
        "butterflies",

        "moth",
        "bee",
        "ant",
        "spider",

        "reptile",
        "snake",
        "lizard",

        "frog",
        "amphibian",

        "ocean animal",
        "marine animal",

        "dolphin",
        "whale",
        "shark",
        "turtle",

        "beetle",
        "dragonfly",

    },


    "health": {

        "health",
        "human body",
        "body",

        "disease",
        "virus",
        "bacteria",
        "infection",

        "medicine",
        "medical",

        "heart",
        "lung",
        "brain",
        "blood",

        "diabetes",
        "cancer",
        "fever",

        "nutrition",
        "vitamin",

        "symptom",
        "symptoms",

        "immune",
        "immunity",

        "cell",
        "cells",

    },


    "earth": {

        "earth",
        "weather",
        "climate",

        "ocean",
        "sea",
        "river",
        "water",

        "rock",
        "rocks",
        "mineral",

        "volcano",
        "earthquake",

        "soil",

        "environment",
        "pollution",
        "ecosystem",

        "geology",

        "storm",
        "hurricane",
        "tornado",
        "tsunami",

        "glacier",
        "forest",

    },


    "physics": {

        "physics",

        "force",
        "motion",
        "energy",

        "electricity",

        "magnet",
        "magnetic",

        "gravity",

        "light",
        "sound",

        "wave",
        "waves",

        "atom",
        "quantum",
        "particle",

        "speed",
        "velocity",
        "mass",
        "acceleration",

        "friction",
        "circuit",

    },


    "chemistry": {

        "chemistry",
        "chemical",

        "element",
        "elements",

        "molecule",
        "molecules",

        "compound",
        "reaction",

        "acid",
        "base",

        "periodic",

        "bond",
        "bonds",

        "solution",
        "mixture",

        "carbon",
        "oxygen",

    },


    "plants": {

        "plant",
        "plants",

        "flower",
        "flowers",

        "tree",
        "trees",

        "leaf",
        "leaves",

        "seed",
        "seeds",

        "root",
        "roots",

        "photosynthesis",

        "botany",

        "fungus",
        "fungi",

        "moss",
        "fern",

    },

}


# ======================================================
# STOP WORDS
# ======================================================

SEARCH_STOP_WORDS = {

    "a",
    "an",
    "the",
    "and",
    "or",

    "is",
    "are",
    "was",
    "were",
    "be",

    "to",
    "of",
    "in",
    "on",
    "at",

    "for",
    "from",
    "with",

    "what",
    "why",
    "how",
    "who",
    "where",
    "when",

    "this",
    "that",
    "these",
    "those",

    "image",
    "picture",
    "photo",

    "tell",
    "me",
    "about",

    "does",
    "do",

    "can",
    "could",
    "would",
    "should",

    "explain",

}


# ======================================================
# BROAD WORDS
#
# These words are useful, but should not by themselves
# make a page look highly relevant.
# ======================================================

BROAD_TOPIC_WORDS = {

    "science",
    "scientific",

    "animal",
    "animals",

    "wildlife",
    "species",

    "mammal",
    "mammals",

    "bird",
    "birds",

    "fish",

    "insect",
    "insects",

    "butterfly",
    "butterflies",

    "plant",
    "plants",

    "flower",
    "flowers",

    "tree",
    "trees",

    "health",
    "body",

    "earth",
    "space",

    "physics",
    "chemistry",
    "chemical",

    "weather",
    "climate",

    "ocean",
    "nature",

}


# ======================================================
# SMALL WORD ALIASES
# ======================================================

WORD_ALIASES = {

    "fly": (
        "fly",
        "flying",
        "flight"
    ),

    "flies": (
        "flies",
        "flying",
        "flight"
    ),

    "bird": (
        "bird",
        "birds"
    ),

    "birds": (
        "bird",
        "birds"
    ),

}


# ======================================================
# HTTP HEADERS
# ======================================================

HEADERS = {

    "User-Agent": (

        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"

    ),

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language":
        "en-US,en;q=0.9",

}


# ======================================================
# NORMALIZE TEXT
# ======================================================

def normalize_text(text):

    return re.sub(

        r"\s+",

        " ",

        str(
            text or ""
        )

    ).strip().lower()


# ======================================================
# GET IMPORTANT QUESTION WORDS
# ======================================================

def get_query_words(question):

    words = re.findall(

        r"[A-Za-z][A-Za-z'-]*",

        normalize_text(
            question
        )

    )


    return [

        word

        for word in words

        if (
            word not in SEARCH_STOP_WORDS
            and
            len(word) >= 3
        )

    ]


# ======================================================
# CLEAN QUESTION
# ======================================================

def clean_search_question(question):

    cleaned = re.sub(

        r"\s+",

        " ",

        str(
            question or ""
        )

    ).strip()


    if not cleaned:

        return ""


    if len(cleaned) <= MAX_SEARCH_QUERY_LENGTH:

        return cleaned


    keywords = get_query_words(
        cleaned
    )


    if not keywords:

        return cleaned[
            :MAX_SEARCH_QUERY_LENGTH
        ].strip()


    return " ".join(

        keywords[:10]

    )[:MAX_SEARCH_QUERY_LENGTH].strip()


# ======================================================
# FLEXIBLE WORD MATCH
# ======================================================

def word_matches_text(
    word,
    text
):

    text = normalize_text(
        text
    )

    word = normalize_text(
        word
    )


    if not word:

        return False


    # --------------------------------------------------
    # ALIASES
    # --------------------------------------------------

    for alias in WORD_ALIASES.get(
        word,
        (word,)
    ):

        if alias in text:

            return True


    # --------------------------------------------------
    # SIMPLE SCIENTIFIC / PLURAL MATCHING
    #
    # Example:
    #
    # lycaenid
    # matches
    # Lycaenidae
    #
    # butterfly
    # matches
    # butterflies
    # --------------------------------------------------

    if len(word) >= 6:

        stem = word[:5]


        if stem in text:

            return True


    return False


# ======================================================
# DETECT QUESTION CATEGORY
# ======================================================

def classify_question(question):

    text = normalize_text(
        question
    )


    categories = []


    for category, keywords in CATEGORY_KEYWORDS.items():

        if any(

            keyword in text

            for keyword in keywords

        ):

            categories.append(
                category
            )


    # No obvious category?
    # Use general science.
    if not categories:

        categories.append(
            "general"
        )


    return categories


# ======================================================
# ADD UNIQUE ITEM
# ======================================================

def add_unique(
    items,
    value
):

    if value not in items:

        items.append(
            value
        )


# ======================================================
# SELECT RELEVANT WEBSITES FROM 125
# ======================================================

def select_source_domains(question):

    categories = classify_question(
        question
    )


    selected = []


    # --------------------------------------------------
    # GENERAL REFERENCE SOURCES FIRST
    # --------------------------------------------------

    add_unique(
        selected,
        "wikipedia.org"
    )

    add_unique(
        selected,
        "britannica.com"
    )


    # --------------------------------------------------
    # CATEGORY SOURCES
    # --------------------------------------------------

    for category in categories:

        for domain in SOURCE_GROUPS.get(
            category,
            []
        ):

            add_unique(
                selected,
                domain
            )


    # --------------------------------------------------
    # GENERAL SCIENCE FALLBACK SOURCES
    # --------------------------------------------------

    for domain in SOURCE_GROUPS[
        "general"
    ]:

        add_unique(
            selected,
            domain
        )


    # We have 125 available,
    # but only query the most relevant ones.
    return selected[
        :MAX_SOURCE_SEARCHES
    ]


# ======================================================
# DOMAIN CHECK
# ======================================================

def belongs_to_domain(
    url,
    allowed_domain
):

    try:

        domain = (

            urlparse(url)
            .netloc
            .lower()
            .split(":")[0]

        )


        if domain.startswith(
            "www."
        ):

            domain = domain[4:]


        allowed = (
            allowed_domain
            .lower()
        )


        if allowed.startswith(
            "www."
        ):

            allowed = allowed[4:]


        return (

            domain == allowed

            or

            domain.endswith(
                "." + allowed
            )

        )


    except Exception:

        return False


# ======================================================
# CHECK IF URL LOOKS LIKE REAL CONTENT
# ======================================================

def is_content_url(
    url,
    allowed_domain
):

    try:

        parsed = urlparse(
            url
        )


        if parsed.scheme not in (
            "http",
            "https"
        ):

            return False


        if not belongs_to_domain(
            url,
            allowed_domain
        ):

            return False


        path = parsed.path.lower()


        # Home page is not an article.
        if path in (
            "",
            "/"
        ):

            return False


        # --------------------------------------------------
        # BLOCK NON-CONTENT PAGES
        # --------------------------------------------------

        blocked_parts = (

            "/search",

            "/login",
            "/signin",

            "/signup",
            "/register",

            "/privacy",
            "/terms",

            "/contact",
            "/about",
            "/help",

            "/account",

            "/donate",
            "/subscribe",
            "/newsletter",

            "/author/",
            "/tag/",
            "/category/",

        )


        if any(

            part in path

            for part in blocked_parts

        ):

            return False


        # --------------------------------------------------
        # BLOCK NON-WEBPAGE FILES
        # --------------------------------------------------

        blocked_extensions = (

            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",

            ".pdf",
            ".zip",

            ".mp4",
            ".mp3",

            ".xml",

        )


        if path.endswith(
            blocked_extensions
        ):

            return False


        # --------------------------------------------------
        # WIKIPEDIA SPECIAL PAGES
        # --------------------------------------------------

        if "wikipedia.org" in allowed_domain:

            blocked_wiki = (

                "/wiki/special:",
                "/wiki/help:",
                "/wiki/category:",
                "/wiki/template:",
                "/wiki/file:",
                "/wiki/talk:",

            )


            if any(

                item in path

                for item in blocked_wiki

            ):

                return False


        return True


    except Exception:

        return False


# ======================================================
# LIMITED HTML DOWNLOAD
# ======================================================

def fetch_limited_html(
    url,
    params=None,
    byte_limit=MAX_SEARCH_HTML_BYTES
):

    try:

        with requests.get(

            url,

            params=params,

            headers=HEADERS,

            timeout=REQUEST_TIMEOUT,

            allow_redirects=True,

            stream=True

        ) as response:


            response.raise_for_status()


            content_type = (

                response
                .headers
                .get(
                    "Content-Type",
                    ""
                )
                .lower()

            )


            if (
                content_type
                and
                "text/html"
                not in content_type
                and
                "application/xhtml+xml"
                not in content_type
            ):

                return (
                    response.url,
                    ""
                )


            downloaded = bytearray()


            for chunk in response.iter_content(
                chunk_size=8192
            ):

                if not chunk:

                    continue


                downloaded.extend(
                    chunk
                )


                if len(downloaded) >= byte_limit:

                    break


            encoding = (
                response.encoding
                or "utf-8"
            )


            final_url = (
                response.url
            )


        html = downloaded.decode(

            encoding,

            errors="ignore"

        )


        del downloaded


        return (
            final_url,
            html
        )


    except Exception as error:

        print(
            "Fetch failed:",
            url,
            "->",
            error
        )


        return (
            url,
            ""
        )


# ======================================================
# SEARCH URL FORMATS
# ======================================================

def build_search_attempts(
    domain,
    question
):

    # --------------------------------------------------
    # WIKIPEDIA
    # --------------------------------------------------

    if domain == "wikipedia.org":

        return [

            (

                "https://en.wikipedia.org/w/index.php",

                {
                    "search":
                        question
                }

            )

        ]


    # --------------------------------------------------
    # BRITANNICA
    # --------------------------------------------------

    if domain == "britannica.com":

        return [

            (

                "https://www.britannica.com/search",

                {
                    "query":
                        question
                }

            )

        ]


    # --------------------------------------------------
    # ANIMAL DIVERSITY WEB
    # --------------------------------------------------

    if domain == "animaldiversity.org":

        return [

            (

                "https://animaldiversity.org/search/",

                {
                    "feature":
                        "INFORMATION",

                    "q":
                        question
                }

            )

        ]


    # --------------------------------------------------
    # GENERIC DIRECT WEBSITE SEARCH
    #
    # Most modern websites use one of these.
    # --------------------------------------------------

    base = (
        "https://"
        + domain
    )


    return [

        (

            base + "/search",

            {
                "q":
                    question
            }

        ),

        (

            base + "/",

            {
                "s":
                    question
            }

        ),

    ]


# ======================================================
# SEARCH RESULT SCORE
# ======================================================

def score_result(
    url,
    anchor_text,
    question
):

    query_words = get_query_words(
        question
    )


    if not query_words:

        return 0


    title_text = normalize_text(
        anchor_text
    )


    url_text = normalize_text(
        url
    )


    full_text = (

        title_text

        + " "

        + url_text

    )


    score = 0


    normalized_question = normalize_text(
        question
    )


    # --------------------------------------------------
    # EXACT PHRASE BONUS
    # --------------------------------------------------

    if (
        normalized_question
        and
        normalized_question
        in title_text
    ):

        score += 10


    # --------------------------------------------------
    # WORD MATCHES
    # --------------------------------------------------

    for word in query_words:

        title_match = word_matches_text(

            word,

            title_text

        )


        url_match = word_matches_text(

            word,

            url_text

        )


        if title_match:

            score += 4


        if url_match:

            score += 2


        # Specific scientific names / concepts
        # get additional importance.
        if (
            word not in BROAD_TOPIC_WORDS
            and
            word_matches_text(
                word,
                full_text
            )
        ):

            score += 3


    # --------------------------------------------------
    # ARTICLE-LIKE PATH BONUS
    # --------------------------------------------------

    path = urlparse(
        url
    ).path


    if path.count("/") >= 2:

        score += 1


    return score


# ======================================================
# SEARCH ONE TRUSTED WEBSITE
# ======================================================

def search_source(
    domain,
    question
):

    safe_question = clean_search_question(
        question
    )


    print(
        "\n---------------------------------"
    )


    print(
        "Searching:",
        domain
    )


    print(
        "Query:",
        safe_question
    )


    results = []

    seen_urls = set()


    attempts = build_search_attempts(

        domain,

        safe_question

    )


    for search_url, params in attempts[
        :MAX_SEARCH_ATTEMPTS_PER_SOURCE
    ]:


        final_url, html = fetch_limited_html(

            search_url,

            params=params,

            byte_limit=
                MAX_SEARCH_HTML_BYTES

        )


        if not html:

            continue


        # ==================================================
        # SEARCH REDIRECTED DIRECTLY TO ARTICLE
        # ==================================================

        if is_content_url(
            final_url,
            domain
        ):

            direct_score = (

                score_result(

                    final_url,

                    final_url,

                    safe_question

                )

                + 6

            )


            if (
                direct_score
                >= MIN_RESULT_SCORE
                and
                final_url not in seen_urls
            ):

                results.append({

                    "url":
                        final_url,

                    "score":
                        direct_score,

                    "source":
                        domain

                })


                seen_urls.add(
                    final_url
                )


        # ==================================================
        # PARSE SEARCH PAGE LINKS
        # ==================================================

        link_filter = SoupStrainer(
            "a"
        )


        soup = BeautifulSoup(

            html,

            "html.parser",

            parse_only=
                link_filter

        )


        del html


        for tag in soup.find_all(
            "a",
            href=True
        ):

            href = tag.get(
                "href"
            )


            if not href:

                continue


            url = urljoin(

                final_url,

                href

            )


            if url in seen_urls:

                continue


            if not is_content_url(
                url,
                domain
            ):

                continue


            anchor_text = tag.get_text(

                " ",

                strip=True

            )


            if not anchor_text:

                continue


            score = score_result(

                url,

                anchor_text,

                safe_question

            )


            # Balanced threshold.
            if score < MIN_RESULT_SCORE:

                continue


            results.append({

                "url":
                    url,

                "score":
                    score,

                "source":
                    domain

            })


            seen_urls.add(
                url
            )


        soup.decompose()

        del soup


        # If this search style worked,
        # don't waste another request.
        if results:

            break


    # ==================================================
    # MOST RELEVANT FIRST
    # ==================================================

    results.sort(

        key=
            lambda item:
                item["score"],

        reverse=True

    )


    results = results[
        :MAX_RESULTS_PER_SOURCE
    ]


    for result in results:

        print(

            "Candidate:",

            result["url"],

            "score:",

            result["score"]

        )


    return results


# ======================================================
# SEARCH THE 125-SITE TRUSTED POOL
# ======================================================

def search_web(question):

    print(
        "\n================================="
    )

    print(
        "TRUSTED-SITE SEARCH"
    )

    print(
        "================================="
    )


    print(
        "Question:",
        question
    )


    selected_domains = select_source_domains(
        question
    )


    print(
        "Question categories:",
        classify_question(question)
    )


    print(
        "Trusted pool size:",
        len(TRUSTED_DOMAINS)
    )


    print(
        "Sources selected for this question:",
        len(selected_domains)
    )


    all_results = []

    seen_urls = set()


    # ==================================================
    # SEARCH SELECTED TRUSTED SITES
    # ==================================================

    for domain in selected_domains:

        source_results = search_source(

            domain,

            question

        )


        for result in source_results:

            if result["url"] in seen_urls:

                continue


            all_results.append(
                result
            )


            seen_urls.add(
                result["url"]
            )


        # We already have enough candidates.
        if len(all_results) >= MAX_CANDIDATES:

            break


    # ==================================================
    # SORT ALL CANDIDATES
    # ==================================================

    all_results.sort(

        key=
            lambda item:
                item["score"],

        reverse=True

    )


    candidates = all_results[
        :MAX_CANDIDATES
    ]


    print(
        "\nCandidate pages found:",
        len(candidates)
    )


    for number, item in enumerate(

        candidates,

        start=1

    ):

        print(

            number,

            item["source"],

            "->",

            item["url"],

            "score:",

            item["score"]

        )


    return candidates


# ======================================================
# READ ONE ARTICLE PAGE
# ======================================================

def read_website(url):

    print(
        "\nReading:"
    )


    print(
        url
    )


    final_url, html = fetch_limited_html(

        url,

        params=None,

        byte_limit=
            MAX_DOWNLOAD_BYTES

    )


    if not html:

        return ""


    # ==================================================
    # PARSE ONLY PARAGRAPHS
    #
    # This keeps memory usage low.
    # ==================================================

    paragraph_filter = SoupStrainer(
        "p"
    )


    soup = BeautifulSoup(

        html,

        "html.parser",

        parse_only=
            paragraph_filter

    )


    del html


    useful_paragraphs = []


    current_length = 0


    for paragraph in soup.find_all(
        "p"
    ):

        text = paragraph.get_text(

            " ",

            strip=True

        )


        text = " ".join(
            text.split()
        )


        # Ignore navigation / tiny fragments.
        if len(text) < 60:

            continue


        useful_paragraphs.append(
            text
        )


        current_length += len(
            text
        )


        if (
            current_length
            >= MAX_TEXT_CHARS
        ):

            break


    combined_text = " ".join(
        useful_paragraphs
    )


    combined_text = combined_text[
        :MAX_TEXT_CHARS
    ]


    soup.decompose()


    del soup

    del useful_paragraphs


    print(
        "Final URL:",
        final_url
    )


    print(
        "Characters collected:",
        len(combined_text)
    )


    return combined_text


# ======================================================
# PAGE QUALITY + RELEVANCE FILTER
# ======================================================

def page_is_useful(
    text,
    question
):

    if not text:

        return False


    clean_text = normalize_text(
        text
    )


    # Tiny page = probably stub / error.
    if len(clean_text) < 180:

        return False


    # ==================================================
    # ERROR / SEARCH PAGE FILTER
    # ==================================================

    bad_phrases = (

        "does not exist",

        "page does not exist",

        "there were no results matching the query",

        "no results found",

        "search results",

        "this page is not available",

        "search request is longer than the maximum allowed length",

        "search request is too long",

        "cannot find the page you are looking for",

        "please try another search",

        "access denied",

    )


    if any(

        phrase in clean_text

        for phrase in bad_phrases

    ):

        return False


    query_words = get_query_words(
        question
    )


    if not query_words:

        return True


    # ==================================================
    # CHECK QUESTION WORDS IN ARTICLE
    # ==================================================

    matched_words = [

        word

        for word in query_words

        if word_matches_text(
            word,
            clean_text
        )

    ]


    # No relation to question at all.
    if not matched_words:

        return False


    # ==================================================
    # SPECIFIC TERMS
    # ==================================================

    specific_words = [

        word

        for word in query_words

        if word not in BROAD_TOPIC_WORDS

    ]


    specific_matches = [

        word

        for word in specific_words

        if word_matches_text(
            word,
            clean_text
        )

    ]


    # ==================================================
    # BALANCED RULE
    #
    # Example:
    #
    # Query:
    # lycaenid butterfly
    #
    # A page that only says "butterfly"
    # should normally be rejected.
    #
    # But we do not require EVERY word to match.
    # ==================================================

    if (
        specific_words
        and
        not specific_matches
        and
        len(matched_words) < 2
    ):

        return False


    return True


# ======================================================
# COMPLETE RESEARCH PIPELINE
# ======================================================

def research_question(question):

    # ==================================================
    # VALIDATE QUESTION
    # ==================================================

    if (
        not question
        or
        not str(question).strip()
    ):

        return []


    question = clean_search_question(
        question
    )


    if not question:

        return []


    # ==================================================
    # GET MANY CANDIDATES
    # ==================================================

    try:

        candidates = search_web(
            question
        )


    except Exception as error:

        print(
            "Research search failed:",
            error
        )


        return []


    if not candidates:

        print(
            "No candidate pages found."
        )


        return []


    # ==================================================
    # TEST CANDIDATES
    # ==================================================

    research_results = []


    seen_urls = set()


    for candidate in candidates:

        url = candidate.get(
            "url",
            ""
        )


        if not url:

            continue


        if url in seen_urls:

            continue


        seen_urls.add(
            url
        )


        text = read_website(
            url
        )


        # ==================================================
        # REJECT BAD / UNRELATED PAGE
        # ==================================================

        if not page_is_useful(
            text,
            question
        ):

            print(
                "Rejected page:",
                url
            )


            # IMPORTANT:
            # Continue to the next candidate.
            continue


        # ==================================================
        # ACCEPT USEFUL PAGE
        # ==================================================

        print(
            "Accepted useful page:",
            url
        )


        research_results.append({

            "url":
                url,

            "text":
                text,

            "source":
                candidate.get(
                    "source",
                    urlparse(url).netloc
                )

        })


        # Stop only after enough GOOD pages.
        if (
            len(research_results)
            >= MAX_GOOD_WEBSITES
        ):

            break


    print(
        "\n================================="
    )


    print(
        "USEFUL WEBSITES READ:",
        len(research_results)
    )


    print(
        "================================="
    )


    return research_results


# ======================================================
# LOCAL TEST
# ======================================================

if __name__ == "__main__":

    question = input(
        "\nEnter research question: "
    ).strip()


    results = research_question(
        question
    )


    if not results:

        print(
            "\nNo useful information found."
        )


    else:

        # ==================================================
        # SUMMARIZE
        # ==================================================

        summary = summarize_research(

            results,

            question,

            3

        )


        print(
            "\n\n================================="
        )


        print(
            "3-LINE ANSWER"
        )


        print(
            "================================="
        )


        print(
            summary
        )


        # ==================================================
        # SOURCES
        # ==================================================

        print(
            "\n================================="
        )


        print(
            "SOURCES"
        )


        print(
            "================================="
        )


        for number, result in enumerate(

            results,

            start=1

        ):

            print(
                f"{number}. {result['url']}"
            )