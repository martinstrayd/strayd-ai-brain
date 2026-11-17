from datetime import date
from pathlib import Path
import subprocess
import zipfile

# Repository folders
ROOT = Path.cwd()
SOCIAL = ROOT / "social-posts"
DAILY = SOCIAL / "daily"
WEEKLY = SOCIAL / "weekly"
OUT = ROOT / "exports"

OUT.mkdir(parents=True, exist_ok=True)


def get_markdown_files(folder):
    if not folder.is_dir():
        raise FileNotFoundError(
            f"Required folder does not exist: {folder}"
        )

    today_str = date.today().isoformat()  # Today's date: "2026-11-17"
    
    files = []
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".md":
            # Extract date from filename (assuming format starts with YYYY-MM-DD)
            filename_date = p.name[:10]
            # Keep ONLY today and future dates (the week ahead)
            if filename_date >= today_str:
                files.append(p)

    # Sort chronologically so today comes first, followed by the rest of the week ahead
    files = sorted(files)

    if not files:
        raise FileNotFoundError(
            f"No Markdown files found for today or upcoming dates in {folder}"
        )

    return files


def create_zip(folder, output_file, filtered_files=None):
    with zipfile.ZipFile(
        output_file, "w", zipfile.ZIP_DEFLATED
    ) as archive:
        target_files = filtered_files if filtered_files is not None else sorted(folder.rglob("*"), reverse=True)
        for file in target_files:
            if file.is_file():
                archive.write(
                    file,
                    Path(folder.name) / file.relative_to(folder)
                )

    print(f"Created {output_file.name}")


def combine_markdown(files, folder, title):
    sections = [f"# {title} Social Posts (Week Ahead starting {date.today().isoformat()})\n"]

    for file in files:
        relative_name = file.relative_to(folder)

        sections.append(
            f"\n---\n\n# {relative_name.as_posix()}\n"
        )

        content = file.read_text(
            encoding="utf-8-sig",
            errors="replace"
        ).strip()

        sections.append(content)

    return "\n\n".join(sections) + "\n"


def create_pdf(markdown_file, pdf_file):
    subprocess.run(
        [
            "pandoc",
            str(markdown_file),
            "--from=markdown",
            "--standalone",
            "--output",
            str(pdf_file),
            "--pdf-engine=xelatex",
            "--variable=mainfont:DejaVu Sans",
            "--variable=geometry:margin=18mm",
        ],
        check=True,
    )

    print(f"Created {pdf_file.name}")


def export_folder(folder, label):
    files = get_markdown_files(folder)

    # ZIP containing individual Markdown files for the active week ahead
    create_zip(folder, OUT / f"{label}.zip", filtered_files=files)

    # Combined Markdown document starting from today
    combined = combine_markdown(files, folder, label)
    markdown_file = OUT / f"{label}.md"

    markdown_file.write_text(
        combined,
        encoding="utf-8"
    )

    print(f"Created {markdown_file.name}")

    # Readable PDF generated from the combined Markdown
    create_pdf(
        markdown_file,
        OUT / f"{label}.pdf"
    )

    return files


def main():
    daily_files = export_folder(DAILY, "DAILY")
    weekly_files = export_folder(WEEKLY, "WEEKLY")

    # Full Archive ZIP containing all historical files (preserved completely)
    archive_zip = OUT / "FULL_ARCHIVE.zip"
    with zipfile.ZipFile(
        archive_zip, "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for folder in (DAILY, WEEKLY):
            for file in sorted(folder.rglob("*")):
                if file.is_file():
                    archive.write(
                        file,
                        file.relative_to(SOCIAL)
                    )

    print(f"Created {archive_zip.name}")
    print("\nAll exports completed successfully.")

    for file in sorted(OUT.iterdir()):
        if file.is_file():
            print(
                f"  {file.name}: "
                f"{file.stat().st_size:,} bytes"
            )


if __name__ == "__main__":
    main()
