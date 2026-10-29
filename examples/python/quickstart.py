"""List the projects your key reads, and print each one's headline numbers.

    export LANESRA_API_KEY=lns_live_your_key_here
    python quickstart.py
"""

import sys

from lanesra import Lanesra, LanesraError, LanesraToolError


def fmt(value, suffix=""):
    """A metric as text. None means it could not be computed, which is not the same as zero."""
    return "n/a" if value is None else f"{value}{suffix}"


def main():
    client = Lanesra()

    listing = client.call("list_projects")
    projects = listing["projects"]
    if not projects:
        print(listing.get("note", "This key reads no projects."))
        return

    for project in projects:
        slug = project["slug"]
        try:
            overview = client.call("get_visibility_overview", project=slug)
        except LanesraToolError as e:
            # For example a project whose first capture has not finished yet.
            print(f"{slug}: {e}")
            continue

        own = overview.get("own") or {}
        print(f"{overview['brand']} ({slug})")
        print(f"  captured        {overview['capturedAt'] or 'not yet'}, over {overview['answers']} answers")
        print(f"  engines         {', '.join(overview['engines'])}")
        print(f"  score           {fmt(own.get('score'))}")
        print(f"  visibility      {fmt(own.get('visibility'), '%')}")
        print(f"  share of voice  {fmt(own.get('shareOfVoice'), '%')}")
        print(f"  avg position    {fmt(own.get('avgPosition'))}")
        print(f"  rank            {fmt(overview.get('rankAmongTracked'))} of {overview.get('trackedBrands')}")
        if overview.get("note"):
            print(f"  note            {overview['note']}")


if __name__ == "__main__":
    try:
        main()
    except LanesraError as e:
        sys.exit(f"Lanesra: {e}")
