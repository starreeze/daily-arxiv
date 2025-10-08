import json
import math
import os
from datetime import datetime
from typing import TypeVar, cast

from iterwrap import retry_dec
from qwen_webapi import QwenApi
from tqdm import tqdm

from arxiv import Paper, search_arxiv
from utils import find_first_json_block

T = TypeVar("T")


def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)

    # If token not in config, try to read from environment variable
    if "qwen_webapi_token" not in config or not config["qwen_webapi_token"]:
        config["qwen_webapi_token"] = os.environ.get("QWEN_WEBAPI_TOKEN", "")

    return config


def create_balanced_batches(items: list[T], batch_size: int) -> list[list[T]]:
    """
    Create balanced batches from a list of items.

    Instead of creating batches of fixed size (which may leave a small remainder),
    this function calculates the total number of batches needed and distributes
    items evenly across all batches.

    Args:
        items: List of items to batch
        batch_size: Target batch size (actual size may be slightly different for balance)

    Returns:
        List of batches, each containing approximately the same number of items
    """
    if not items:
        return []

    # Calculate total number of batches needed
    num_batches = math.ceil(len(items) / batch_size)

    # Calculate base size and number of batches that need one extra item
    base_size = len(items) // num_batches
    extra_items = len(items) % num_batches

    batches = []
    start_idx = 0

    for i in range(num_batches):
        # First 'extra_items' batches get one extra item
        current_batch_size = base_size + (1 if i < extra_items else 0)
        end_idx = start_idx + current_batch_size
        batches.append(items[start_idx:end_idx])
        start_idx = end_idx

    return batches


def format_papers(papers: list[Paper]) -> str:
    return "\n\n".join(
        f"Paper {i+1}\nTitle: {paper.title}\nAbstract:\n{paper.summary}" for i, paper in enumerate(papers)
    )


@retry_dec(max_retry=3)
def filter_papers_batch(papers: list[Paper], filter_statement: str, api: QwenApi) -> list[bool]:
    prompt_template = open("prompts/filter.txt", "r").read()

    # Format papers for the prompt
    papers_text = format_papers(papers)
    prompt = prompt_template.format(filter_statement=filter_statement, papers=papers_text)
    completion = api(prompt)
    json_block, _ = find_first_json_block(completion)
    json_data = json.loads(json_block)

    # Extract list of boolean answers
    assert isinstance(json_data, list) and all(isinstance(item, bool) for item in json_data)
    assert len(json_data) == len(papers), f"Expected {len(papers)} results but got {len(json_data)}"
    return json_data


@retry_dec(max_retry=3)
def summarize_papers_batch(papers: list[Paper], api: QwenApi) -> list[dict[str, str]]:
    prompt_template = open("prompts/summary.txt", "r").read()

    # Format papers for the prompt
    papers_text = format_papers(papers)
    prompt = prompt_template.format(papers=papers_text)
    completion = api(prompt)
    json_block, _ = find_first_json_block(completion)
    data = json.loads(json_block)

    # Validate results
    assert isinstance(data, list)
    assert len(data) == len(papers), f"Expected {len(papers)} summaries but got {len(data)}"
    for item in data:
        assert item["motivation"] and item["method"], "Missing motivation or method in summary"
    return data


def main():
    config = load_config()

    print("Searching for today's papers...")
    papers = search_arxiv(config["search_keyword"], config["categories"])

    if not papers:
        print("No new papers found today.")
        return

    print(f"Found {len(papers)} papers. Filtering and summarizing...")

    api = QwenApi(token=config["qwen_webapi_token"])

    # Process papers in batches
    batch_size = config["batch_size"]
    filtered_papers: list[Paper] = []

    # First, filter all papers in batches with balanced distribution
    paper_batches = create_balanced_batches(papers, batch_size)
    print(f"Filtering papers in {len(paper_batches)} balanced batches...")
    for batch in tqdm(paper_batches):
        filter_results = filter_papers_batch(batch, config["filter_statement"], api)

        for paper, passed in zip(batch, cast(list[bool], filter_results)):
            if passed:
                filtered_papers.append(paper)

    if not filtered_papers:
        print("No papers matched the filter criteria.")
        return

    print(f"{len(filtered_papers)} papers passed the filter. Summarizing...")

    # Then summarize filtered papers in batches with balanced distribution
    filtered_batches = create_balanced_batches(filtered_papers, batch_size)
    print(f"Summarizing in {len(filtered_batches)} balanced batches...")
    selected_papers: list[tuple[Paper, dict[str, str]]] = []
    for batch in tqdm(filtered_batches):
        summaries = summarize_papers_batch(batch, api)

        for paper, summary in zip(batch, cast(list[dict[str, str]], summaries)):
            selected_papers.append((paper, summary | {"abstract": paper.summary}))

    this_month = datetime.now().strftime("%Y-%m")
    os.makedirs(config["report_dir"], exist_ok=True)
    report_path = os.path.join(config["report_dir"], f"{this_month}.md")
    with open(report_path, "a") as f:
        f.write(f"# {this_month}\n\n")
        for paper, summary in selected_papers:
            f.write(f"## {paper.title}\n\n")
            f.write(f"**Authors:** {', '.join(paper.authors)}\n")
            f.write(f"**Link:** {paper.pdf_url}\n\n")
            for k, v in summary.items():
                f.write(f"### {k}\n{v}\n\n")

    print(f"Successfully generated report at {report_path}")


if __name__ == "__main__":
    main()
