# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

### Development Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m thriftbot db init

# Test installation
python -m thriftbot version
```

### New User Onboarding Commands
```bash
# Interactive getting started guide (choose your experience level)
python -m thriftbot start

# Full step-by-step onboarding for beginners
python -m thriftbot onboard

# Quick item entry for experienced users
python -m thriftbot quick
```

### Common Development Commands
```bash
# Run ThriftBot CLI
python -m thriftbot

# Add inventory item (traditional method)
python -m thriftbot item add --sku 25-0001 --category "Clothing" --brand "Patagonia" --name "Better Sweater" --size "M" --cost 7.99 --condition "Good" --color "Navy"

# List items with pricing info
python -m thriftbot item list --show-pricing --limit 50

# Generate AI content for item
python -m thriftbot ai describe --sku 25-0001 --use-ai --style professional

# Analyze pricing for item
python -m thriftbot pricing analyze --sku 25-0001

# Process photos for item
python -m thriftbot photo process --sku 25-0001 --input-dir photos --output-dir processed

# Export to eBay CSV
python -m thriftbot export ebay-csv --output drafts/my_listings.csv

# Run complete workflow pipeline
python -m thriftbot workflow pipeline --sku 25-0001 --style professional --auto-export

# Batch process multiple items
python -m thriftbot workflow batch-pipeline --input-dir photos --style professional
```

### Testing Commands
```bash
# Test eBay API integration (sandbox)
python -m thriftbot ebay test --sku 25-0001 --sandbox

# Check eBay API status
python -m thriftbot ebay status --sandbox

# Analyze photo quality
python -m thriftbot photo analyze --path photos/25-0001_front.jpg
```

### Database Management
```bash
# Reinitialize database (destructive)
rm thriftbot.db
python -m thriftbot db init

# Check database contents via CLI
python -m thriftbot item list --show-pricing --show-photos
```

## User Experience Features

### Beginner-Friendly Onboarding
- **Interactive Start Guide**: `python -m thriftbot start` - Choose experience level and get guided to appropriate flow
- **Step-by-Step Onboarding**: `python -m thriftbot onboard` - Full walkthrough with explanations, examples, and validation
- **Quick Entry Mode**: `python -m thriftbot quick` - Minimal questions for experienced users

### Intelligent User Assistance
- **Smart SKU Generation**: Auto-generates unique SKUs with format YEAR-MONTH-RANDOM
- **Category Suggestions**: Pre-populated list of common reseller categories
- **Condition Guide**: Detailed explanations of each condition level with eBay standards
- **Input Validation**: Real-time validation with helpful error messages
- **Duplicate Detection**: Automatic SKU conflict resolution

### Guided Workflows
- **Progressive Disclosure**: Users can opt-in to AI content generation and pricing analysis during onboarding
- **Next Step Recommendations**: Clear guidance on what to do after each major action
- **Contextual Help**: Commands suggest follow-up actions based on current state

## Architecture Overview

### Core Architecture
ThriftBot is a **modular CLI application** built with Python 3.9+ using a **phase-based development approach**:

**Phase 1 (MVP)**: Core inventory management, database, CSV export  
**Phase 2 (AI)**: OpenAI integration for content generation  
**Phase 3 (Workflow)**: Photo processing, advanced pricing, automation pipelines  
**Phase 4 (Integration)**: eBay API integration, browser automation

### Key Components

#### CLI Framework (`cli.py`)
- Built with **Typer** for type-safe command-line interfaces
- Organized into sub-commands: `db`, `item`, `export`, `ai`, `photo`, `pricing`, `workflow`, `ebay`
- Each sub-command group handles a specific domain (inventory, AI generation, etc.)

#### Database Layer (`db.py`)
- **SQLModel** with SQLite for local persistence
- Two main models:
  - `InventoryItem`: Complete item tracking with cost, pricing, photos, status, profit calculations
  - `MarketComparable`: Market research data for pricing analysis
- Automatic fee calculation (eBay 10%, PayPal 2.9% + $0.30)
- Built-in profit tracking with ROI calculations

#### AI Integration (`ai.py`)
- **OpenAI GPT-3.5-turbo** for title/description generation
- **Intelligent fallback** to template-based content when API unavailable
- Multiple style support: professional, casual, enthusiastic, minimalist
- Keyword optimization and title analysis features

#### Photo Processing (`images.py`)
- **Pillow + rembg** for background removal and image enhancement
- Automatic photo discovery by SKU pattern matching
- Batch processing capabilities
- Image quality analysis and recommendations

#### Export System (`exporters.py`)
- **eBay-compatible CSV** format for bulk uploads
- JSON export for browser automation
- Configurable filtering (sold items, categories)

#### Pricing Engine (`pricing.py`)
- Market research integration with comparable analysis
- Break-even calculations including all fees
- Profit scenario modeling (conservative, competitive, aggressive)
- ROI optimization recommendations

### Data Flow Architecture

1. **Inventory Input**: Items added via CLI with basic details (SKU, brand, cost, etc.)
2. **Photo Processing**: Automatic discovery and enhancement of product photos
3. **AI Enhancement**: Content generation (titles, descriptions, keywords)
4. **Pricing Analysis**: Market research and profit optimization
5. **Export Generation**: eBay-ready CSV files or JSON for automation

### Configuration
- **Environment variables** via `.env` file (see `.env.example`)
- **Database**: Configurable via `THRIFTBOT_DB` (defaults to SQLite)
- **API Keys**: OpenAI (`OPENAI_API_KEY`), eBay (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`)

### Workflow Patterns

#### Single Item Workflow
```bash
# Add item → Process photos → Generate content → Analyze pricing → Export
python -m thriftbot workflow pipeline --sku SKU-001 --auto-export
```

#### Batch Processing Workflow
```bash
# Process all items found in photos directory
python -m thriftbot workflow batch-pipeline --input-dir photos
```

### Directory Structure
- `thriftbot/` - Main package with modular components
- `photos/` - Original product photos (git-ignored)
- `processed/` - Enhanced photos after processing (git-ignored)
- `drafts/` - CSV exports and generated content
- `comps/` - Market comparable data storage

### Development Notes
- **Phase-based approach**: Features are organized into development phases
- **Intelligent fallbacks**: AI features gracefully degrade when APIs unavailable
- **Comprehensive profit tracking**: Built-in eBay fee calculations and ROI analysis
- **Browser automation ready**: JSON exports designed for automation tools
- **SKU-based organization**: All features centered around SKU as primary identifier