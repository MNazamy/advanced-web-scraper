from utils.constants import PREDEFINED_SEARCHES, SEARCH_ENGINES
from utils.search_utils import search
from utils.db_utils import start_run, complete_run, insert_results, start_batch_run, complete_batch_run

if __name__ == "__main__":
    term = PREDEFINED_SEARCHES[0]
    print(f"Query: {term}\n")

    batch_id = start_batch_run()

    for engine in SEARCH_ENGINES:

        run_id = start_run(term, engine, batch_id)

        results = search(term, engine, run_id)
        print(f"\nFound {len(results)} results:\n")

        insert_results(run_id, results)
        complete_run(run_id)

    complete_batch_run(batch_id)