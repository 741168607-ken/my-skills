"""
build_video.py - Picture book video builder

Usage:
  python build_video.py --pdf <pdf_path> --audio <audio_path> --output <output_mp4>

Steps:
  1. Extract PDF pages as PNG
  2. Map pages to spreads (skip cover/copyright/glossary)
  3. Build video with audio
  4. Page timing can be adjusted via --timings JSON
"""
import argparse
import json
import os
import sys

def extract_pdf_pages(pdf_path, out_dir, zoom=2, page_nums=None):
    """Extract selected PDF pages as PNG using PyMuPDF.
    page_nums: optional list of 1-based page numbers; default all pages."""
    import pymupdf
    os.makedirs(out_dir, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    pages = []
    mat = pymupdf.Matrix(zoom, zoom)
    for i, page in enumerate(doc):
        if page_nums and (i + 1) not in page_nums:
            continue
        pix = page.get_pixmap(matrix=mat)
        path = os.path.join(out_dir, f"page_{i+1:03d}.png")
        pix.save(path)
        pages.append(path)
        print(f"  Page {i+1}: {pix.width}x{pix.height}")
    doc.close()
    return pages


def build_video(page_images, page_durations, audio_path, output_path,
                canvas_size=(1152, 720), fps=30):
    """Build video from page images + audio with specified durations per page."""
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    from PIL import Image
    import numpy as np

    clips = []
    for img_path, dur in zip(page_images, page_durations):
        # Fit image to canvas
        img = Image.open(img_path).convert("RGB")
        img_ratio = img.width / img.height
        canvas_ratio = canvas_size[0] / canvas_size[1]
        if img_ratio > canvas_ratio:
            new_w = canvas_size[0]
            new_h = int(canvas_size[0] / img_ratio)
        else:
            new_h = canvas_size[1]
            new_w = int(canvas_size[1] * img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGB", canvas_size, (255, 255, 255))
        ox = (canvas_size[0] - new_w) // 2
        oy = (canvas_size[1] - new_h) // 2
        canvas.paste(img, (ox, oy))
        tmp = img_path + ".canvas.png"
        canvas.save(tmp)
        clip = ImageClip(tmp).with_duration(dur)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path)
    video = video.with_audio(audio)
    video.write_videofile(output_path, fps=fps, codec="libx264",
                          audio_codec="aac", audio_bitrate="192k",
                          preset="medium", threads=4)
    audio.close()
    for c in clips:
        c.close()


def main():
    parser = argparse.ArgumentParser(description="Build picture book video")
    parser.add_argument("--pdf", required=True, help="PDF file path")
    parser.add_argument("--audio", required=True, help="Audio file path (mp3/wav)")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--timings", help="JSON file with page durations: [dur1, dur2, ...]")
    parser.add_argument("--pages", help="Comma-separated 1-based page numbers to include, e.g. '1,4,5,6'")
    args = parser.parse_args()

    work_dir = os.path.dirname(args.output) or "."
    pages_dir = os.path.join(work_dir, "pages_extracted")

    print(f"[1/3] Extracting PDF pages...")
    page_nums = None
    if args.pages:
        page_nums = [int(x) for x in args.pages.split(",")]
    pages = extract_pdf_pages(args.pdf, pages_dir, page_nums=page_nums)
    print(f"  Total pages: {len(pages)}")

    print(f"[2/3] Loading timings...")
    if args.timings and os.path.exists(args.timings):
        with open(args.timings) as f:
            durations = json.load(f)
    else:
        # Default: equal distribution
        print("  No timings file, using equal duration per page")
        from moviepy import AudioFileClip
        audio = AudioFileClip(args.audio)
        dur = audio.duration / len(pages)
        audio.close()
        durations = [dur] * len(pages)
    print(f"  Total duration: {sum(durations):.1f}s")

    print(f"[3/3] Building video...")
    build_video(pages, durations, args.audio, args.output)
    print(f"Done: {args.output}")


if __name__ == "__main__":
    main()
