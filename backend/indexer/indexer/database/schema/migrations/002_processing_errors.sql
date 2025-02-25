CREATE TABLE processing_errors (
    id SERIAL PRIMARY KEY,
    block_number BIGINT REFERENCES block_processing(block_number),
    error_type VARCHAR(50) NOT NULL,  -- VALIDATION, DECODE, etc.
    error_message TEXT NOT NULL,
    error_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);