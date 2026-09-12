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
# MEMORY-OPTIMIZED FOR RENDER
#
# Question
#    ↓
# DuckDuckGo Lite
#    ↓
# Trusted websites
#    ↓
# Read limited webpage data
#    ↓
# summarizer.py
#    ↓
# 3-line answer
# ======================================================


# ======================================================
# SETTINGS
# ======================================================

# We only need a few good sources
# for a short 3-line answer.
MAX_WEBSITES = 3


# Maximum amount of HTML downloaded
# from ONE website.
#
# 500 KB prevents very large webpages
# from filling Render memory.
MAX_DOWNLOAD_BYTES = 500000


# Maximum useful text kept from ONE website.
MAX_TEXT_CHARS = 6000


# Request timeout
REQUEST_TIMEOUT = 8


# ======================================================
# TRUSTED DOMAINS
# ======================================================

TRUSTED_DOMAINS = [

    # --------------------------------------------------
    # GENERAL SCIENCE
    # --------------------------------------------------

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


    # --------------------------------------------------
    # UNIVERSITIES
    # --------------------------------------------------

    "mit.edu",
    "harvard.edu",
    "stanford.edu",
    "berkeley.edu",
    "caltech.edu",

    "cam.ac.uk",
    "ox.ac.uk",


    # --------------------------------------------------
    # EDUCATION
    # --------------------------------------------------

    "khanacademy.org",
    "openstax.org",
    "physicsclassroom.com",
    "ck12.org",

    "libretexts.org",


    # --------------------------------------------------
    # ENCYCLOPEDIAS
    # --------------------------------------------------

    "britannica.com",
    "wikipedia.org",


    # --------------------------------------------------
    # GENERAL SCIENCE / NATURE
    # --------------------------------------------------

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


    # --------------------------------------------------
    # HEALTH / HUMAN BODY
    # --------------------------------------------------

    "kidshealth.org",
    "mayoclinic.org",
    "clevelandclinic.org",


    # --------------------------------------------------
    # ANIMAL / WILDLIFE
    # --------------------------------------------------

    "animaldiversity.org",
    "gbif.org",
    "eol.org",
    "iucnredlist.org",
    "mammaldiversity.org",


    # --------------------------------------------------
    # BIRDS
    # --------------------------------------------------

    "allaboutbirds.org",
    "ebird.org",
    "audubon.org",


    # --------------------------------------------------
    # INSECTS / BUTTERFLIES
    # --------------------------------------------------

    "bugguide.net",
    "butterfliesandmoths.org",
    "xerces.org",
    "butterfly-conservation.org",
    "monarchjointventure.org",


    # --------------------------------------------------
    # FISH / MARINE LIFE
    # --------------------------------------------------

    "fishbase.se",
    "marinespecies.org",


    # --------------------------------------------------
    # REPTILES / AMPHIBIANS
    # --------------------------------------------------

    "reptile-database.reptarium.cz",
    "amphibiaweb.org",


    # --------------------------------------------------
    # WILDLIFE ORGANIZATIONS
    # --------------------------------------------------

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

        parsed = urlparse(
            url
        )

        domain = (
            parsed
            .netloc
            .lower()
            .split(":")[0]
        )


        # Remove www.
        if domain.startswith(
            "www."
        ):

            domain = domain[4:]


        for trusted in TRUSTED_DOMAINS:

            # Exact domain
            if domain == trusted:

                return True


            # Subdomain
            if domain.endswith(
                "." + trusted
            ):

                return True


        return False


    except Exception:

        return False


# ======================================================
# GET REAL URL FROM DUCKDUCKGO
# ======================================================

def get_real_url(url):

    if not url:

        return ""


    try:

        # DuckDuckGo may return:
        #
        # //duckduckgo.com/l/?uddg=...
        #
        # Convert // into https://

        if url.startswith("//"):

            url = "https:" + url


        parsed = urlparse(
            url
        )


        # DuckDuckGo redirect URL
        if (
            "duckduckgo.com"
            in parsed.netloc
            and
            "uddg="
            in parsed.query
        ):

            params = parse_qs(
                parsed.query
            )


            real_urls = params.get(
                "uddg"
            )


            if real_urls:

                return unquote(
                    real_urls[0]
                )


        return url


    except Exception:

        return url


# ======================================================
# SEARCH DUCKDUCKGO
# ======================================================

def search_once(search_query):

    print(
        "\nTrying search:"
    )

    print(
        search_query
    )


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

            timeout=REQUEST_TIMEOUT

        )


        response.raise_for_status()


        print(
            "DuckDuckGo status:",
            response.status_code
        )


        # Parse search result page
        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        links = []


        # Look through every link
        for tag in soup.find_all(
            "a"
        ):

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


            # Must be real web URL
            if not real_url.startswith(
                (
                    "http://",
                    "https://"
                )
            ):

                continue


            # Only trusted sources
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


            # Stop immediately when we have enough.
            if len(links) >= MAX_WEBSITES:

                break


        # Release BeautifulSoup memory
        soup.decompose()

        del soup


        print(
            "Trusted results:",
            len(links)
        )


        return links


    except Exception as error:

        print(
            "Search error:"
        )

        print(
            error
        )


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


    # --------------------------------------------------
    # SEARCH 1
    # EXACT QUERY
    # --------------------------------------------------

    results = search_once(
        question
    )


    # If we found something useful,
    # stop searching immediately.
    if results:

        return results[
            :MAX_WEBSITES
        ]


    # --------------------------------------------------
    # SEARCH 2
    # ONLY ONE FALLBACK
    # --------------------------------------------------

    print(
        "\nExact search found nothing."
    )

    print(
        "Trying one science fallback..."
    )


    results = search_once(
        question
        + " science"
    )


    return results[
        :MAX_WEBSITES
    ]


