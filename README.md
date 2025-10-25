# 🧠 ThriftBot - AI-Powered Reseller CLI

**ThriftBot** is an intelligent command-line tool designed for eBay resellers to streamline the entire process from thrift store finds to optimized eBay listings and comprehensive profit tracking.

## 🚀 Features

### ✅ Phase 1: CLI MVP (Current)
- **Inventory Management**: Add, track, and manage your thrift store finds
- **Database Integration**: SQLite-based local storage with comprehensive data tracking
- **CSV Export**: Generate eBay-compatible CSV files for bulk upload
- **Profit Tracking**: Automatic calculation of fees, profits, and ROI
- **CLI Interface**: Intuitive command-line interface built with Typer

### 🔮 Coming Soon
- **Phase 2**: AI-powered title/description generation with OpenAI
- **Phase 3**: Automated workflow pipeline and photo processing
- **Phase 4**: Browser automation for automatic eBay listing creation

## 🛠️ Installation

### Prerequisites
- Python 3.9+ 
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd thriftbot
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python -m thriftbot db init
   ```

5. **Test installation**
   ```bash
   python -m thriftbot version
   ```

## 📖 Usage

### Basic Commands

**View version:**
```bash
python -m thriftbot version
```

**Initialize database:**
```bash
python -m thriftbot db init
```

### Inventory Management

**Add a new item:**
```bash
python -m thriftbot item add \\
  --sku 25-0001 \\
  --category "Clothing" \\
  --brand "Patagonia" \\
  --name "Better Sweater" \\
  --size "M" \\
  --cost 7.99 \\
  --condition "Good" \\
  --color "Navy"
```

**List items** (coming soon):
```bash
python -m thriftbot item list
```

### Export Data

**Export to eBay CSV:**
```bash
python -m thriftbot export ebay-csv --output drafts/my_listings.csv
```

**Export with sold items:**
```bash
python -m thriftbot export ebay-csv --output drafts/all_items.csv --include-sold
```

### AI Features (Phase 2)

**Generate item description:**
```bash
python -m thriftbot ai describe --sku 25-0001 --use-ai
```

## 📁 Project Structure

```
thriftbot/
├── thriftbot/                 # Main package
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point for python -m thriftbot
│   ├── cli.py                # Command-line interface
│   ├── db.py                 # Database models and operations
│   ├── exporters.py          # Data export functionality
│   ├── images.py             # Photo processing (Phase 3)
│   ├── ai.py                 # AI integration (Phase 2)
│   ├── pricing.py            # Price analysis (Phase 1)
│   └── profit_tracker.py     # Profit calculations
│
├── comps/                    # Market comparables data
├── drafts/                   # Export outputs
├── photos/                   # Original photos
├── processed/                # Processed photos
│
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── project_log.md           # Development log
└── README.md               # This file
```

## 💰 Profit Tracking

ThriftBot automatically calculates comprehensive profit metrics:

- **Cost Tracking**: Purchase price and associated costs
- **Fee Calculations**: eBay listing fees, final value fees, PayPal fees
- **Profit Analysis**: Gross profit, net profit, and ROI percentage
- **Market Analysis**: Compare against sold listings for pricing optimization

### Fee Structure (Built-in)
- eBay Final Value Fee: 10% of sale price
- PayPal Fee: 2.9% + $0.30
- Listing Fee: $0 (basic listings)

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key settings:
- `THRIFTBOT_DB`: Database path
- `OPENAI_API_KEY`: For AI descriptions (Phase 2)
- `EBAY_CLIENT_ID/SECRET`: For eBay API integration (Phase 4)

## 🗄️ Database Schema

### InventoryItem Table
- Basic item information (SKU, brand, name, category, etc.)
- Cost and pricing data
- Profit calculations and fees
- Status tracking (inventory → listed → sold)
- Photo paths and processing status
- eBay listing data for browser automation

### MarketComparable Table
- Market research data for pricing decisions
- Competitor analysis and sold listings
- Multi-platform support (eBay, Mercari, Poshmark)

## 🤖 Browser Automation (Phase 4)

ThriftBot will generate complete eBay listing JSON files that can be consumed by:
- **Claude + Comet Browser**: Automated eBay seller portal interaction
- **ChatGPT + Atlas Browser**: Alternative browser automation setup

### Listing JSON Format
```json
{
  "sku": "25-0001",
  "title": "Patagonia Better Sweater Size M Navy",
  "price": 45.99,
  "description": {...},
  "shipping": {...},
  "photos": {...}
}
```

## 📊 Workflow Examples

### Complete Item Workflow
```bash
# 1. Add item to inventory
python -m thriftbot item add --sku 25-0001 --category "Clothing" --brand "Patagonia" --name "Better Sweater" --size "M" --cost 7.99

# 2. Process photos (Phase 3)
python -m thriftbot images process --sku 25-0001 --input photos/ --output processed/

# 3. Generate AI description (Phase 2)  
python -m thriftbot ai describe --sku 25-0001 --use-ai

# 4. Analyze pricing
python -m thriftbot pricing suggest --sku 25-0001

# 5. Export for listing
python -m thriftbot export ebay-csv --output drafts/ready_to_list.csv
```

## 🐛 Troubleshooting

**Database issues:**
```bash
# Reinitialize database
rm thriftbot.db
python -m thriftbot db init
```

**Module not found errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

## 🤝 Contributing

This project follows a phase-based development approach:
1. **Phase 1**: Core CLI and database functionality ✅
2. **Phase 2**: AI integration with OpenAI
3. **Phase 3**: Photo processing and workflow automation  
4. **Phase 4**: Browser automation and eBay integration

## 📝 License

MIT License - see LICENSE file for details.

## 📞 Support

For issues and feature requests, please check the `project_log.md` for development updates and known issues.

---

**Built with:** Python 3.9+, Typer, SQLModel, Pillow, OpenAI SDK, and other modern tools for reliable reseller automation.