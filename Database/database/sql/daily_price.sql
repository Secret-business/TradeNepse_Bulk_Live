-- ============================================================================
-- TradeNepse Data Platform - Daily Price Schema
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_price (
    business_date           DATE NOT NULL,
    security_id             INTEGER,
    symbol                  VARCHAR(30) NOT NULL,
    company_name            VARCHAR(150) NOT NULL,
    open_price              NUMERIC(12, 2),
    high_price              NUMERIC(12, 2),
    low_price               NUMERIC(12, 2),
    close_price             NUMERIC(12, 2),
    previous_close          NUMERIC(12, 2),
    volume                  BIGINT,
    turnover                NUMERIC(20, 2),
    trades                  INTEGER,
    vwap                    NUMERIC(12, 2),
    last_price              NUMERIC(12, 2),
    fifty_two_week_high     NUMERIC(12, 2),
    fifty_two_week_low      NUMERIC(12, 2),
    last_updated_time       TIMESTAMP WITH TIME ZONE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (business_date, symbol),
    
    -- Relationship linking to company_master.
    -- Changed to ON DELETE RESTRICT to ensure historical data is preserved if a company profile is removed.
    CONSTRAINT fk_daily_price_company FOREIGN KEY (symbol) 
        REFERENCES company_master(symbol) ON DELETE RESTRICT,
        
    -- Check constraints to enforce logical financial values
    CONSTRAINT chk_daily_price_open CHECK (open_price >= 0),
    CONSTRAINT chk_daily_price_high CHECK (high_price >= 0),
    CONSTRAINT chk_daily_price_low CHECK (low_price >= 0),
    CONSTRAINT chk_daily_price_close CHECK (close_price >= 0),
    CONSTRAINT chk_daily_price_prev CHECK (previous_close >= 0),
    CONSTRAINT chk_daily_price_volume CHECK (volume >= 0),
    CONSTRAINT chk_daily_price_turnover CHECK (turnover >= 0),
    CONSTRAINT chk_daily_price_trades CHECK (trades >= 0),
    CONSTRAINT chk_daily_price_vwap CHECK (vwap >= 0),
    CONSTRAINT chk_daily_price_last CHECK (last_price >= 0),
    CONSTRAINT chk_daily_price_52w_high CHECK (fifty_two_week_high >= 0),
    CONSTRAINT chk_daily_price_52w_low CHECK (fifty_two_week_low >= 0)
);

-- Optimize date-based analysis (e.g. daily trading volumes, reports)
CREATE INDEX IF NOT EXISTS idx_daily_price_date ON daily_price(business_date);

-- Optimize joins and queries matching security_id
CREATE INDEX IF NOT EXISTS idx_daily_price_security_id ON daily_price(security_id);

-- Optimize historical lookup for a single stock (highly common for charting, tech analysis)
CREATE INDEX IF NOT EXISTS idx_daily_price_symbol_date ON daily_price(symbol, business_date);
