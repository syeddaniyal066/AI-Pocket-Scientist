import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs

from summarizer import summarize_research


# ======================================================
# SETTINGS
# ======================================================

# Maximum number of websites we will read
MAX_WEBSITES = 5


# For now, AI Pocket Scientist prefers these
# science / educational websites.
TRUSTED_DOMAINS = [
    "nasa.gov",
    "usgs.gov",
    "noaa.gov",
    "britannica.com",
    "nationalgeographic.com",
    "smithsonianmag.com",
    "sciencenews.org",
    "wikipedia.org"
]


# ======================================================
# CHECK WHETHER A WEBSITE IS TRUSTED
# ======================================================

def is_trusted_url(url):

    try:

        domain = urlparse(url).netloc.lower()

        # Remove www.
        domain = domain.replace("www.", "")

        for trusted_domain in TRUSTED_DOMAINS:

            if (
                domain == trusted_domain
                or domain.endswith("." + trusted_domain)
            ):
                return True

        return False

    except Exception:

        return False


# ======================================================
# SEARCH WEB
# ======================================================

def search_web(question):

    print("\nSearching for:")
    print(question)

    # Convert spaces and special characters
    # so the question can be used inside a URL.
    search_question = quote_plus(question)

    search_url = (
        "https://html.duckduckgo.com/html/"
        f"?q={search_question}"
    )


    # Makes our request look like a normal browser.
    headers = {

        "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120.0 Safari/537.36"

    }


    try:

        response = requests.get(
            search_url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        links = []


        # Find search-result links.
        search_results = soup.select(
            ".result__a"
        )


        for result in search_results:

            url = result.get("href")

            if not url:
                continue


            # DuckDuckGo sometimes gives us
            # a redirect instead of the real URL.
            if "uddg=" in url:

                parsed_url = urlparse(url)

                parameters = parse_qs(
                    parsed_url.query
                )

                real_url = parameters.get(
                    "uddg"
                )

                if real_url:

                    url = real_url[0]


            # Only accept our trusted websites.
            if is_trusted_url(url):

                if url not in links:

                    links.append(url)


            # Stop after enough websites.
            if len(links) >= MAX_WEBSITES:

                break


        return links


    except Exception as error:

        print(
            "Search error:",
            error
        )

        return []


# ======================================================
# READ ONE WEBSITE
# ======================================================

def read_website(url):

    print("\nReading:")
    print(url)


    headers = {

        "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120.0 Safari/537.36"

    }


    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # Remove unnecessary parts of webpage.
        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "form"
            ]
        ):

            tag.decompose()


        # Find paragraphs.
        paragraphs = soup.find_all("p")


        useful_paragraphs = []


        for paragraph in paragraphs:

            text = paragraph.get_text(
                " ",
                strip=True
            )


            # Skip very short text.
            if len(text) >= 80:

                useful_paragraphs.append(
                    text
                )


        # Combine all useful paragraphs.
        page_text = " ".join(
            useful_paragraphs
        )


        # Don't allow one website to produce
        # an enormous amount of text.
        page_text = page_text[:12000]


        return page_text


    except Exception as error:

        print(
            "Could not read website:",
            error
        )

        return ""


# ======================================================
# COMPLETE RESEARCH PROCESS
# ======================================================

def research_question(question):

    # First search for websites.
    websites = search_web(question)


    print(
        "\nFound",
        len(websites),
        "trusted website(s)."
    )


    research_results = []


    # Read each website.
    for website in websites:

        text = read_website(
            website
        )


        if text:

            research_results.append(
                {
                    "url": website,
                    "text": text
                }
            )


    return research_results


# ======================================================
# TEST PROGRAM
# ======================================================

if __name__ == "__main__":

    question = input(
        "\nAsk a science question: "
    )


    results = research_question(
        question
    )

    summary = summarize_research(
        results,
        question,
        3
    )

    print(
        "\n\n=============================="
    )

    print(
        "3-LINE SUMMARY"
    )

    print(
    "=============================="
)

    print(summary)



    print(
        "\n\n=============================="
    )

    print(
        "RESEARCH RESULTS"
    )

    print(
        "=============================="
    )


    for number, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nWEBSITE {number}"
        )

        print(
            result["url"]
        )

        print(
            "\n"
        )


        # For testing, only show first
        # 1000 characters from each website.
        print(
            result["text"][:1000]
        )


        print(
            "\n------------------------------"
        )