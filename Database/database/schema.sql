-- ============================================================================
-- TradeNepse Data Platform V2 - Master Database Schema
-- ============================================================================
-- Description: Consolidated master database schema for TradeNepse.
--              Ties together company_master, daily_price, indices, and floorsheet.
-- Target DB:   PostgreSQL 12+
-- Deployment:  Raspberry Pi (constrained RAM/CPU) with SSD storage.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CLEANUP / RESET SCHEMA (Order respects foreign key dependencies)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS floorsheet CASCADE;
DROP TABLE IF EXISTS indices CASCADE;
DROP TABLE IF EXISTS daily_price CASCADE;
DROP TABLE IF EXISTS company_master CASCADE;

-- ----------------------------------------------------------------------------
-- 2. CREATE TABLE: company_master
-- ----------------------------------------------------------------------------
-- Purpose: Stores metadata and capitalization details for listed companies and securities.
-- Relation: Referenced by daily_price(symbol).
CREATE TABLE company_master (
    security_id             INTEGER PRIMARY KEY,
    symbol                  VARCHAR(30) UNIQUE NOT NULL,
    security_name           VARCHAR(150) NOT NULL,
    sector                  VARCHAR(100),
    listing_date            DATE,
    isin                    VARCHAR(30) UNIQUE,
    stock_listed_shares     NUMERIC(25, 2),
    public_shares           NUMERIC(25, 2),
    public_percentage       NUMERIC(5, 2) CONSTRAINT chk_company_public_pct CHECK (public_percentage BETWEEN 0 AND 100),
    promoter_shares         NUMERIC(25, 2),
    promoter_percentage     NUMERIC(5, 2) CONSTRAINT chk_company_promoter_pct CHECK (promoter_percentage BETWEEN 0 AND 100),
    paid_up_capital         NUMERIC(25, 2),
    issued_capital          NUMERIC(25, 2),
    market_capitalization   NUMERIC(25, 2),
    updated_date            TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_company_listed_shares CHECK (stock_listed_shares >= 0),
    CONSTRAINT chk_company_public_shares CHECK (public_shares >= 0),
    CONSTRAINT chk_company_promoter_shares CHECK (promoter_shares >= 0),
    CONSTRAINT chk_company_paid_up CHECK (paid_up_capital >= 0),
    CONSTRAINT chk_company_issued CHECK (issued_capital >= 0),
    CONSTRAINT chk_company_market_cap CHECK (market_capitalization >= 0)
);

-- Optimize company lookup and grouping by sector description
CREATE INDEX idx_company_master_sector ON company_master(sector);

-- ----------------------------------------------------------------------------
-- 3. CREATE TABLE: daily_price
-- ----------------------------------------------------------------------------
-- Purpose: Stores day-by-day closing prices and trading metrics for each security.
-- Relation: Many-to-one with company_master on symbol.
CREATE TABLE daily_price (
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
    
    -- Changed to ON DELETE RESTRICT to ensure historical data is preserved if a company profile is removed.
    CONSTRAINT fk_daily_price_company FOREIGN KEY (symbol) 
        REFERENCES company_master(symbol) ON DELETE RESTRICT,
        
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

-- Optimize date-based queries
CREATE INDEX idx_daily_price_date ON daily_price(business_date);

-- Optimize joins and queries matching security_id
CREATE INDEX idx_daily_price_security_id ON daily_price(security_id);

-- Optimize single-symbol historical charts and analysis
CREATE INDEX idx_daily_price_symbol_date ON daily_price(symbol, business_date);

-- ----------------------------------------------------------------------------
-- 4. CREATE TABLE: indices
-- ----------------------------------------------------------------------------
-- Purpose: Stores daily NEPSE sub-indices and main index points history.
CREATE TABLE indices (
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

-- Optimize date-based index lookups
CREATE INDEX idx_indices_date ON indices(business_date);

-- Optimize tracking of specific indexes over time
CREATE INDEX idx_indices_id_date ON indices(index_id, business_date);

-- ----------------------------------------------------------------------------
-- 5. CREATE TABLE: floorsheet
-- ----------------------------------------------------------------------------
-- Purpose: Stores individual transaction-level details (high-volume table).
CREATE TABLE floorsheet (
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
    
    CONSTRAINT chk_floorsheet_qty CHECK (quantity > 0),
    CONSTRAINT chk_floorsheet_rate CHECK (rate > 0),
    CONSTRAINT chk_floorsheet_amount CHECK (amount > 0)
);

-- Optimize range filters and date-based analytics on transactions
CREATE INDEX idx_floorsheet_date ON floorsheet(business_date);

-- Optimize charting and trading pattern analysis for specific symbols
CREATE INDEX idx_floorsheet_symbol_date ON floorsheet(symbol, business_date);

-- Optimize queries analyzing broker actions (buy/sell distribution) over time
CREATE INDEX idx_floorsheet_buyer_broker_date ON floorsheet(buyer_broker_id, business_date);
CREATE INDEX idx_floorsheet_seller_broker_date ON floorsheet(seller_broker_id, business_date);

-- Optimize intra-day price feeds and order-flow sequence analysis
CREATE INDEX idx_floorsheet_trade_time ON floorsheet(trade_time);

-- Optimize symbol and trade time index (Smart Money tracking, ChartLab queries)
CREATE INDEX idx_floorsheet_symbol_trade_time ON floorsheet(symbol, trade_time);

-- ----------------------------------------------------------------------------
-- 6. PERFORMANCE PLANNING & RECOMMENDATIONS (Raspberry Pi & SSD Optimization)
-- ----------------------------------------------------------------------------
/*
   PERFORMANCE SUMMARY FOR HARDWARE CONSTRAINTS:
   
   1. INDEX CONGESTION MANAGEMENT:
      - For floorsheet (millions of rows), we have created composite indexes (e.g. symbol + date).
      - Since the deployment is on an SSD, random-read times are fast, but RAM is scarce (Raspberry Pi).
      - To keep the working set in RAM, we focus on indexes starting with high cardinality fields (symbol, broker)
        combined with date. This avoids scanning large sub-indexes.
   
   2. VACUUM AND AUTOVACUUM TUNING:
      - High volume daily imports in the floorsheet table require timely statistics updates.
      - We recommend configuring aggressive autovacuum settings specifically for the floorsheet table:
        ALTER TABLE floorsheet SET (
            autovacuum_vacuum_scale_factor = 0.05,
            autovacuum_vacuum_threshold = 5000,
            autovacuum_analyze_scale_factor = 0.02,
            autovacuum_analyze_threshold = 2000
        );

   3. COMPOSITE INDEX ADVANTAGE:
      - Filters on both `symbol` and `business_date` (or `broker_id` and `business_date`) will perform Index Scans
        or Index Only Scans rather than Bitmap Heap Scans.

   4. OPTIONAL TABLE PARTITIONING (For Multi-Year History):
      - If floorsheet exceeds 10M+ rows, range partitioning by business_date (e.g. monthly or yearly partitions)
        should be implemented.
      - To support range partitioning in PostgreSQL:
        a) Table must be created with "PARTITION BY RANGE (business_date)"
        b) Primary key must include business_date: "PRIMARY KEY (contract_id, business_date)"
        c) Individual partition tables must be created (e.g. floorsheet_y2026m06).
*/
