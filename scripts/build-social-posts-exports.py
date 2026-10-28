
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

    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() == ".md"
    )

    if not files:
        raise FileNotFoundError(
            f"No Markdown files found in {folder}"
        )

    return files


def create_zip(folder, output_file):
    with zipfile.ZipFile(
        output_file, "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                archive.write(
                    file,
                    Path(folder.name) / file.relative_to(folder)
                )

    print(f"Created {output_file.name}")


def combine_markdown(files, folder, title):
    sections = [f"# {title} Social Posts\n"]

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

    # ZIP containing the original individual Markdown files.
    create_zip(folder, OUT / f"{label}.zip")

    # Combined Markdown document.
    combined = combine_markdown(files, folder, label)
    markdown_file = OUT / f"{label}.md"

    markdown_file.write_text(
        combined,
        encoding="utf-8"
    )

    print(f"Created {markdown_file.name}")

    # Readable PDF generated from the combined Markdown.
    create_pdf(
        markdown_file,
        OUT / f"{label}.pdf"
    )

    return files


def main():
    daily_files = export_folder(DAILY, "DAILY")
    weekly_files = export_folder(WEEKLY, "WEEKLY")

    # One ZIP containing both original folder structures.
    all_markdown = OUT / "ALL_MARKDOWN.zip"

    with zipfile.ZipFile(
        all_markdown, "w", zipfile.ZIP_DEFLATED
    ) as archive:

        for folder in (DAILY, WEEKLY):
            for file in sorted(folder.rglob("*")):
                if file.is_file():
                    archive.write(
                        file,
                        file.relative_to(SOCIAL)
                    )

    print(f"Created {all_markdown.name}")
    print("\nAll exports completed successfully.")

    for file in sorted(OUT.iterdir()):
        if file.is_file():
            print(
                f"  {file.name}: "
                f"{file.stat().st_size:,} bytes"
            )


if __name__ == "__main__":
    main()
