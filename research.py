import requests

from bs4 import BeautifulSoup

from urllib.parse import (
    urlparse,
    parse_qs,
    unquote
)

from summarizer import summarize_research


# ======================================================
# AI POCKET SCIENTIST
# STEP 1 - WEB RESEARCH ENGINE
#
# NO CHATBOT
# NO GEMINI
# NO GROQ
# NO PERPLEXITY
#
# Question
#    ↓
# DuckDuckGo Lite search
#    ↓
# Trusted websites only
#    ↓
# Read webpage text
#    ↓
# summarizer.py
#    ↓
# 3-line answer
# ======================================================


# ======================================================
# SETTINGS
# ======================================================

MAX_WEBSITES = 5


# ======================================================
# TRUSTED DOMAINS
# ======================================================

TRUSTED_DOMAINS = [

    # -------------------------
    # GENERAL SCIENCE
    # -------------------------

    "nasa.gov",
    "usgs.gov",
    "noaa.gov",
    "nsf.gov",
    "energy.gov",
    "epa.gov",

    "nih.gov",
    "ncbi.nlm.nih.gov",
    "medlineplus.gov",
    "cdc.gov",

    "who.int",
    "esa.int",
    "cern.ch",


    # -------------------------
    # UNIVERSITIES
    # -------------------------

    "mit.edu",
    "harvard.edu",
    "stanford.edu",
    "berkeley.edu",
    "caltech.edu",

    "cam.ac.uk",
    "ox.ac.uk",


    # -------------------------
    # EDUCATION
    # -------------------------

    "khanacademy.org",
    "openstax.org",
    "physicsclassroom.com",
    "ck12.org",

    "libretexts.org",


    # -------------------------
    # ENCYCLOPEDIAS
    # -------------------------

    "britannica.com",
    "wikipedia.org",


    # -------------------------
    # GENERAL SCIENCE / NATURE
    # -------------------------

    "nationalgeographic.com",
    "smithsonianmag.com",
    "si.edu",
    "amnh.org",

    "sciencenews.org",
    "livescience.com",
    "scientificamerican.com",

    "nature.com",
    "science.org",
    "pnas.org",
    "royalsociety.org",


    # -------------------------
    # HEALTH / HUMAN BODY
    # -------------------------

    "kidshealth.org",
    "mayoclinic.org",
    "clevelandclinic.org",


    # -------------------------
    # ANIMAL / WILDLIFE
    # -------------------------

    "animaldiversity.org",
    "gbif.org",
    "eol.org",
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

    "sandiegozoowildlifealliance.org",
    "worldwildlife.org",
    "inaturalist.org"
]


# ======================================================
# HEADERS
# ======================================================

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language":
        "en-US,en;q=0.9"

}


# ======================================================
# CHECK WHETHER URL IS TRUSTED
# ======================================================

def is_trusted_url(url):

    try:

        parsed = urlparse(url)

        domain = parsed.netloc.lower()

        # Remove port if any
        domain = domain.split(":")[0]

        # Remove www.
        if domain.startswith("www."):

            domain = domain[4:]


        for trusted in TRUSTED_DOMAINS:

            if domain == trusted:
                return True


            if domain.endswith(
                "." + trusted
            ):

                return True


        return False


    except Exception:

        return False


# ======================================================
# GET REAL URL FROM DUCKDUCKGO REDIRECT
# ======================================================

def get_real_url(url):

    if not url:

        return ""


    try:

        # Sometimes DuckDuckGo gives:
        #
        # //duckduckgo.com/l/?uddg=https%3A%2F%2F...
        #
        # or:
        #
        # https://duckduckgo.com/l/?uddg=...

        if url.startswith("//"):

            url = "https:" + url


        parsed = urlparse(url)


        if (
            "duckduckgo.com" in parsed.netloc
            and
            "uddg=" in parsed.query
        ):

            params = parse_qs(
                parsed.query
            )


            real_url = params.get(
                "uddg"
            )


            if real_url:

                return unquote(
                    real_url[0]
                )


        return url


    except Exception:

        return url


# ======================================================
# SEARCH DUCKDUCKGO LITE
# ======================================================

