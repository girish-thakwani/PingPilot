# PingPilot

PingPilot is currently focused on multimodal browser-agent research: improving how models ground actions to the correct page element. The repository also contains earlier workflow-automation and Playwright tooling.

## Problem

Multimodal browser agents can predict the right action but still interact with the wrong page element. This is an
element-grounding problem: selecting the correct DOM element for a task, rather than only predicting an action
such as click or fill.

## Project origin

This project grew out of automating workflows for justyouapparels.in. Building the workflows manually was
tedious, and browser agents such as Stagehand and Browser Use sometimes selected the wrong controls. This
highlighted the limits of relying on screenshots or flattened DOM text alone to understand a page.

## Research background

The Mind2Web dataset ([project page](https://osu-nlp-group.github.io/Mind2Web/)) provides browser tasks and
page context for studying this challenge. PingPilot explores whether richer page representations can help a
model distinguish the intended element from other similar candidates.

## Longer-term research direction

One direction is to represent webpage DOM elements as a graph that captures their structure and relationships,
then combine that information with vision-language reasoning. The original concept considered a Graph Attention
Network, a lightweight cross-attention adapter, and LoRA fine-tuning with a Qwen3-VL model. This remains a
research direction; the current model experiment documented below is a Qwen2-VL candidate-selection prototype.

## Current focus: Inference and evaluation

This project is currently centered on inference and evaluation for grounding and action prediction on Mind2Web-style browser tasks. The core goal is to improve how a model selects the correct element in the DOM, not just predict the next action.

The experimental research code in `Inference/`, `models/`, and the dataset/AXTree utilities addresses this challenge. This is the active focus of the project right now.

### What is included

- `batch_inference.py`: a template for running baseline inference across multiple modality settings, including text-only, image-only, multimodal, and axtree-aware setups
- `inference_VLM.py`: an evaluation script that reads model predictions in JSONL format and computes grounding and action quality metrics
- `models/multimodel_qwen.py`: an initial Qwen2-VL inference prototype that combines a task, a screenshot, truncated page HTML, and candidate actions to predict the correct candidate index

### Baseline directions supported

The inference setup is designed to compare several model configurations, such as:

- text-only baselines
- image-only baselines
- multimodal text + image baselines
- axtree / DOM-structure-aware baselines
- multimodal + axtree combinations
- chain-of-thought style variants

The batch baseline runner is currently a scaffold: its model loading and inference functions are placeholders. The Qwen2-VL script is the current end-to-end model experiment, and compares its predicted action index with the dataset target on the `test_website` split.

The Qwen2-VL prototype uses `Qwen/Qwen2-VL-7B-Instruct` with 4-bit NF4 quantization and automatic device mapping. It loads the Multimodal Mind2Web dataset from Hugging Face and supplies screenshot, task text, cleaned HTML (up to 8,000 characters), and candidate action descriptions to the model. This allows the project to explore whether combining visual and textual context helps select the right action candidate.

The prototype currently reports overall candidate-index accuracy and keeps per-example results in memory; it does not yet save predictions to a file or connect directly to the JSONL evaluation utility. Running it requires a CUDA-capable environment with enough GPU resources for the quantized model.

### Evaluation metrics

The evaluation layer measures the core metrics needed to validate browser grounding quality and task completion:

- Element Accuracy (Top-1 grounding)
- Action Accuracy
- Exact Match (element and action together)
- Parse Failure Rate
- Top-k Element Accuracy
- MRR (Mean Reciprocal Rank)
- Per-action Precision / Recall / F1
- Task Success Rate (when task-level labels are available)

### Why this matters

These scripts provide the benchmark layer for the project’s core hypothesis: structured page representations, such as DOM graphs or axtree-style relational structure, can improve grounding accuracy and reduce failures caused by weak localization in browser interfaces. In other words, the model should reason over structure, not just flattened page text.

This research-facing evaluation layer supports the current work: testing whether structural page representations and vision-language reasoning can improve element selection. AXTree preprocessing is available, while graph-model integration and the baseline comparisons remain research directions rather than completed model implementations.

## Project direction

The practical implementation in this repository follows a more engineering-focused version of the same idea: instead of relying on fragile multi-step browser inference alone, PingPilot emphasizes resilient automation, retriable workflows, and clean execution around browser interactions.

This project is designed for:

- WhatsApp Web outreach automation
- CSV or Google Sheets based contact ingestion
- Resumable processing for large outreach runs
- Retry, delay, and offline handling policies
- A structured automation layer built on Playwright

## Current implementation highlights

- Playwright-powered browser automation
- Contact source support from Google Sheets or CSV files
- Message templating via direct text or a file-based message input
- Config-driven policies for retries, batching, and failure handling
- Dry-run and source-channel controls
- Resumable execution patterns for operational stability

## Setup

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Or install using the package metadata:

```bash
pip install -e .
```

## Configuration

Create a `.env` file from the sample template:

```bash
copy .env.example .env
```

Key environment variables include:

- `SOURCE`: `sheet` or `csv`
- `CHANNEL`: `whatsapp_web` or `dry_run`
- `SHEET_URL`: Google Sheet URL
- `CREDS_FILE`: credentials JSON path
- `CSV_PATH`: CSV contacts file path
- `MESSAGE`: WhatsApp invite link or message text
- `MESSAGE_FILE`: optional message file
- `CDP_URL`: Chrome DevTools Protocol endpoint
- retry and batching controls such as `MAX_ATTEMPTS`, `BATCH_SIZE`, and `ROW_RETRIES`

## Usage

The project exposes a CLI entry point:

```bash
pingpilot
```

For the browser automation recorder/flow conversion utilities, the repo also contains examples such as:

```bash
python main.py record https://web.whatsapp.com
python main.py edit main.py
python main.py convert main.py
```

These commands are useful when generating or visualizing automation flows from Playwright scripts.

## Workflow philosophy

PingPilot is built around a practical principle: real-world automation is not only about selecting the correct DOM element, but also about designing workflows that recover gracefully from transient failures, network issues, and UI changes. The system aims to keep outreach automation reliable, observable, and resumable in production-like conditions.

## Repository status

This repository is a working prototype and research-direction project intended to bridge the gap between multimodal web-grounding research and practical automation tooling for outreach tasks.

## License

This project is currently maintained as a local research and automation prototype. Licensing terms should be confirmed before production deployment or commercial reuse.
## Earlier solution direction

Extract relevant interactive elements from the webpage’s DOM, retrieve similar workflows and contextual information
using RAG, and provide them to an LLM to determine the appropriate action. This approach eliminates the need for
custom model training or a Graph Attention Network, making the system simpler, more flexible, and easier to implement.

This remains a proposed direction; the current Qwen2-VL prototype instead evaluates candidate action selection using task text, page HTML, and screenshots.
