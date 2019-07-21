"""Pre-defined tag-to-url patterns."""
import re

# These systems have easy-to-identify patterns for their Ticket IDs but each user will
# have a unique URL for their system. As such, while `url_template` is needed to work
# with each system, they are not provided below.
JIRA = {"pattern": re.compile("^([A-Z][A-Z]+-[0-9]+)$")}
SNOW = {"pattern": re.compile("(^[A-Z][A-Z]+[0-9]+)$")}
VersionOne = {"pattern": re.compile("(^[A-Z]-[0-9]+)$")}
