# C21 Commodities

A full-stack commodity market tracking platform that provides real-time price monitoring, technical analysis, price alerts, and daily email reports.

## Features

- **Real-time Price Tracking**: Monitor commodity prices with live updates from the Financial Modeling Prep (FMP) API
- **Interactive Dashboard**: Visualize price trends with customizable charts and comparisons
- **Technical Analysis**: Pivot point analysis, candlestick charts, and moving averages (7, 14, 20 day)
- **Price Alerts**: Set buy/sell thresholds and receive email notifications when conditions are met
- **Daily Reports**: Automated email reports with personalized commodity summaries and charts
- **AI Chatbot (ICMA)**: Intelligent Commodity Market Analyst for natural language queries
- **News Feed**: Real-time commodity market news aggregation with smart filtering
- **User Management**: Secure authentication with personalized commodity subscriptions

## Architecture

The project runs on AWS infrastructure managed via Terraform:

- **AWS RDS (PostgreSQL)**: Stores user data, commodity information, and market records
- **AWS Lambda**: Executes ETL pipelines and alert processing
- **AWS ECR**: Container registry for Lambda function images
- **AWS SES**: Sends email alerts and daily reports
- **Streamlit**: Powers the interactive web dashboard

## Project Structure

```
├── dashboard/              # Streamlit web application
│   ├── pages/              # Dashboard pages (analysis, chatbot, news, etc.)
│   ├── queries/            # SQL query files
│   ├── adv_analysis/       # Technical analysis module
│   └── news/               # News feed configuration
├── pipeline/               # Real-time ETL pipeline
├── historical_pipeline/    # Historical data ETL pipeline
├── daily_report/           # Email report generation
├── price_alerts/           # Price alert monitoring and notifications
├── database/               # Database schema and seed data
├── documents/              # Architecture diagrams and ERD
└── terraform/              # Infrastructure as Code
```

## Tech Stack

- **Backend**: Python 3.9+
- **Database**: PostgreSQL
- **Dashboard**: Streamlit, Plotly, Altair
- **Infrastructure**: Terraform, AWS (Lambda, RDS, ECR, SES)
- **Data Source**: [Financial Modeling Prep API](https://financialmodelingprep.com/)

## Prerequisites

- Python 3.9+
- PostgreSQL database
- AWS account (for deployment)
- FMP API key

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd c21-commodities
```

### 2. Create environment variables

Create a `.env` file in each component directory with the following variables:

```env
# Database
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432

# API
API_KEY=your_fmp_api_key
CHATBOT_API_KEY=your_openrouter_api_key

# AWS (for alerts and reports)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
SES_EMAIL=your_ses_verified_email
SENDER_EMAIL=your_ses_verified_sender_email
HISTORICAL_LAMBDA_NAME=your_historical_lambda_function_name

# Security 
ENCRYPTION_KEY=your_encryption_key
```

### 3. Set up the database

```bash
cd database
./deploy.sh
```

### 4. Install dependencies

```bash
# Dashboard
cd dashboard
pip install -r dashboard_requirements.txt

# Pipeline
cd pipeline
pip install -r pipeline_requirements.txt
```

### 5. Run the dashboard

```bash
cd dashboard
streamlit run dashboard.py
```

## Components

### Pipeline

The ETL pipeline extracts commodity data from the FMP API, transforms it to match the database schema, and loads it into the `market_records` table. Runs on a schedule via AWS Lambda.

### Historical Pipeline

Loads historical commodity data (past 30 days) for new commodities, enabling immediate chart display for newly tracked assets.

### Daily Report

Generates and sends personalized HTML email reports for each user with their subscribed commodity performance, including price charts and key metrics.

### Price Alerts

Monitors user-defined buy/sell price thresholds and sends email notifications when conditions are met. Includes cooldown periods to prevent alert spam.

### Dashboard

A Streamlit web application featuring:
- Home page with commodity price overview and comparison charts
- Advanced analysis with pivot points and candlestick charts
- AI-powered chatbot for market queries
- Real-time news feed
- User subscription management

## Testing

Run tests with pytest:

```bash
pytest
```

## Deployment

Infrastructure is managed with Terraform:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## License

This project was created as part of the Sigma Labs coursework.
