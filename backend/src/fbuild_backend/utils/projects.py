import re

REPO_SUFFIX_PATTERN = re.compile(r"\.git$")
SLUG_INVALID_PATTERN = re.compile(r"[^a-z0-9]+")


def derive_project_name(repo_url: str) -> str:
    cleaned = repo_url.rstrip("/")
    name = cleaned.split("/")[-1]
    return REPO_SUFFIX_PATTERN.sub("", name)


def slugify_project_name(name: str) -> str:
    normalized = SLUG_INVALID_PATTERN.sub("-", name.strip().lower()).strip("-")
    return normalized or "project"