def search_once(search_query):

    print("\nTrying search:")
    print(search_query)


    search_url = (
        "https://lite.duckduckgo.com/lite/"
    )


    try:

        response = requests.post(

            search_url,

            data={
                "q": search_query
            },

            headers=HEADERS,

            timeout=20

        )


        response.raise_for_status()


        print(
            "DuckDuckGo status:",
            response.status_code
        )


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        links = []


        # Look at every link returned by DDG Lite
        for tag in soup.find_all("a"):

            href = tag.get(
                "href"
            )


            if not href:
                continue


            real_url = get_real_url(
                href
            )


            if not real_url:
                continue


            if not real_url.startswith(
                ("http://", "https://")
            ):
                continue


            if not is_trusted_url(
                real_url
            ):
                continue


            if real_url not in links:

                links.append(
                    real_url
                )


                print(
                    "Found trusted result:",
                    real_url
                )


        print(
            "Trusted results from this search:",
            len(links)
        )


        return links


    except Exception as error:

        print(
            "Search error:"
        )

        print(error)


        return []


# ======================================================
# SEARCH WEB
# ======================================================

def search_web(question):

    print(
        "\n================================="
    )

    print(
        "SEARCHING WEB"
    )

    print(
        "================================="
    )


    print(
        "Original query:"
    )

    print(
        question
    )


    links = []


    # --------------------------------------------------
    # 1. EXACT SEARCH
    # --------------------------------------------------

    exact_results = search_once(
        question
    )


    for url in exact_results:

        if url not in links:

            links.append(
                url
            )


        if len(links) >= MAX_WEBSITES:

            return links


    # --------------------------------------------------
    # 2. FALLBACK SEARCHES
    # --------------------------------------------------

    fallback_queries = [

        question + " science",

        question + " biology",

        question + " facts",

        question + " explanation"

    ]


    for fallback_query in fallback_queries:

        if len(links) >= MAX_WEBSITES:
            break


        results = search_once(
            fallback_query
        )


        for url in results:

            if url not in links:

                links.append(
                    url
                )


            if len(links) >= MAX_WEBSITES:
                break


    return links


# ======================================================
# CLEAN WEBPAGE
# ======================================================

def clean_webpage(soup):

    unwanted_tags = [

        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript",
        "button",
        "svg",
        "iframe"

    ]


    for tag_name in unwanted_tags:

        for tag in soup.find_all(
            tag_name
        ):

            tag.decompose()


    return soup


# ======================================================
# READ ONE WEBSITE
# ======================================================

def read_website(url):

    print("\nReading:")
    print(url)


    try:

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=20,

            allow_redirects=True

        )


        response.raise_for_status()


        print(
            "Page status:",
            response.status_code
        )


        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()


        # Skip PDFs, images, etc.
        if (
            "text/html" not in content_type
            and
            "application/xhtml+xml"
            not in content_type
        ):

            print(
                "Skipped: not an HTML page."
            )

            return ""


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        soup = clean_webpage(
            soup
        )


        paragraphs = soup.find_all(
            "p"
        )


        useful_paragraphs = []


        for paragraph in paragraphs:

            text = paragraph.get_text(
                " ",
                strip=True
            )


            text = " ".join(
                text.split()
            )


            # Ignore tiny navigation-like text
            if len(text) < 60:
                continue


            useful_paragraphs.append(
                text
            )


        combined_text = " ".join(
            useful_paragraphs
        )


        # Limit page size
        combined_text = combined_text[
            :15000
        ]


        print(
            "Characters collected:",
            len(combined_text)
        )


        return combined_text


    except Exception as error:

        print(
            "Could not read website:"
        )

        print(error)


        return ""


# ======================================================
# COMPLETE RESEARCH PROCESS
# ======================================================

def research_question(question):

    websites = search_web(
        question
    )


    print(
        "\n================================="
    )

    print(
        "TRUSTED WEBSITES FOUND:",
        len(websites)
    )

    print(
        "================================="
    )


    research_results = []


    for website in websites:

        text = read_website(
            website
        )


        if text:

            research_results.append({

                "url":
                    website,

                "text":
                    text

            })


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
# STEP 1 + STEP 2
# ======================================================

if __name__ == "__main__":

    question = input(
        "\nEnter research question: "
    )


    # STEP 1
    results = research_question(
        question
    )


    if not results:

        print(
            "\nNo useful information found."
        )


    else:

        # STEP 2
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