# Monday.com Business Intelligence Agent

A conversational Business Intelligence prototype that reads live data
from monday.com Deals and Work Orders boards, cleans inconsistent data,
performs deterministic business analysis, and provides founder-friendly
answers through a Streamlit interface.

---

## Hosted Prototype

Add the deployed Streamlit URL here:

`https://monday-bi-agent-akshayraoaroor.streamlit.app/`

---

## Source Code

GitHub:

`https://github.com/AkshayRaoA/monday-bi-agent`

---

## Features

### Monday.com Integration

- Connects directly to monday.com using the GraphQL API
- Reads Deals and Work Orders dynamically
- No CSV or Excel data is hardcoded into the application
- Supports local environment variables and Streamlit Cloud secrets
- Read-only integration

### Data Resilience

The application handles:

- Missing/null values
- Inconsistent status formatting
- Inconsistent sector names
- Invalid or missing dates
- Missing financial values
- Embedded duplicate/header rows
- Negative receivable values
- Missing billing information

Missing financial values are treated as **unknown**, not zero.

### Business Intelligence

The agent can answer questions about:

- Active sales pipeline
- Pipeline by sector
- Pipeline this quarter
- Pipeline this month
- Work order execution
- Billing
- Collections
- Receivables
- Delayed work orders
- Data quality
- Leadership updates

### Conversational Interface

Example questions:

- How much active pipeline do we have?
- How is the renewables pipeline looking?
- What's our pipeline this quarter?
- Which sectors have the largest pipeline?
- How much money have we collected?
- How much is receivable?
- How much have we billed?
- How are our work orders doing?
- Which projects are behind schedule?
- What data quality issues should leadership know about?
- Prepare a leadership update.

---

## Architecture

```text
                 User / Founder
                       |
                       v
              Streamlit Interface
                       |
                       v
            Conversational Router
                       |
           +-----------+-----------+
           |                       |
           v                       v
     Deals Analytics        Work Order Analytics
           |                       |
           +-----------+-----------+
                       |
                       v
                 Data Cleaning
                       |
                       v
             monday.com GraphQL API
                  /           \
                 /             \
                v               v
          Deals Board     Work Orders Board