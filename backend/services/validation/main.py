import os
import base64
import json
from flask import Flask, request, jsonify
import functions_framework
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()
from indexer.indexer.env import env

# Import after loading environment variables
from indexer.indexer.database.operations.session import DatabaseManager
from backend.indexer.indexer.database.operations.manager import BlockValidator
from indexer.indexer.processing.validation import BlockValidationService
from indexer.indexer.database.models.status import ProcessingStatus
from indexer.indexer.database.models.validation import BlockValidation
from backend.indexer.indexer.storage.base import GCSHandler

app = Flask(__name__)

db_manager = DatabaseManager(env.get_db_url())
validator = BlockValidator(db_manager)
validation_service = BlockValidationService(validator)

gcs_handler = GCSHandler(
    bucket_name=env.get_bucket_name(),
    credentials_path=os.getenv("GCS_CREDENTIALS_PATH")
)


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "validation"})

@app.route("/pubsub", methods=["POST"])
def handle_pubsub():
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
    
    # TODO: Extract GCS path (which depends on your Pub/Sub message format)
    gcs_path = data.get("name")
    if not gcs_path:
        return "No GCS path in message", 400
    
    try:
        # Download the block data
        block_data = gcs_handler.download_blob_as_bytes(gcs_path)
        if not block_data:
            return jsonify({
                "status": "error",
                "message": f"Block at {gcs_path} not found in GCS"
            }), 404
        
        success = validation_service.process_block(gcs_path, block_data)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Block at {gcs_path} validated successfully"
            })
        else:
            return jsonify({
                "status": "failure",
                "message": f"Block at {gcs_path} failed validation"
            }), 200  # Still return 200 so Pub/Sub knows we processed it
    
    except Exception as e:
        # Log the error but return 200 to acknowledge receipt
        print(f"Error processing {gcs_path}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 200  # Return 200 so Pub/Sub doesn't retry

@app.route("/status", methods=["GET"])
def get_validation_status():
    with db_manager.get_session() as session:
        status_counts = {}
        for status in ProcessingStatus:
            count = session.query(BlockValidation).filter(
                BlockValidation.status == status
            ).count()
            status_counts[status.value] = count
            
        latest_block = session.query(BlockValidation).order_by(
            desc(BlockValidation.block_number)
        ).first()
        
        return jsonify({
            "status_counts": status_counts,
            "latest_block": latest_block.block_number if latest_block else None,
            "total_blocks": sum(status_counts.values())
        })

@app.route("/reprocess", methods=["POST"])
def reprocess_blocks():
    """Reprocess failed blocks."""
    data = request.get_json()
    
    # If a specific block number is provided
    if "block_number" in data:
        block_number = data["block_number"]
        block_record = validator.get_block(block_number)
        
        if not block_record:
            return jsonify({
                "status": "error",
                "message": f"Block {block_number} not found"
            }), 404
            
        # Get block data using your GCSHandler
        block_data = gcs_handler.download_blob_as_bytes(block_record.gcs_path)
        if not block_data:
            return jsonify({
                "status": "error",
                "message": f"Block data not found in GCS: {block_record.gcs_path}"
            }), 404
        
        # Reprocess
        success = validation_service.reprocess_block(block_number, block_data)
        
        return jsonify({
            "status": "success" if success else "failure",
            "block_number": block_number
        })
    
    # Otherwise, reprocess all invalid blocks
    limit = data.get("limit", 100)
    invalid_blocks = validator.get_blocks_by_status(ProcessingStatus.INVALID, limit=limit)
    
    results = {
        "total": len(invalid_blocks),
        "success": 0,
        "failure": 0
    }
    
    for block in invalid_blocks:
        try:
            block_data = gcs_handler.download_blob_as_bytes(block.gcs_path)
            if not block_data:
                results["failure"] += 1
                continue

            success = validation_service.reprocess_block(block.block_number, block_data)
            
            if success:
                results["success"] += 1
            else:
                results["failure"] += 1
                
        except Exception:
            print(f"Error reprocessing block {block.block_number}: {str(e)}")
            results["failure"] += 1
    
    return jsonify(results)

if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    # For Cloud Run (functions_framework integration)
    @functions_framework.http
    def validation_service_http(request):
        """HTTP function for Cloud Run."""
        return app(request.environ, lambda *args: None)