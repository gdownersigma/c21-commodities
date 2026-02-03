# Commodities ETL Pipeline

This ETL pipeline extracts, transforms, and loads commodity market data into a PostgreSQL database. It consists of three main steps:

1. **Extract**: Fetches commodity data from the Financial Modeling Prep (FMP) API.
2. **Transform**: Cleans and reshapes the data to match the target schema.
3. **Load**: Inserts the transformed data into the `market_records` table in the database.

## Prerequisites

1. **Environment Setup**:
   - Python 3.8+
   - PostgreSQL database
   - Install dependencies:
     ```bash
     pip install -r pipeline_requirements.txt
     ```

2. **Environment Variables**:
   Create a `.env` file in the `pipeline/` directory with the following variables:
   ```env
   API_KEY=your_fmp_api_key
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_PORT=your_database_port
   ```

## How It Works

1. **Extract**:
   - The `extract.py` script fetches data for tracked commodity symbols from the FMP API.
   - Symbols are fetched from the database (`user_commodities` table) and combined with default symbols.

2. **Transform**:
   - The `transform.py` script cleans and reshapes the raw data:
     - Renames columns to match the database schema.
     - Converts timestamps to `datetime64[s]` precision.
     - Removes unused columns.
     - Adds an `ingested_at` timestamp.
     - Maps `symbol` to `commodity_id`.

3. **Load**:
   - The `load.py` script inserts the transformed data into the `market_records` table using batch inserts.

## How to Run

1. Navigate to the `pipeline/` directory:
   ```bash
   cd pipeline
   ```

2. Run the pipeline:
   ```bash
   python3 pipeline.py
   ```

3. Logs will indicate the progress of each step (extract, transform, load).

## Troubleshooting

- **No Data Extracted**:
  - Ensure your `.env` file contains a valid `API_KEY`.
  - Check the `user_commodities` table for tracked symbols.

- **Database Connection Issues**:
  - Verify the database credentials in your `.env` file.
  - Ensure the database is running and accessible.

- **API Errors**:
  - Check the API response for rate limits or invalid API keys.

## File Structure

```plaintext
pipeline/
├── extract.py                  # Extracts data from the FMP API
├── transform.py                # Transforms raw data into the target schema
├── load.py                     # Loads transformed data into the database
├── pipeline.py                 # Orchestrates the ETL process
├── pipeline_requirements.txt   # Python dependencies
└── .env                        # Environment variables (not committed to version control)
```

## Extending the Pipeline

- **Add New Data Sources**:
  - Update `extract.py` to include additional API endpoints.

- **Modify Transformations**:
  - Edit `transform.py` to include new cleaning or reshaping logic.

- **Change Database Schema**:
  - Update the `market_records` table schema and adjust `transform.py` and `load.py` accordingly.
