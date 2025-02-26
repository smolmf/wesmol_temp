import os
import sys
import argparse
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# Import from indexer package
from indexer.indexer.env import env
from indexer.indexer.processing.batch import BatchProcessor
from indexer.indexer.database.models.status import ProcessingStatus
from indexer.indexer.utils.logging import setup_logger

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generic batch processor for WESMOL Indexer")

    # Parse local-db flag early
    parser.add_argument("--local-db", action="store_true",
                       help="Use local SQLite database instead of PostgreSQL")
    args, remaining_argv = parser.parse_known_args()
    
    # Set SQLite environment variable immediately if flag is present
    if args.local_db:
        os.environ["DB_USE_SQLITE"] = "True"
        print("Using local SQLite database")
    
    parser = argparse.ArgumentParser(description="Generic batch processor for WESMOL Indexer")

    # Storage options
    parser.add_argument("--storage", choices=["gcs", "local"], default="local",
                       help="Where to store decoded blocks (default: local)")
    parser.add_argument("--local-dir", type=str, default=None,
                       help="Local directory for storage (default: data_dir from env)")
    parser.add_argument("--local-db", action="store_true",
                       help="Use local SQLite database instead of PostgreSQL")
    
    # Block selection methods (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", type=int, metavar="N",
                      help="Sample N random blocks")
    group.add_argument("--block-numbers", type=int, nargs="+",
                      help="Process specific block numbers")
    group.add_argument("--status", choices=["pending", "valid", "invalid", "processing"],
                      help="Process blocks with specific status")
    group.add_argument("--file", type=str,
                      help="File with list of block numbers or paths")
    group.add_argument("--range", type=int, nargs=2, metavar=("MIN", "MAX"),
                      help="Process blocks in range MIN to MAX (inclusive)")
    
    # Other options
    parser.add_argument("--prefix", type=str, default=None,
                      help="GCS prefix for blocks (default: from env)")
    parser.add_argument("--filter-status", choices=["pending", "valid", "invalid", "processing"],
                      help="Filter blocks in range by status")
    parser.add_argument("--limit", type=int, default=100,
                      help="Maximum number of blocks to process for --status (default: 100)")
    parser.add_argument("--batch-size", type=int, default=None,
                      help="Process blocks in batches of this size")
    parser.add_argument("--force", action="store_true",
                      help="Force reprocessing even if decoded blocks already exist")
    parser.add_argument("--sync", action="store_true", dest="sync",
                      help="Sync GCS objects to database before querying (default)")
    parser.add_argument("--no-sync", action="store_false", dest="sync",
                      help="Don't sync GCS objects to database before querying")
    parser.add_argument("--output", type=str, default=None,
                      help="Output file for results (default: auto-generated)")
    parser.set_defaults(sync=True)
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logger()
    
    # Verify database connection
    if not env.verify_database():
        logger.error("Database verification failed. Cannot proceed.")
        sys.exit(1)
    
    # Initialize batch processor
    batch_processor = BatchProcessor(
        storage_type=args.storage,
        local_dir=args.local_dir,
        use_local_db=args.local_db
    )
    
    # Map status string to enum
    status_map = {
        "pending": ProcessingStatus.PENDING,
        "valid": ProcessingStatus.VALID,
        "invalid": ProcessingStatus.INVALID,
        "processing": ProcessingStatus.PROCESSING
    }
    
    # Determine which blocks to process
    if args.sample:
        block_paths = batch_processor.sample_blocks(args.sample, args.prefix, sync_first=args.sync)
    elif args.block_numbers:
        block_paths = batch_processor.get_blocks_by_block_numbers(args.block_numbers, args.prefix, sync_first=args.sync)
    elif args.status:
        block_paths = batch_processor.get_blocks_by_status(status_map[args.status], args.limit, sync_first=args.sync)
    elif args.file:
        # Read from file - support both block numbers and full paths
        with open(args.file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # Determine if lines are block numbers or paths
        if all(line.isdigit() for line in lines):
            # Block numbers
            block_numbers = [int(line) for line in lines]
            block_paths = batch_processor.get_blocks_by_block_numbers(block_numbers, args.prefix, sync_first=args.sync)
        else:
            # Assume full paths
            block_paths = lines
    elif args.range:
        min_block, max_block = args.range
        filter_status = status_map.get(args.filter_status) if args.filter_status else None
        block_paths = batch_processor.get_blocks_in_range(min_block, max_block, filter_status, args.prefix, sync_first=args.sync)
    
    # Process blocks
    if not block_paths:
        logger.warning("No blocks to process. Exiting.")
        return
    
    logger.info(f"Will process {len(block_paths)} blocks with {args.storage} storage")
    
    # Process blocks
    results = batch_processor.process_blocks(
        block_paths,
        batch_size=args.batch_size,
        force=args.force,
        sync_first=args.sync
    )
    
    # Save results
    batch_processor.save_results(results, args.output)


if __name__ == "__main__":
    main()