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
        skills[path.stem] = parse_skill(path, text)  # path.stem = skill name
    return skills

# helper function for load library, turns one file into a dict
def parse_skill(path, text):
    parsed_skill = {}
    split_text = text.split("---", maxsplit=2)

    # reject the file if there are fewer than 2 --- lines -> no header is closed
    # or something comes before the first ---
    if split_text[0].strip() != "" or len(split_text) < 3:
        raise ValueError(f"Error, {path} missing or misplaced --- header")

    # split_text[0] = empty text before first ---
    # split_text[1] = header
    # split_text[2] = body
    before, header, body = split_text
    for line in header.splitlines():
        if line.strip() == "":
            continue
        if ":" not in line:
            raise ValueError(f"Error with line: {line} in file:{path}")
        key, val = line.split(":", 1)
        parsed_skill[key.strip()] = val.strip()

    raw = parsed_skill.get("sources", "")
    parsed_skill["sources"] = [s.strip() for s in raw.split(",") if s.strip()]

    parsed_skill["name"] = path.stem
    parsed_skill["body"] = body.strip()
    return parsed_skill

# turn dict into one string for slicey's custom instruction
def render(skills):
    skill_as_prompt = []
    prompt_intro = "Skills for working in 3D Slicer. Use the ones that fit the task."
    if not skills:
        return ""
    for skill in skills.values():
        prompt = f"## {skill['name']}\n{skill['description']}\n\n{skill['body']}"
        skill_as_prompt.append(prompt)

    skill_as_prompt.insert(0, prompt_intro)
    instruction = "\n\n".join(skill_as_prompt)
    return instruction


def save_skill(skill):
    path = SKILLS_PATH / f"{skill['name']}.md"
    SKILLS_PATH.mkdir(parents=True, exist_ok=True)
    sources = ", ".join(skill['sources'])
    skill_text = f"---\ndescription: {skill['description']}\ncategory: {skill['category']}\nsources: {sources}\n---\n{skill['body']}\n"
    path.write_text(skill_text, encoding="utf-8")
    return path

if __name__ == "__main__":
    print(render(load_library()))
