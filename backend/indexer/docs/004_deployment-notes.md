# Deployment Notes

## Local Development

### Environment Setup

1. Create `.env` file in project root:
   ```
   # Database credentials
   DB_USER=postgres
   DB_PASS=password
   DB_NAME=wesmol
   DB_HOST=localhost
   
   # GCS configuration
   GCS_PROJECT_ID=wesmol
   GCS_BUCKET_NAME=smol_joes_blocks
   GCS_CREDENTIALS_PATH=None
   GCS_RAW_PREFIX=raw/
   GCS_DECODED_PREFIX=decoded/
   
   # RPC settings
   AVAX_RPC=https://your-rpc-endpoint.com
   ```

2. Set up Google Cloud credentials:
   ```bash
   gcloud auth application-default login
   ```

3. Install dependencies:
   ```bash
   pip install -e backend/indexer/
   pip install -r backend/services/decoder/requirements.txt
   ```

### Running Locally

1. Start the database:
   ```bash
   # If using PostgreSQL
   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_USER=postgres -e POSTGRES_DB=wesmol postgres
   ```

2. Run the decoder service:
   ```bash
   cd backend/services/decoder
   python -m server.main
   ```

3. Test with sample data:
   ```bash
   curl -X POST http://localhost:8080/process -d '{"block_path": "test/sample_block.json"}'
   ```

## Cloud Deployment

### Deployment to Cloud Run

1. Build and push Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/block-decoder backend/services/decoder/
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy block-decoder \
     --image gcr.io/PROJECT_ID/block-decoder \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DB_USER=postgres,DB_PASS=password,DB_NAME=wesmol,DB_HOST=cloudsql-host"
   ```

### Setting Up Pub/Sub Trigger

1. Create Pub/Sub topic:
   ```bash
   gcloud pubsub topics create new-blocks
   ```

2. Create Pub/Sub subscription:
   ```bash
   gcloud pubsub subscriptions create block-decoder-sub \
     --topic new-blocks \
     --push-endpoint=https://YOUR-SERVICE-URL/pubsub \
     --ack-deadline=60
   ```

3. Set up GCS notification:
   ```bash
   gsutil notification create -t new-blocks -f json gs://YOUR-BUCKET
   ```

### Serverless VPC Access (for database)

If using Cloud SQL, set up VPC connector:
```bash
gcloud compute networks vpc-access connectors create wesmol-connector \
  --region=us-central1 \
  --network=default \
  --range=10.8.0.0/28
```

Then add to service:
```bash
gcloud run services update block-decoder \
  --vpc-connector=wesmol-connector
```