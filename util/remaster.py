import re

# Matches common "Remaster" / "Remastered" suffixes appended to song titles.
# Examples handled:
#   "Song Title - 2020 Remaster"
#   "Song Title (2020 Remaster)"
#   "Song Title (Remastered)"
#   "Song Title - Remastered 2020"
#   "Song Title (Remastered 2020 Version)"
_REMASTER_RE = re.compile(
    r"""
    [\s\-–]+            # separator: whitespace and/or dash
    [\(\[]?             # optional opening bracket
    (?:\d{4}\s+)?       # optional year before keyword
    Remaster(?:ed)?     # "Remaster" or "Remastered"
    (?:\s+\d{4})?       # optional year after keyword
    (?:\s+Version)?     # optional trailing "Version"
    [\)\]]?             # optional closing bracket
    \s*$                # up to end of string
    """,
    re.IGNORECASE | re.VERBOSE,
)


def remove_remaster(name: str) -> str:
    """Return *name* with any remaster annotation stripped from the end."""
    return _REMASTER_RE.sub("", name).strip()
