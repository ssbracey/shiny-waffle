"""Search TMDb for movies and TV shows.

Setup:
    conda install requests
    export TMDB_API_TOKEN="your-tmdb-read-access-token"

Examples:
    python shiny-waffle/tmdb-text.py "The Matrix"
    python shiny-waffle/tmdb-text.py "Severance" --type tv
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import requests


BASE_URL = "https://api.themoviedb.org/3"


def get_token() -> str:
    token = os.getenv("TMDB_API_TOKEN")
    if not token:
        raise ValueError(
            "Missing TMDB_API_TOKEN. Export your TMDb read access token before running the script."
        )
    return token


def make_request(path: str, *, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Accept": "application/json",
        },
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def search_titles(query: str, *, media_type: str, page: int) -> dict[str, Any]:
    endpoint = "/search/multi" if media_type == "multi" else f"/search/{media_type}"
    return make_request(
        endpoint,
        params={
            "query": query,
            "page": page,
            "include_adult": "false",
            "language": "en-US",
        },
    )


def format_result(item: dict[str, Any]) -> str:
    media_type = item.get("media_type", "movie")
    title = item.get("title") or item.get("name") or "Untitled"
    date = item.get("release_date") or item.get("first_air_date") or "unknown date"
    rating = item.get("vote_average")
    overview = (item.get("overview") or "").strip()

    parts = [f"{title} [{media_type}] ({date})"]
    if rating is not None:
        parts.append(f"rating={rating}")
    if overview:
        parts.append(overview[:140] + ("..." if len(overview) > 140 else ""))
    return " | ".join(parts)


def print_results(payload: dict[str, Any]) -> None:
    results = payload.get("results", [])
    if not results:
        print("No matches found.")
        return

    for index, item in enumerate(results, start=1):
        print(f"{index}. {format_result(item)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search TMDb for titles.")
    parser.add_argument("query", help="Movie or TV show title to search for")
    parser.add_argument(
        "--type",
        choices=["multi", "movie", "tv"],
        default="multi",
        help="Type of TMDb search to run",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number to request",
    )
    args = parser.parse_args()

    try:
        payload = search_titles(args.query, media_type=args.type, page=args.page)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc.response.status_code} {exc.response.reason}", file=sys.stderr)
        if exc.response.text:
            print(exc.response.text, file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    print_results(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
