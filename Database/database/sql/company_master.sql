-- ============================================================================
-- TradeNepse Data Platform - Company Master Schema
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_master (
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
    
    -- Ensure shares counts are positive
    CONSTRAINT chk_company_listed_shares CHECK (stock_listed_shares >= 0),
    CONSTRAINT chk_company_public_shares CHECK (public_shares >= 0),
    CONSTRAINT chk_company_promoter_shares CHECK (promoter_shares >= 0),
    CONSTRAINT chk_company_paid_up CHECK (paid_up_capital >= 0),
    CONSTRAINT chk_company_issued CHECK (issued_capital >= 0),
    CONSTRAINT chk_company_market_cap CHECK (market_capitalization >= 0)
);

-- Optimize queries filtering by sector (e.g. Banking, HydroPower)
CREATE INDEX IF NOT EXISTS idx_company_master_sector ON company_master(sector);
