"""Pre-defined tag-to-url patterns."""
import re

JIRA = {"pattern": re.compile("^([A-Z][A-Z]+-[0-9]+)$")}
SNOW = {"pattern": re.compile("(^[A-Z][A-Z]+[0-9]+)$")}
VersionOne = {"pattern": re.compile("(^[A-Z]-[0-9]+)$")}
