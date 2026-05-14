from utils.constants import PREDEFINED_SEARCHES
from utils.search_utils import google_search
from utils.db_utils import start_run, complete_run, insert_results

if __name__ == "__main__":
    term = PREDEFINED_SEARCHES[0]
    print(f"Query: {term}\n")

    run_id = start_run(term, "google")

    results = google_search(term)
    print(f"\nFound {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['url']}")
        print()

    insert_results(run_id, results)
    complete_run(run_id)
