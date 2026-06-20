-- ============================================================================
-- TradeNepse Data Platform - Floorsheet Schema
-- ============================================================================

CREATE TABLE IF NOT EXISTS floorsheet (
    contract_id             BIGINT NOT NULL,
    business_date           DATE NOT NULL,
    symbol                  VARCHAR(30) NOT NULL,
    company_name            VARCHAR(150),
    buyer_broker_id         VARCHAR(20) NOT NULL,
    seller_broker_id        VARCHAR(20) NOT NULL,
    buyer_broker_name       VARCHAR(150),
    seller_broker_name      VARCHAR(150),
    quantity                BIGINT NOT NULL,
    rate                    NUMERIC(12, 2) NOT NULL,
    amount                  NUMERIC(20, 2) NOT NULL,
    trade_time              TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (contract_id, business_date),
    
    -- Quantity, rate and amount must be positive values
    CONSTRAINT chk_floorsheet_qty CHECK (quantity > 0),
    CONSTRAINT chk_floorsheet_rate CHECK (rate > 0),
    CONSTRAINT chk_floorsheet_amount CHECK (amount > 0)
);

-- ============================================================================
-- PERFORMANCE INDEXES (Optimized for Raspberry Pi & SSD Storage)
-- ============================================================================

-- 1. Date-based filtering index (Critical for partition-like queries, reports, and daily cleanups)
CREATE INDEX IF NOT EXISTS idx_floorsheet_date 
ON floorsheet(business_date);

-- 2. Composite symbol & date index (Optimized for looking up transaction history of specific stocks)
CREATE INDEX IF NOT EXISTS idx_floorsheet_symbol_date 
ON floorsheet(symbol, business_date);

-- 3. Composite buyer broker & date index (Optimized for broker buy volume analytics over time)
CREATE INDEX IF NOT EXISTS idx_floorsheet_buyer_broker_date 
ON floorsheet(buyer_broker_id, business_date);

-- 4. Composite seller broker & date index (Optimized for broker sell volume analytics over time)
CREATE INDEX IF NOT EXISTS idx_floorsheet_seller_broker_date 
ON floorsheet(seller_broker_id, business_date);

-- 5. Trade time index (Optimized for intra-day analysis and order flow timeline queries)
CREATE INDEX IF NOT EXISTS idx_floorsheet_trade_time 
ON floorsheet(trade_time);

-- 6. Symbol and trade time index (Optimized for intraday replay, Smart Money tracking, and ChartLab queries)
CREATE INDEX IF NOT EXISTS idx_floorsheet_symbol_trade_time
ON floorsheet(symbol, trade_time);
