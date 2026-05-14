"""Orchestrator: Run all three training and packaging steps."""

from src.model import search_hyperparameters, train, create_artifacts


def main():
    """Execute all three steps: search, train, and package."""
    print("\n" + "#"*60)
    print("# COMPLETE TRAINING PIPELINE")
    print("#"*60)
    
    # Step 1: Search for best hyperparameters
    print("\n" + "="*60)
    print("RUNNING STEP 1: HYPERPARAMETER SEARCH")
    print("="*60)
    search_hyperparameters.main()
    
    # Step 2: Train with best hyperparameters
    print("\n" + "="*60)
    print("RUNNING STEP 2: TRAIN WITH BEST HYPERPARAMETERS")
    print("="*60)
    train.main()
    
    # Step 3: Create artifacts
    print("\n" + "="*60)
    print("RUNNING STEP 3: CREATE ARTIFACTS")
    print("="*60)
    create_artifacts.main()
    
    print("\n" + "#"*60)
    print("# PIPELINE COMPLETE")
    print("#"*60)


if __name__ == "__main__":
    main()