# ======================================================
# CLEAN HTML
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
# MEMORY-OPTIMIZED
# ======================================================

def read_website(url):

    print(
        "\nReading:"
    )

    print(
        url
    )


    response = None


    try:

        # --------------------------------------------------
        # STREAM WEBSITE
        # --------------------------------------------------

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=REQUEST_TIMEOUT,

            allow_redirects=True,

            stream=True

        )


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


        # Ignore PDFs, images, etc.
        if (
            "text/html"
            not in content_type
            and
            "application/xhtml+xml"
            not in content_type
        ):

            print(
                "Skipped: not HTML."
            )


            response.close()

            return ""


        # --------------------------------------------------
        # DOWNLOAD ONLY PART OF PAGE
        # --------------------------------------------------

        downloaded = bytearray()


        for chunk in response.iter_content(
            chunk_size=8192
        ):

            if not chunk:

                continue


            downloaded.extend(
                chunk
            )


            # Stop once we reach memory limit
            if (
                len(downloaded)
                >= MAX_DOWNLOAD_BYTES
            ):

                print(
                    "Download limit reached."
                )

                break


        # Save encoding before closing response
        encoding = (
            response.encoding
            or "utf-8"
        )


        response.close()

        response = None


        print(
            "HTML bytes downloaded:",
            len(downloaded)
        )


        # --------------------------------------------------
        # BYTES → HTML TEXT
        # --------------------------------------------------

        html = downloaded.decode(

            encoding,

            errors="ignore"

        )


        # We no longer need bytearray
        del downloaded


        # --------------------------------------------------
        # PARSE HTML
        # --------------------------------------------------

        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        # We no longer need raw HTML string
        del html


        soup = clean_webpage(
            soup
        )


        # --------------------------------------------------
        # EXTRACT PARAGRAPHS
        # --------------------------------------------------

        useful_paragraphs = []


        current_length = 0


        for paragraph in soup.find_all(
            "p"
        ):

            text = paragraph.get_text(
                " ",
                strip=True
            )


            # Normalize spaces
            text = " ".join(
                text.split()
            )


            # Ignore tiny navigation text
            if len(text) < 60:

                continue


            useful_paragraphs.append(
                text
            )


            current_length += (
                len(text)
            )


            # Stop collecting once enough
            # information has been gathered.
            if (
                current_length
                >= MAX_TEXT_CHARS
            ):

                break


        # --------------------------------------------------
        # BUILD FINAL PAGE TEXT
        # --------------------------------------------------

        combined_text = " ".join(
            useful_paragraphs
        )


        combined_text = combined_text[
            :MAX_TEXT_CHARS
        ]


        print(
            "Characters collected:",
            len(combined_text)
        )


        # --------------------------------------------------
        # FREE MEMORY
        # --------------------------------------------------

        soup.decompose()

        del soup

        del useful_paragraphs


        return combined_text


    except Exception as error:

        print(
            "Could not read website:"
        )

        print(
            error
        )


        # Make sure connection closes
        if response is not None:

            try:

                response.close()

            except Exception:

                pass


        return ""


# ======================================================
# COMPLETE STEP 1
# ======================================================

def research_question(question):

    # --------------------------------------------------
    # FIND TRUSTED PAGES
    # --------------------------------------------------

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


    # --------------------------------------------------
    # READ EACH WEBSITE
    # --------------------------------------------------

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


        # Stop when we have enough good pages
        if (
            len(research_results)
            >= MAX_WEBSITES
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
# STEP 1 + STEP 2
# ======================================================

if __name__ == "__main__":

    question = input(
        "\nEnter research question: "
    )


    # --------------------------------------------------
    # STEP 1
    # --------------------------------------------------

    results = research_question(
        question
    )


    if not results:

        print(
            "\nNo useful information found."
        )


    else:

        # --------------------------------------------------
        # STEP 2
        # --------------------------------------------------

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


        # --------------------------------------------------
        # SOURCES
        # --------------------------------------------------

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