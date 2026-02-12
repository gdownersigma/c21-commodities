# Historical Pipeline

An ETL pipeline that extracts, transforms, and loads historical commodity price data (past 30 days) into the PostgreSQL database.

## Overview

This pipeline backfills historical market data for commodities, enabling immediate chart visualization when users start tracking new assets.

## How It Works

1. **Extract** (`historical_extract.py`): Fetches 30 days of historical end-of-day price data from the Financial Modeling Prep (FMP) API for a specified commodity symbol.

2. **Transform** (`historical_transform.py`): Cleans and reshapes the data:
   - Converts date strings to timestamps
   - Renames columns to match database schema (`close` → `price`, `high` → `day_high`, etc.)
   - Removes unused columns (`vwap`)
   - Maps commodity symbols to database IDs

3. **Load** (`historical_load.py`): Batch inserts the transformed data into the `market_records` table.

## Prerequisites

- Python 3.8+
- PostgreSQL database with the commodities schema
- FMP API key

## Setup

1. Install dependencies:
   ```bash
   pip install -r historical_requirements.txt
   ```

2. Create a `.env` file:
   ```env
   API_KEY=your_fmp_api_key
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_PORT=5432
   ```

## Usage

### Local Execution

```bash
python historical_pipeline.py
```

Edit the `test_symbol` variable in `historical_pipeline.py` to specify which commodity to backfill.

### AWS Lambda

The pipeline includes a Lambda handler function. Invoke with:

```json
{
  "symbol": "GCUSD"
}
```

### Docker

```bash
docker build -t historical-pipeline .
docker run --env-file .env historical-pipeline
```

## Testing

```bash
pytest
```

## Files

| File | Description |
|------|-------------|
| `historical_pipeline.py` | Main orchestrator and Lambda handler |
| `historical_extract.py` | FMP API data extraction |
| `historical_transform.py` | Data cleaning and transformation |
| `historical_load.py` | Database insertion |
| `Dockerfile` | Container configuration |
