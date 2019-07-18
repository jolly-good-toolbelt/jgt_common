"""Pre-defined tag-to-url patterns."""
import re

JIRA = {
    "pattern": re.compile("^([A-Z][A-Z]+-[0-9]+)$"),
    "url_template": "https://jira.rax.io/browse/{}",
}
SNOW = {
    "pattern": re.compile("(^[A-Z][A-Z]+[0-9]+)$"),
    "url_template": "https://rackspace.service-now.com/rm_story.do"
    "?sysparm_query=number={}&sysparm_view=scrum",
}
VersionOne = {"pattern": re.compile("(^[A-Z]-[0-9]+)$")}
