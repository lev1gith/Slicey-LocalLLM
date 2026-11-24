from pathlib import Path

SKILLS_PATH = Path(__file__).resolve().parent.parent / "skills" / "library"

# load and save skill files
# render library into small text that goes into system prompt
# report token count and version


# read all skill files and return them in a fixed order
def load_library():
    skills = {}
    for path in sorted(SKILLS_PATH.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        skill_name = path.stem
        skills[skill_name] = text
    return skills
