-- ============================================================================
-- TradeNepse Data Platform - Indices Schema
-- ============================================================================

CREATE TABLE IF NOT EXISTS indices (
    business_date           DATE NOT NULL,
    index_id                INTEGER NOT NULL,
    index_name              VARCHAR(100) NOT NULL,
    open_index              NUMERIC(12, 2),
    high_index              NUMERIC(12, 2),
    low_index               NUMERIC(12, 2),
    closing_index           NUMERIC(12, 2),
    fifty_two_week_high     NUMERIC(12, 2),
    fifty_two_week_low      NUMERIC(12, 2),
    turnover_value          NUMERIC(25, 2),
    turnover_volume         BIGINT,
    total_transaction       BIGINT,
    abs_change              NUMERIC(12, 2),
    percentage_change       NUMERIC(10, 4),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (business_date, index_id),
    
    -- Check constraints to enforce logical values
    CONSTRAINT chk_indices_open CHECK (open_index >= 0),
    CONSTRAINT chk_indices_high CHECK (high_index >= 0),
    CONSTRAINT chk_indices_low CHECK (low_index >= 0),
    CONSTRAINT chk_indices_closing CHECK (closing_index >= 0),
    CONSTRAINT chk_indices_52w_high CHECK (fifty_two_week_high >= 0),
    CONSTRAINT chk_indices_52w_low CHECK (fifty_two_week_low >= 0),
    CONSTRAINT chk_indices_turnover_val CHECK (turnover_value >= 0),
    CONSTRAINT chk_indices_turnover_vol CHECK (turnover_volume >= 0),
    CONSTRAINT chk_indices_transaction CHECK (total_transaction >= 0)
);

-- Optimize date-based filtering for indexes
CREATE INDEX IF NOT EXISTS idx_indices_date ON indices(business_date);

-- Optimize filtering by index ID and date range
CREATE INDEX IF NOT EXISTS idx_indices_id_date ON indices(index_id, business_date);
