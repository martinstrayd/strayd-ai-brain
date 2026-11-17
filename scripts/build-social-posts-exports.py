from datetime import date
# ... existing imports ...

def get_markdown_files(folder):
    if not folder.is_dir():
        raise FileNotFoundError(
            f"Required folder does not exist: {folder}"
        )

    today_str = date.today().isoformat()  # Gets "2026-11-17"
    
    files = []
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".md":
            # Extract date from filename (assumes format starts with YYYY-MM-DD)
            filename_date = p.name[:10]
            # Keep only today and future dates (the week ahead)
            if filename_date >= today_str:
                files.append(p)

    # Sort chronologically so today comes first, followed by the rest of the week
    files = sorted(files)

    if not files:
        raise FileNotFoundError(
            f"No Markdown files found for today or upcoming dates in {folder}"
        )

    return files
