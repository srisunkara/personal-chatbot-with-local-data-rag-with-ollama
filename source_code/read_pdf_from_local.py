import argparse
import datetime
import json
import os
import re
from typing import Dict, Iterable, Tuple

from dotenv import load_dotenv

load_dotenv()

try:
    from pypdf import PdfReader  # lightweight and widely used
except Exception:  # pragma: no cover - optional dependency handling
    PdfReader = None  # type: ignore


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".rtf",
    ".csv",
    ".tsv",
    ".json",
    ".log",
}


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters and strip ends."""
    # Replace Windows newlines, tabs, and multiple spaces/newlines with single spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_pdf(path: str) -> str:
    if PdfReader is None:
        raise RuntimeError(
            "pypdf is not installed. Please install dependencies (see requirements.txt)."
        )
    try:
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
        return normalize_whitespace("\n".join(parts))
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF '{path}': {e}")


def read_text_file(path: str) -> str:
    # Try UTF-8 first, then fall back to latin-1 to avoid crashes on odd encodings
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(path, "r", encoding=encoding, errors="replace") as f:
                return normalize_whitespace(f.read())
        except Exception:
            continue
    raise RuntimeError(f"Failed to read text file '{path}' with common encodings")


def iter_files(input_dir: str) -> Iterable[Tuple[str, str]]:
    """Yield (absolute_path, extension) for supported files within input_dir recursively."""
    for root, _dirs, files in os.walk(input_dir):
        for name in files:
            # Skip our output file if scanning the same directory
            if name == os.getenv("DATASET_STORAGE_FILE_NAME"):
                continue
            abs_path = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            if ext == ".pdf" or ext in TEXT_EXTENSIONS:
                yield abs_path, ext


def build_corpus(input_dir: str, use_basename_keys: bool = True) -> Dict[str, str]:
    """
    Build a mapping from file name to extracted text content.

    - If use_basename_keys is True, keys are just the file's base name.
    - Otherwise, keys are paths relative to the input_dir (using forward slashes).
    """
    mapping: Dict[str, str] = {}
    input_dir_abs = os.path.abspath(input_dir)

    for abs_path, ext in iter_files(input_dir):
        try:
            if ext == ".pdf":
                content = read_pdf(abs_path)
            else:
                content = read_text_file(abs_path)
        except Exception as e:
            # Log to console and skip file on error
            print(f"[WARN] Skipping '{abs_path}': {e}")
            continue

        if not content:
            print(f"[INFO] Skipping empty file: {abs_path}")
            continue

        if use_basename_keys:
            key = os.path.basename(abs_path)
        else:
            rel = os.path.relpath(abs_path, input_dir_abs)
            key = rel.replace(os.sep, "/")

        mapping[key] = content

    return mapping


def save_json(mapping: Dict[str, str], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # if file exists, rename the existing with the current timestamp and .txt at the end
    if os.path.exists(output_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{output_path}.{timestamp}.txt"
        os.rename(output_path, backup_path)
        print(f"Renamed existing file to {backup_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(mapping)} items to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Read PDFs and text files from a folder and write a JSON {file_name: content} "
            "mapping to datasets/data.txt."
        )
    )
    in_data_folder = '/Users/srini/Library/CloudStorage/OneDrive-Personal/Munny/Private Company Inv'
    parser.add_argument(
        "--input-dir",
        default=in_data_folder,
        help="Directory to scan for input files (default: datasets)",
    )
    # Determine default output path from environment with safe fallbacks
    default_output = os.path.join("../datasets", "data.txt")
    folder = os.getenv("DATASET_STORAGE_FOLDER")
    file_name = os.getenv("DATASET_STORAGE_FILE_NAME")
    if folder:
        if not file_name:
            file_name = "data.txt"
        default_output = os.path.join(folder, file_name)

    parser.add_argument(
        "--output",
        default=default_output,
        help="Output JSON file path (default: datasets/data.txt)",
    )
    parser.add_argument(
        "--relative-keys",
        action="store_true",
        help="Use paths relative to input-dir as keys instead of just base names.",
    )

    args = parser.parse_args()

    corpus = build_corpus(args.input_dir, use_basename_keys=not args.relative_keys)
    save_json(corpus, args.output)


if __name__ == "__main__":
    main()
