import subprocess
import sys
from datetime import datetime


def run_step(name, command):
    print(f"\n========== {name} ==========")
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"FAILED: {name}")
        sys.exit(1)

    print(f"DONE: {name}")


if __name__ == "__main__":
    print("Starting Airbus Intelligence Pipeline")
    print("Time:", datetime.now())

    run_step(
        "Data Scraping",
        "python DataScraping/run_collection.py"
    )

    run_step(
        "Data Cleaning",
        "python DataCleaning/data_clean.py"
    )

    run_step(
        "Embedding + ChromaDB Update",
        "python VectorDB/store_to_chroma.py"
    )

    print("\nPipeline completed successfully.")