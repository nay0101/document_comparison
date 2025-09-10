#!/usr/bin/env python3
from pathlib import Path
from typing import Optional
import argparse
try:
    from PyPDF2 import PdfReader, PdfWriter
except Exception:
    # fallback: pypdf package has same interfaces
    from pypdf import PdfReader, PdfWriter

def split_pdf(input_pdf: str, out_dir: str, pages_per_chunk: int = 1) -> None:
    outdir = Path(out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    for start in range(0, total_pages, pages_per_chunk):
        writer = PdfWriter()
        end = min(start + pages_per_chunk, total_pages)
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        out_path = outdir / f"chunk_{start+1:04d}_to_{end:04d}.pdf"
        with out_path.open("wb") as f:
            writer.write(f)
        print(f"Saved {out_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Input PDF path")
    ap.add_argument("--out", default="chunks", help="Output directory for chunks")
    ap.add_argument("--pages-per-chunk", type=int, default=1, help="Pages per split PDF")
    args = ap.parse_args()
    split_pdf(args.pdf, args.out, args.pages_per_chunk)

if __name__ == "__main__":
    main()
