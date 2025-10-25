# 🎓 ThriftBot Complete Tutorial

**Welcome to ThriftBot!** This comprehensive guide will take you from setup to listing your first items on eBay with professional AI-generated content and optimized pricing.

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Workflow](#basic-workflow)
3. [Adding Your First Item](#adding-your-first-item)
4. [Photo Processing](#photo-processing)
5. [AI Content Generation](#ai-content-generation)
6. [Pricing Analysis](#pricing-analysis)
7. [Complete Automation Pipeline](#complete-automation-pipeline)
8. [Export to eBay](#export-to-ebay)
9. [Advanced Features](#advanced-features)
10. [Tips for Success](#tips-for-success)
11. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites
- macOS, Linux, or Windows
- Python 3.9 or higher
- OpenAI API key (for AI features)

### Installation

1. **Clone and setup:**
   ```bash
   cd thriftbot
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   python -m thriftbot db init
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Test installation:**
   ```bash
   python -m thriftbot version
   ```

---

## Basic Workflow

ThriftBot follows a simple 4-step process:

```
Thrift Store → Add Item → Process → List on eBay
     ↓            ↓          ↓           ↓
  Find Item → ThriftBot → Automation → Profit!
```

### The ThriftBot Process:
1. **Add** items to inventory with basic details
2. **Process** photos for professional appearance  
3. **Generate** AI-powered titles and descriptions
4. **Analyze** pricing with market research
5. **Export** eBay-ready CSV files

---

## Adding Your First Item

### Step 1: Add Item to Inventory

When you find an item at a thrift store, add it to ThriftBot:

```bash
python -m thriftbot item add \
  --sku 25-0001 \
  --category "Clothing" \
  --brand "Patagonia" \
  --name "Better Sweater Fleece Jacket" \
  --size "M" \
  --cost 7.99 \
  --condition "Good" \
  --color "Navy Blue"
```

**SKU Tips:**
- Use format: `YY-NNNN` (e.g., `25-0001` for 2025, item #1)
- Keep it simple and sequential
- ThriftBot can detect SKUs from photo filenames

### Step 2: Verify Your Item

```bash
python -m thriftbot item list
```

You'll see your item in a nice table format!

---

## Photo Processing

Good photos are critical for eBay success. ThriftBot makes this easy.

### Setting Up Photos

1. **Create photo directory structure:**
   ```bash
   mkdir -p photos
   ```

2. **Name your photos with SKU:**
   ```
   photos/25-0001_front.jpg
   photos/25-0001_back.jpg  
   photos/25-0001_label.jpg
   ```

### Get Photo Suggestions

```bash
python -m thriftbot photo suggestions --category clothing
```

This shows you exactly what photos to take for your category!

### Process Photos

```bash
python -m thriftbot photo process --sku 25-0001
```

**What happens:**
- ✅ Background removal for clean, professional look
- ✅ Image optimization and enhancement  
- ✅ Multiple variants (square crop, thumbnail)
- ✅ Automatic quality analysis

### Batch Process All Photos

```bash
python -m thriftbot photo batch --input-dir photos
```

ThriftBot automatically detects SKUs from filenames and processes everything!

---

## AI Content Generation

This is where ThriftBot shines - professional eBay content in seconds.

### Generate Title and Description

```bash
python -m thriftbot ai describe --sku 25-0001
```

**Example Output:**
```
🏷️  TITLE (72 chars):
   Patagonia Better Sweater Fleece Jacket Men's M Navy Blue Good Condition

📄 DESCRIPTION:
   Professional HTML description optimized for eBay...
```

### Different Styles Available

```bash
# Professional (default)
python -m thriftbot ai describe --sku 25-0001 --style professional

# Casual and friendly
python -m thriftbot ai describe --sku 25-0001 --style casual

# Enthusiastic sales copy
python -m thriftbot ai describe --sku 25-0001 --style enthusiastic

# Clean and minimal
python -m thriftbot ai describe --sku 25-0001 --style minimalist
```

### Get SEO Keywords

```bash
python -m thriftbot ai keywords --sku 25-0001 --count 10
```

### Analyze Title Optimization

```bash
python -m thriftbot ai analyze-title --title "Your eBay title here"
```

Get specific recommendations to improve your titles!

---

## Pricing Analysis

ThriftBot's pricing intelligence helps maximize profits.

### Full Pricing Analysis

```bash
python -m thriftbot pricing analyze --sku 25-0001
```

**You'll get:**
- Market research from comparable items
- Conservative, competitive, and aggressive pricing
- Detailed profit scenarios with ROI calculations
- Category-specific recommendations

### Break-Even Analysis

```bash
python -m thriftbot pricing breakeven --sku 25-0001
```

Know your absolute minimum price to avoid losses.

### Price Adjustment Suggestions

```bash
python -m thriftbot pricing suggest-adjustments --sku 25-0001
```

For items that aren't selling, get data-driven suggestions.

---

## Complete Automation Pipeline

The real power of ThriftBot: complete automation.

### Single Item Pipeline

```bash
python -m thriftbot workflow pipeline --sku 25-0001 --auto-export
```

**This runs the complete workflow:**
1. 📷 Process photos (if found)
2. 🤖 Generate AI content  
3. 💰 Analyze pricing and update database
4. 📤 Export CSV for eBay

### Batch Processing

Process multiple items at once:

```bash
python -m thriftbot workflow batch-pipeline --input-dir photos
```

ThriftBot finds all SKUs in your photos directory and processes them automatically!

### Pipeline Options

```bash
# Skip photo processing (if photos already done)
python -m thriftbot workflow pipeline --sku 25-0001 --skip-photos

# Skip AI generation (use templates)
python -m thriftbot workflow pipeline --sku 25-0001 --skip-ai

# Skip pricing (manual pricing)
python -m thriftbot workflow pipeline --sku 25-0001 --skip-pricing

# Use casual style for AI content
python -m thriftbot workflow pipeline --sku 25-0001 --style casual
```

---

## Export to eBay

### Generate eBay CSV

```bash
python -m thriftbot export ebay-csv --output drafts/my_listings.csv
```

### Review Your Inventory

```bash
python -m thriftbot item list --show-pricing --show-photos
```

See everything in one organized view!

### Upload to eBay

1. Go to eBay Seller Hub
2. Choose "Sell in Bulk" → "Upload CSV"
3. Upload your ThriftBot-generated CSV
4. Review listings and publish

---

## Advanced Features

### Photo Analysis

```bash
python -m thriftbot photo analyze --path photos/25-0001_front.jpg
```

Get specific recommendations for improving photo quality.

### Inventory Filtering

```bash
# Show only clothing items
python -m thriftbot item list --category Clothing

# Show only sold items  
python -m thriftbot item list --status sold

# Show detailed pricing info
python -m thriftbot item list --show-pricing --limit 10
```

### Market Research

ThriftBot can track market comparables for better pricing decisions (this will expand in future versions with API integrations).

---

## Tips for Success

### 📸 Photography Tips
- Use natural lighting when possible
- Clean items before photographing
- Take photos on plain backgrounds (white/neutral)
- Show all angles and any flaws honestly
- Include brand labels and size tags

### 🏷️ SKU Management
- Keep SKUs sequential: `25-0001`, `25-0002`, etc.
- Use the year prefix for organization
- Name photos with SKU for automatic processing
- Keep a backup list of your SKUs

### 💰 Pricing Strategy
- Start with "competitive" pricing for faster sales
- Use "conservative" for quick flips
- Use "aggressive" for rare/designer items
- Monitor your ROI - aim for 100%+ when possible

### 🤖 AI Content Tips
- Use "professional" style for expensive items
- Use "casual" style for everyday items
- Use "enthusiastic" for unique/vintage finds
- Always review AI content before listing

### 📊 Inventory Management
- Process items in batches for efficiency
- Use the pipeline command for complete automation
- Review pricing suggestions regularly
- Track your actual vs. predicted ROI

---

## Troubleshooting

### Common Issues

**"No photos found for SKU"**
- Check photo filenames include the SKU
- Ensure photos are in the correct directory
- Use supported formats: jpg, jpeg, png, webp, bmp, tiff

**"AI generation failed"**
- Check your OpenAI API key in `.env`
- Verify you have API credits remaining
- ThriftBot automatically falls back to templates

**"Database errors"**  
- Reinitialize: `rm thriftbot.db && python -m thriftbot db init`
- Ensure virtual environment is activated
- Check file permissions

**"Module not found errors"**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Getting Help

1. Check the error message carefully
2. Verify your setup with `python -m thriftbot version`
3. Make sure all dependencies are installed
4. Check that your `.env` file is properly configured

---

## Example: Complete Workflow

Let's walk through finding and listing an item:

### 1. At the Thrift Store
You find a Patagonia jacket for $7.99

### 2. Add to ThriftBot
```bash
python -m thriftbot item add \
  --sku 25-0001 \
  --category "Clothing" \
  --brand "Patagonia" \
  --name "Better Sweater" \
  --size "M" \
  --cost 7.99 \
  --condition "Good"
```

### 3. Take Photos at Home
- `photos/25-0001_front.jpg`
- `photos/25-0001_back.jpg`  
- `photos/25-0001_label.jpg`

### 4. Run Complete Pipeline
```bash
python -m thriftbot workflow pipeline --sku 25-0001 --auto-export
```

### 5. Results
- ✅ 3 photos processed into 9 optimized variants
- ✅ AI-generated professional title and description
- ✅ Competitive price: $24.16 (159.6% ROI)
- ✅ eBay CSV ready for upload

### 6. List on eBay
Upload CSV to eBay Seller Hub and publish!

**Total time:** ~5 minutes
**Expected profit:** ~$12-15 after fees
**ROI:** 150%+

---

## What's Next?

ThriftBot is continuously evolving! Coming features:
- Direct eBay API integration for automatic listing
- Enhanced market research with multiple data sources  
- Mobile app for on-the-go inventory management
- Advanced analytics and profit reporting
- Integration with other selling platforms

---

**Ready to transform your reselling business? Start with your first item and watch ThriftBot handle the rest!** 🚀

*For more advanced features and API documentation, see the README.md and technical documentation.*