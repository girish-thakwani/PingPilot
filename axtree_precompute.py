"""Precompute AXTree representations for Multimodal Mind2Web (hang-resistant).

Changes vs original: fresh page per row, timeouts, per-row try/except (bad rows get an
empty tree and are logged), HTML size cap, browser restart every N rows.

    python axtree_precompute.py --split test_website --out_dir data/mind2web_axtree
"""

import argparse
import json
import re

from datasets import load_dataset
from playwright.sync_api import sync_playwright
from tqdm import tqdm

DATASET_NAME = "osunlp/Multimodal-Mind2Web"
VALID_SPLITS = ["train", "test_task", "test_website", "test_domain"]
MAX_HTML_CHARS = 1_500_000
TIMEOUT_MS = 10_000


def sanitize_html(html: str) -> str:
    if not html:
        return ""
    html = html[:MAX_HTML_CHARS]
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.I | re.S)
    html = re.sub(r"<link\b[^>]*>", "", html, flags=re.I)
    return html


def flatten_axtree(snapshot: dict, max_nodes: int = 800, max_chars: int = 12000) -> str:
    if not snapshot:
        return ""
    lines, size = [], 0
    stack = [(snapshot, 0)]
    while stack and len(lines) < max_nodes:
        node, depth = stack.pop()
        role = node.get("role", "")
        name = (node.get("name") or "").strip()
        value = node.get("value")
        value_str = "" if value is None else f" value={str(value).strip()}"
        line = ("  " * depth) + f"{role}: {name}{value_str}".strip()
        lines.append(line)
        size += len(line) + 1
        for c in reversed(node.get("children") or []):
            stack.append((c, depth + 1))
        if size > max_chars:
            break
    return "\n".join(lines)[:max_chars]


def launch(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(java_script_enabled=False)
    context.set_default_timeout(TIMEOUT_MS)
    context.set_default_navigation_timeout(TIMEOUT_MS)
    context.route("**/*", lambda route: route.abort())
    return browser, context


def html_to_axtree(context, html: str) -> dict:
    page = context.new_page()  # fresh page per row: no state build-up
    cdp = None
    try:
        page.set_content(sanitize_html(html), wait_until="domcontentloaded")
        cdp = context.new_cdp_session(page)
        nodes = cdp.send("Accessibility.getFullAXTree").get("nodes", [])
    finally:
        if cdp is not None:
            try:
                cdp.detach()
            except Exception:
                pass
        page.close()

    nodes_by_id = {}
    for node in nodes:
        nid = node.get("nodeId")
        if not nid:
            continue
        role = node.get("role") or {}
        name = node.get("name") or {}
        value = node.get("value")
        t = {"role": role.get("value", ""), "name": name.get("value", ""), "children": []}
        if t["role"] == "RootWebArea":
            t["role"] = "WebArea"
        if isinstance(value, dict) and "value" in value:
            t["value"] = value["value"]
        nodes_by_id[nid] = (node, t)

    roots = []
    for node, t in nodes_by_id.values():
        parent = nodes_by_id.get(node.get("parentId"))
        if parent is None:
            roots.append(t)
        else:
            parent[1]["children"].append(t)
    return roots[0] if roots else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="train", choices=VALID_SPLITS)
    ap.add_argument("--out_dir", default="data/mind2web_axtree")
    ap.add_argument("--html_field", default="cleaned_html", choices=["raw_html", "cleaned_html"])
    ap.add_argument("--restart_every", type=int, default=50)
    args = ap.parse_args()

    print(f"Loading {DATASET_NAME} split='{args.split}'...")
    ds = load_dataset(DATASET_NAME, split=args.split)

    json_col, text_col, failed = [], [], []

    with sync_playwright() as p:
        browser, context = launch(p)
        try:
            for i, ex in enumerate(tqdm(ds, desc=f"AXTree [{args.split}]")):
                if i and i % args.restart_every == 0:
                    context.close()
                    browser.close()
                    browser, context = launch(p)
                try:
                    snap = html_to_axtree(context, ex.get(args.html_field, ""))
                except Exception as e:
                    print(f"\nrow {i} failed ({type(e).__name__}); empty tree")
                    failed.append(i)
                    snap = {}
                    try:  # recover a possibly wedged browser
                        context.close()
                        browser.close()
                    except Exception:
                        pass
                    browser, context = launch(p)
                json_col.append(json.dumps(snap, ensure_ascii=False))
                text_col.append(flatten_axtree(snap))
        finally:
            try:
                context.close()
                browser.close()
            except Exception:
                pass

    ds = ds.add_column("axtree_json", json_col)
    ds = ds.add_column("axtree_text", text_col)
    save_path = f"{args.out_dir}/{args.split}"
    ds.save_to_disk(save_path)
    print(f"Saved: {save_path} | failed rows: {len(failed)} {failed[:20]}")


if __name__ == "__main__":
    main()