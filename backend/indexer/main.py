from typing import Dict, Any
import functions_framework
from google.cloud import storage
from processors.block_processor import BlockProcessor
from decoders import get_decoders  # factory to initialize decoders
from mappers import get_mappers    # factory to initialize mappers
from config import load_config

@functions_framework.cloud_event
def process_new_block(cloud_event: Dict[str, Any]) -> None:
    """Entry point for Cloud Run, triggered by Cloud Storage events"""
    
    # Get file info from cloud event
    bucket = cloud_event.data["bucket"]
    name = cloud_event.data["name"]
    
    # Initialize components
    config = load_config()
    decoders = get_decoders(config.contracts)
    mappers = get_mappers()
    processor = BlockProcessor(decoders, mappers)
    
    # Process the block
    processor.process_block(bucket, name)
