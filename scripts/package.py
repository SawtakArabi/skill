"""Build the Claude upload ZIP from a fixed list of public skill files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
skill = root / "skills/arabic-voiceover"
files = ["SKILL.md", "requirements.txt", "scripts/generate.py", "references/video-workflow.md", "agents/openai.yaml"]
destination = root / "dist/arabic-voiceover.zip"
destination.parent.mkdir(exist_ok=True)
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(skill / name, f"arabic-voiceover/{name}")
    archive.write(root / "LICENSE", "arabic-voiceover/LICENSE")
print(destination)
