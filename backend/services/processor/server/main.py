# backend/services/processor/server/main.py
import os
import base64
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import functions_framework

# Load environment variables
load_dotenv()
from indexer.indexer.env import env

# Import after loading environment variables
from indexer.indexer.database.operations.session import ConnectionManager
from indexer.indexer.database.operations.manager import DatabaseManager
from indexer.indexer.database.models.status import ProcessingStatus, BlockProcess
from indexer.indexer.processing.validator import BlockValidator
from indexer.indexer.processing.processor import BlockProcessor
from indexer.indexer.decoders.block import BlockDecoder
from indexer.indexer.storage.base import GCSBaseHandler
from indexer.indexer.storage.handler import BlockHandler
# Initialize Flask app
app = Flask(__name__)

# Initialize services
db_manager = DatabaseManager(env.get_db_url())
status_tracker = DBValidator(db_manager)

# Initialize GCS handler
gcs_handler = GCSHandler(
    bucket_name=env.get_bucket_name(),
    credentials_path=os.getenv("GCS_CREDENTIALS_PATH")
)

# Initialize individual components
validator = BlockValidator()
decoder = BlockDecoder()
storage = BlockStorage(gcs_handler, 
                      raw_prefix=os.getenv("GCS_RAW_PREFIX", "raw/"),
                      decoded_prefix=os.getenv("GCS_DECODED_PREFIX", "decoded/"))

# Initialize block processor
block_processor = BlockProcessor(
    gcs_handler=gcs_handler,
    status_tracker=status_tracker,
    validator=validator,
    decoder=decoder,
    storage=storage
)

@app.route("/", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy", "service": "block-processor"})

@app.route("/pubsub", methods=["POST"])
def handle_pubsub():
    """Handle Pub/Sub push notifications for new blocks."""
    # Get the message
    envelope = request.get_json()
    if not envelope:
        return "No Pub/Sub message received", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        return "Invalid Pub/Sub message format", 400

    # Extract data
    pubsub_message = envelope["message"]
    
    if not pubsub_message.get("data"):
        return "No data in message", 400
    
    # Decode the data
    data = json.loads(base64.b64decode(pubsub_message["data"]).decode("utf-8"))
    
    # Extract GCS path (depends on your Pub/Sub message format)
    # For GCS notifications, the path is usually in 'name'
    gcs_path = data.get("name")
    if not gcs_path:
        return "No GCS path in message", 400
    
    try:
        # Process the block
        success, result_info = block_processor.process_block(gcs_path)
        
        # Return detailed result info
        response = {
            "status": "success" if success else "failure",
            "path": gcs_path,
            "details": result_info
        }
        
        # Always return 200 to acknowledge receipt to Pub/Sub
        return jsonify(response), 200
    
    except Exception as e:
        # Log the error but return 200 to acknowledge receipt
        print(f"Error processing {gcs_path}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 200

@app.route("/status", methods=["GET"])
def get_processing_status():
    """Get processing status overview."""
    # Get counts of blocks in each state
    with db_manager.get_session() as session:
        status_counts = {}
        for status in ProcessingStatus:
            count = session.query(BlockValidation).filter(
                BlockValidation.status == status
            ).count()
            status_counts[status.value] = count
            
        # Get latest block
        latest_block = session.query(BlockValidation).order_by(
            BlockValidation.block_number.desc()
        ).first()
        
        return jsonify({
            "status_counts": status_counts,
            "latest_block": latest_block.block_number if latest_block else None,
            "total_blocks": sum(status_counts.values())
        })

@app.route("/reprocess", methods=["POST"])
def reprocess_blocks():
    """Reprocess blocks."""
    data = request.get_json()
    
    # If a specific block number is provided
    if "block_number" in data:
        block_number = data["block_number"]
        success, result_info = block_processor.reprocess_block(block_number)
        
        return jsonify({
            "status": "success" if success else "failure",
            "block_number": block_number,
            "details": result_info
        })
    
    # If a list of block numbers is provided
    elif "block_numbers" in data:
        results = block_processor.reprocess_blocks(data["block_numbers"])
        return jsonify(results)
    
    # Otherwise, reprocess invalid blocks
    else:
        limit = data.get("limit", 100)
        invalid_blocks = status_tracker.get_blocks_by_status(ProcessingStatus.INVALID, limit=limit)
        block_numbers = [block.block_number for block in invalid_blocks]
        
        results = block_processor.reprocess_blocks(block_numbers)
        return jsonify(results)

if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    # For Cloud Run (functions_framework integration)
    @functions_framework.http
    def processor_service_http(request):
        """HTTP function for Cloud Run."""
        return app(request.environ, lambda *args: None)