CREATE TABLE block_processing (
    block_number BIGINT PRIMARY KEY,
    gcs_path TEXT NOT NULL,
    raw_status VARCHAR(20) NOT NULL,  -- VALID, INVALID, PENDING
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    validation_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);