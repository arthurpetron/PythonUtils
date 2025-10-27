#!/usr/bin/env python3
import argparse
from pathlib import Path

SEP = "━━━━━━"

def sep_line(depth: int) -> str:
    return f"{'┃'*depth}┣{SEP}\n"

def header(depth: int, kind: str, name: str) -> str:
    return f"{'┃'*depth}┣ {kind}: {name}\n"

def read_utf8_strict(fp: Path) -> str | None:
    try:
        data = fp.read_bytes()
        if b"\x00" in data:  # quick binary check
            return None
        # strict decode: any invalid byte -> UnicodeDecodeError
        return data.decode("utf-8")
    except Exception:
        return None

def dump_file(fp: Path, out, depth: int, text: str):
    out.write(sep_line(depth))
    out.write(header(depth, "File", fp.name))
    out.write(sep_line(depth))
    prefix = "┃" * (depth + 1)
    for line in text.splitlines():
        out.write(f"{prefix}{line}\n")

def walk_dir(dirpath: Path, out, depth: int, skip_path: Path):
    entries = list(dirpath.iterdir())
    files = sorted([e for e in entries if e.is_file()], key=lambda p: p.name.lower())
    dirs  = sorted([e for e in entries if e.is_dir()],  key=lambda p: p.name.lower())

    for f in files:
        if f.resolve() == skip_path:
            continue
        # Skip macOS resource forks explicitly
        if f.name.startswith("._"):
            continue
        if f.name == "__MACOSX":
            continue
        if f.name.startswith("."):
            continue
        if f.name.endswith("__"):
            continue
        text = read_utf8_strict(f)
        if text is not None:
            dump_file(f, out, depth, text)
        # else: silently skip non-UTF-8/binary files

    for d in dirs:
        if d.name == "__MACOSX":  # common binary sidecar dir on macOS zips
            continue
        out.write(sep_line(depth))
        out.write(header(depth, "Directory", d.name))
        walk_dir(d, out, depth + 1, skip_path)

def main():
    ap = argparse.ArgumentParser(
        description="Flatten a directory tree into a single UTF-8 .txt with tree-style headers and file contents. Skips non-UTF-8 files."
    )
    ap.add_argument("input_dir", type=Path, help="Directory to read")
    ap.add_argument("output_txt", type=Path, help="Path to the output .txt file")
    args = ap.parse_args()

    in_dir = args.input_dir.resolve()
    out_txt = args.output_txt.resolve()

    if not in_dir.is_dir():
        raise SystemExit(f"Input is not a directory: {in_dir}")

    out_txt.parent.mkdir(parents=True, exist_ok=True)

    with out_txt.open("w", encoding="utf-8", newline="\n") as out:
        out.write(f"Directory: {in_dir.name}\n")
        walk_dir(in_dir, out, depth=0, skip_path=out_txt)

if __name__ == "__main__":
    main()