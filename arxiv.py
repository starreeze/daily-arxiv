from dataclasses import dataclass
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


@dataclass
class Paper:
    """Data class to hold paper information parsed from arXiv web search."""

    arxiv_id: str
    title: str
    authors: list[str]
    summary: str
    primary_category: str
    pdf_url: str


def search_arxiv(keyword: str, categories: list[str], today: str, last_day: str) -> list[Paper]:
    """Search arXiv using direct web requests and parse HTML results."""
    # Build the arXiv advanced search URL
    params = {
        "advanced": "",
        "terms-0-operator": "AND",
        "terms-0-term": keyword,
        "terms-0-field": "abstract",
        "classification-physics_archives": "all",
        "classification-include_cross_list": "include",
        "date-year": "",
        "date-filter_by": "date_range",
        "date-from_date": last_day,
        "date-to_date": today,
        "date-date_type": "submitted_date_first",
        "abstracts": "show",
        "size": "100",
        "order": "-announced_date_first",
    }

    url = f"https://arxiv.org/search/advanced?{urlencode(params)}"

    # Fetch the search results
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("li", class_="arxiv-result")

    papers: list[Paper] = []
    for result in results:
        # Extract arxiv ID and PDF URL
        link_tag = result.find("a", href=lambda x: x and "/abs/" in x)  # type: ignore
        if not link_tag:
            continue

        arxiv_url = link_tag["href"]
        arxiv_id = arxiv_url.split("/abs/")[-1]  # type: ignore
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        # Extract primary category
        category_tag = result.find("span", class_="tag")
        if not category_tag:
            continue
        primary_category = category_tag.text.strip()

        # Filter by category
        if primary_category not in categories:
            continue

        # Extract title
        title_tag = result.find("p", class_="title")
        if not title_tag:
            continue
        title = title_tag.text.strip()

        # Extract authors
        authors_tag = result.find("p", class_="authors")
        if not authors_tag:
            continue
        author_links = authors_tag.find_all("a")
        authors = [a.text.strip() for a in author_links]

        # Extract abstract (prefer full abstract)
        abstract_tag = result.find("p", class_="abstract")
        if not abstract_tag:
            continue

        abstract_full = abstract_tag.find("span", class_="abstract-full")
        if abstract_full:
            # Remove the "Less" button text
            for a_tag in abstract_full.find_all("a"):
                a_tag.decompose()
            abstract = abstract_full.text.strip()
        else:
            # Fallback to short abstract
            abstract_short = abstract_tag.find("span", class_="abstract-short")
            if abstract_short:
                for a_tag in abstract_short.find_all("a"):
                    a_tag.decompose()
                abstract = abstract_short.text.strip()
            else:
                abstract = abstract_tag.text.replace("Abstract:", "").strip()

        # Clean up the abstract
        abstract = " ".join(abstract.split())

        paper = Paper(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            summary=abstract,
            primary_category=primary_category,
            pdf_url=pdf_url,
        )
        papers.append(paper)

    return papers
