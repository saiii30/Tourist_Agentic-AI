# TouristAI RAG Knowledge Base

This folder contains stable tourism knowledge used by the chat page.

Use RAG for information that does not change often. Do not use RAG as the main
source for live prices, current weather, current ticket availability, or hotel
room availability.

## What Belongs In RAG

- Destination guides
- History
- Culture
- Local customs
- Temple information
- Trekking routes
- Hidden places
- Safety tips
- Packing guides
- Visa information
- State tourism documents

## Trusted Source Types

- PDFs
- Official tourism websites
- Government tourism brochures
- UNESCO information
- State tourism department documents

## Knowledge Types

Use these values in source JSON metadata:

| knowledge_type | Use for |
| --- | --- |
| `destination_guide` | Destination overview, tourist places, highlights |
| `history` | Monument history, museums, heritage sites |
| `culture` | Festivals, art, local food culture |
| `local_customs` | Dress code, etiquette, photography rules |
| `temple_information` | Temple timings, entry rules, darshan guidance |
| `trekking_routes` | Trail routes, difficulty, permits |
| `hidden_places` | Offbeat places and lesser-known viewpoints |
| `safety_tips` | Emergency numbers, local cautions, visitor safety |
| `packing_guides` | Seasonal or activity-specific packing |
| `visa_information` | Passport, visa, entry document guidance |
| `state_tourism_documents` | State brochures, official circuits, state guides |

## Source Types

Use these values in source JSON metadata:

| source_type | Trust |
| --- | --- |
| `official_tourism_website` | 100 |
| `government_brochure` | 100 |
| `state_tourism_document` | 100 |
| `unesco_information` | 100 |
| `pdf_brochure` | 95 |
| `tourism_board_pdf` | 95 |
| `curated_internal` | 90 |

## Add Official Websites And PDFs

Add official URLs, PDF URLs, or local PDF file paths to:

`backend/AI/rag/sources/official_tourism_sources.json`

Then run a dry check:

```powershell
python backend\AI\rag\admin_ingest.py --sources backend\AI\rag\sources\official_tourism_sources.json --dry-run
```

Merge crawled pages into the existing FAISS store:

```powershell
python backend\AI\rag\admin_ingest.py --sources backend\AI\rag\sources\official_tourism_sources.json
```

The ingester supports:

- HTML pages
- Remote PDF URLs
- Local PDF files via `file_path`
- Plain text or Markdown files

For a full rebuild, including the curated built-in Madurai knowledge:

```powershell
python backend\AI\rag\admin_ingest.py --sources backend\AI\rag\sources\official_tourism_sources.json --replace --include-seeded
```

## First-Time Setup

If the embedding model is not already cached locally, install requirements and allow one model download:

```powershell
python -m pip install -r backend\requirements.txt
$env:RAG_ALLOW_MODEL_DOWNLOAD="1"
```

After the first download, the app can use the local cache again.

## Inspect And Test RAG

Show vector store stats:

```powershell
python backend\AI\rag\rag_admin.py --stats
```

List indexed sources:

```powershell
python backend\AI\rag\rag_admin.py --sources
```

Test a question and see answer, citations, and raw chunks:

```powershell
python backend\AI\rag\rag_admin.py --query "What is the dress code for Meenakshi Temple?" --city Madurai
```

Test non-Madurai website knowledge:

```powershell
python backend\AI\rag\rag_admin.py --query "Tell me about Kanyakumari tourist spots" --city Kanniyakumari
```

## Example Source Entry

```json
{
  "enabled": true,
  "name": "Example State Tourism - Destination",
  "url": "https://example-tourism.gov.in/destination",
  "destination": "Destination Name",
  "city": "City Name",
  "category": "Official District Tourism",
  "knowledge_type": "destination_guide",
  "source_type": "official_tourism_website",
  "trust_score": 100,
  "language": "en"
}
```

For a local PDF:

```json
{
  "enabled": true,
  "name": "State Tourism Brochure",
  "file_path": "C:/path/to/state-tourism-brochure.pdf",
  "destination": "State Name",
  "city": "State Name",
  "category": "State Tourism Document",
  "knowledge_type": "state_tourism_documents",
  "source_type": "tourism_board_pdf",
  "trust_score": 95,
  "language": "en"
}
```

## Safety Notes

- The admin ingester merges by default, so existing RAG knowledge is preserved.
- `--replace` rebuilds the FAISS database and should be used only intentionally.
- Disabled source entries (`"enabled": false`) are ignored.
- The chat runtime does not crawl websites directly; ingestion is a separate admin action.
- Every RAG chunk should include `source_url`, `source_domain`, `knowledge_type`, `source_type`, `city`, and `destination`.
- Keep live data out of RAG: weather, hotel availability, ticket availability, and current prices should stay with APIs/agents.
