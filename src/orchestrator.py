from utils.constants import PREDEFINED_SEARCHES
from utils.search_utils import google_search

if __name__ == "__main__":
    term = PREDEFINED_SEARCHES[0]
    print(f"Query: {term}\n")

    results = google_search(term)

    print(f"Found {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['url']}")
        print()
