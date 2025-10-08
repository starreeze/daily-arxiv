# arXiv Daily Paper

An automated tool for discovering, filtering, and summarizing the latest research papers from arXiv using LLM-based analysis.

## Overview

This tool helps researchers stay up-to-date with the latest academic papers by:
- Searching arXiv for papers based on customizable keywords and categories
- Filtering papers using AI to match specific research interests
- Generating concise summaries highlighting motivation and methodology
- Creating organized monthly reports in Markdown format

The report is saved in `reports/YYYY-MM.md`.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Obtain your Qwen API token (a free service provided by https://chat.qwen.ai, please refer to the [Qwen WebAPI Project](https://github.com/starreeze/qwen-webapi)):
   - Option 1: Add it to `config.json` under `qwen_webapi_token`
   - Option 2: Set environment variable `QWEN_WEBAPI_TOKEN`

3. Edit `config.json` to customize your search:

```json
{
    "batch_size": 10,
    "search_keyword": "keyword",
    "categories": [
        "cs.AI",
        "cs.CV",
        "cs.CL",
        "cs.LG",
        "cs.MM"
    ],
    "filter_statement": "Your custom filter criteria...",
    "qwen_webapi_token": ""
}
```

## Usage

### Local Run

Run the tool to search and summarize today's papers:

```bash
python main.py
```

The script will:
1. Search arXiv for papers matching your criteria
2. Filter papers using your custom filter statement
3. Summarize the filtered papers
4. Generate a report in `reports/YYYY-MM.md`

### Github Actions
Activate github actions to run the tool daily. You need to add secrets `PAT_TOKEN` (github personal access token which has content write permission) and `QWEN_WEBAPI_TOKEN` to the repository.

## License

This project is under GPL-3.0 License. Please ensure you comply with arXiv's terms of service and the Qwen WebAPI usage policies.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
