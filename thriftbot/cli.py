"""
ThriftBot CLI - Main command-line interface
"""

import typer
from typing import Optional
from pathlib import Path

from thriftbot import __version__
from thriftbot.db import init_database, add_item_to_inventory
from thriftbot.exporters import export_to_ebay_csv

app = typer.Typer(
    name="thriftbot",
    help="AI-Powered Reseller CLI for eBay sellers",
    add_completion=False
)

# Database commands
db_app = typer.Typer(help="Database management commands")
app.add_typer(db_app, name="db")

# Item management commands  
item_app = typer.Typer(help="Inventory item management")
app.add_typer(item_app, name="item")

# Export commands
export_app = typer.Typer(help="Data export commands")
app.add_typer(export_app, name="export")

# AI commands
ai_app = typer.Typer(help="AI-powered content generation")
app.add_typer(ai_app, name="ai")

# Photo processing commands
photo_app = typer.Typer(help="Photo processing and management")
app.add_typer(photo_app, name="photo")

# Pricing commands
pricing_app = typer.Typer(help="Pricing analysis and market research")
app.add_typer(pricing_app, name="pricing")

# Workflow commands
workflow_app = typer.Typer(help="Automated workflow pipelines")
app.add_typer(workflow_app, name="workflow")

# eBay API commands
ebay_app = typer.Typer(help="Direct eBay API integration")
app.add_typer(ebay_app, name="ebay")


@app.command()
def version():
    """Show ThriftBot version."""
    typer.echo(f"ThriftBot v{__version__}")


@db_app.command("init")
def init_db():
    """Initialize the ThriftBot database."""
    try:
        init_database()
        typer.echo("✅ Database initialized successfully!")
    except Exception as e:
        typer.echo(f"❌ Error initializing database: {e}", err=True)
        raise typer.Exit(1)


@item_app.command("add")
def add_item(
    sku: str = typer.Option(..., help="Item SKU/identifier"),
    category: str = typer.Option(..., help="Item category"),
    brand: str = typer.Option(..., help="Brand name"),
    name: str = typer.Option(..., help="Item name/title"),
    size: Optional[str] = typer.Option(None, help="Item size"),
    cost: float = typer.Option(..., help="Purchase cost in dollars"),
    condition: str = typer.Option("Good", help="Item condition"),
    color: Optional[str] = typer.Option(None, help="Item color"),
):
    """Add a new item to inventory."""
    try:
        item_id = add_item_to_inventory(
            sku=sku,
            category=category,
            brand=brand,
            name=name,
            size=size,
            cost=cost,
            condition=condition,
            color=color
        )
        typer.echo(f"✅ Added item '{name}' with ID: {item_id}")
    except Exception as e:
        typer.echo(f"❌ Error adding item: {e}", err=True)
        raise typer.Exit(1)


@item_app.command("list")
def list_items(
    status: Optional[str] = typer.Option(None, help="Filter by status: inventory, listed, sold"),
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    limit: int = typer.Option(20, help="Maximum number of items to show"),
    show_photos: bool = typer.Option(False, help="Show photo information"),
    show_pricing: bool = typer.Option(False, help="Show pricing information")
):
    """List inventory items with optional filtering."""
    try:
        from thriftbot.db import get_inventory_items
        from tabulate import tabulate
        import json
        
        items = get_inventory_items(status=status, category=category)
        
        if not items:
            typer.echo("📋 No items found matching criteria")
            return
        
        # Limit results
        items = items[:limit]
        
        # Prepare table data
        headers = ["SKU", "Brand", "Name", "Category", "Condition", "Cost", "Status"]
        
        if show_pricing:
            headers.extend(["Suggested $", "Listed $", "Sold $", "Net Profit"])
        
        if show_photos:
            headers.extend(["Photos", "Processed"])
        
        table_data = []
        
        for item in items:
            row = [
                item.sku,
                item.brand,
                item.name[:20] + "..." if len(item.name) > 20 else item.name,
                item.category,
                item.condition,
                f"${float(item.cost):.2f}",
                item.status
            ]
            
            if show_pricing:
                suggested = f"${float(item.suggested_price):.2f}" if item.suggested_price else "-"
                listed = f"${float(item.listed_price):.2f}" if item.listed_price else "-"
                sold = f"${float(item.sold_price):.2f}" if item.sold_price else "-"
                net_profit = f"${float(item.net_profit):.2f}" if item.net_profit else "-"
                row.extend([suggested, listed, sold, net_profit])
            
            if show_photos:
                photo_count = 0
                processed_count = 0
                
                if item.photo_paths:
                    try:
                        photos = json.loads(item.photo_paths)
                        photo_count = len(photos)
                    except:
                        pass
                
                if item.processed_photos:
                    try:
                        processed = json.loads(item.processed_photos)
                        processed_count = len(processed)
                    except:
                        pass
                
                row.extend([str(photo_count), str(processed_count)])
            
            table_data.append(row)
        
        typer.echo(f"📋 Inventory Items ({len(items)} shown)\n")
        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Summary stats
        total_cost = sum(float(item.cost) for item in items)
        total_value = sum(float(item.suggested_price or 0) for item in items)
        
        typer.echo(f"\n📊 Summary:")
        typer.echo(f"   Total items: {len(items)}")
        typer.echo(f"   Total cost: ${total_cost:.2f}")
        typer.echo(f"   Total suggested value: ${total_value:.2f}")
        typer.echo(f"   Potential profit: ${total_value - total_cost:.2f}")
        
    except Exception as e:
        typer.echo(f"❌ Error listing items: {e}", err=True)
        raise typer.Exit(1)


@export_app.command("ebay-csv")
def export_ebay_csv(
    output: str = typer.Option("drafts/ebay_export.csv", help="Output CSV file path"),
    include_sold: bool = typer.Option(False, help="Include sold items")
):
    """Export inventory to eBay-compatible CSV."""
    try:
        export_path = Path(output)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        result = export_to_ebay_csv(str(export_path), include_sold=include_sold)
        typer.echo(f"✅ Exported {result['count']} items to {output}")
    except Exception as e:
        typer.echo(f"❌ Error exporting CSV: {e}", err=True)
        raise typer.Exit(1)


@ai_app.command("describe")
def generate_description(
    sku: str = typer.Option(..., help="Item SKU to generate description for"),
    use_ai: bool = typer.Option(True, help="Use AI for description generation"),
    style: str = typer.Option("professional", help="Description style: professional, casual, enthusiastic, minimalist"),
    keywords: bool = typer.Option(True, help="Include SEO keywords in description"),
    save: bool = typer.Option(False, help="Save generated content to database")
):
    """Generate optimized eBay title and description."""
    try:
        from thriftbot.ai import generate_listing_content
        
        typer.echo(f"🤖 Generating {'AI-powered' if use_ai else 'template-based'} content for {sku}...")
        
        content = generate_listing_content(
            sku=sku,
            style=style,
            include_keywords=keywords,
            max_title_length=80
        )
        
        typer.echo("\n" + "="*60)
        typer.echo(f"📝 GENERATED CONTENT ({content['generated_by'].upper()})")
        typer.echo("="*60)
        
        typer.echo(f"\n🏷️  TITLE ({len(content['title'])} chars):")
        typer.echo(f"   {content['title']}")
        
        typer.echo(f"\n📄 DESCRIPTION:")
        # Strip HTML tags for CLI display
        import re
        clean_desc = re.sub('<[^<]+?>', '', content['description'])
        clean_desc = re.sub(r'\n\s*\n', '\n', clean_desc.strip())
        typer.echo(f"   {clean_desc[:200]}..." if len(clean_desc) > 200 else f"   {clean_desc}")
        
        if save:
            # TODO: Save to database
            typer.echo("\n💾 Saving to database functionality coming soon...")
        
        typer.echo(f"\n\u2705 Content generated successfully using {content['generated_by']} method")
        
    except Exception as e:
        typer.echo(f"\u274c Error generating description: {e}", err=True)
        raise typer.Exit(1)


@ai_app.command("keywords")
def suggest_item_keywords(
    sku: str = typer.Option(..., help="Item SKU to generate keywords for"),
    count: int = typer.Option(10, help="Number of keywords to generate")
):
    """Generate SEO keywords for an inventory item."""
    try:
        from thriftbot.ai import suggest_keywords
        from thriftbot.db import get_item_by_sku
        
        item = get_item_by_sku(sku)
        if not item:
            typer.echo(f"\u274c Item with SKU {sku} not found", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"🔍 Generating {count} keywords for {item.brand} {item.name}...")
        
        keywords = suggest_keywords(item, count)
        
        typer.echo(f"\n🏷️  SUGGESTED KEYWORDS:")
        for i, keyword in enumerate(keywords, 1):
            typer.echo(f"   {i:2d}. {keyword}")
            
        typer.echo(f"\n✅ Generated {len(keywords)} keywords")
        
    except Exception as e:
        typer.echo(f"\u274c Error generating keywords: {e}", err=True)
        raise typer.Exit(1)


@ai_app.command("analyze-title")
def analyze_title(
    title: str = typer.Option(..., help="Title to analyze")
):
    """Analyze an eBay title for optimization."""
    try:
        from thriftbot.ai import analyze_title_optimization
        
        typer.echo(f"🔍 Analyzing title: '{title}'")
        
        analysis = analyze_title_optimization(title)
        
        typer.echo("\n" + "="*50)
        typer.echo("📈 TITLE ANALYSIS")
        typer.echo("="*50)
        
        check_mark = "\u2705"
        x_mark = "\u274c"
        
        typer.echo(f"\nLength: {analysis['length']}/{analysis['max_length']} characters {check_mark if analysis['length_ok'] else x_mark}")
        typer.echo(f"Word count: {analysis['word_count']}")
        
        typer.echo(f"\nOptimization checklist:")
        typer.echo(f"  Brand mentioned: {check_mark if analysis['has_brand'] else x_mark}")
        typer.echo(f"  Size included: {check_mark if analysis['has_size'] else x_mark}")
        typer.echo(f"  Color mentioned: {check_mark if analysis['has_color'] else x_mark}")
        typer.echo(f"  Condition stated: {check_mark if analysis['has_condition'] else x_mark}")
        
        if analysis['suggestions']:
            typer.echo(f"\n💡 Suggestions:")
            for suggestion in analysis['suggestions']:
                typer.echo(f"  - {suggestion}")
        else:
            typer.echo(f"\n{check_mark} Title looks well optimized!")
        
    except Exception as e:
        typer.echo(f"\u274c Error analyzing title: {e}", err=True)
        raise typer.Exit(1)


# Photo processing commands
@photo_app.command("process")
def process_photos(
    sku: str = typer.Option(..., help="Item SKU to process photos for"),
    input_dir: str = typer.Option("photos", help="Input directory with photos"),
    output_dir: str = typer.Option("processed", help="Output directory for processed photos"),
    remove_bg: bool = typer.Option(True, help="Remove background from photos"),
    enhance: bool = typer.Option(True, help="Apply image enhancement"),
    variants: bool = typer.Option(True, help="Create photo variants (square, thumbnail)")
):
    """Process photos for an inventory item."""
    try:
        from thriftbot.images import process_item_photos
        
        typer.echo(f"📷 Processing photos for {sku}...")
        
        result = process_item_photos(
            sku=sku,
            input_dir=input_dir,
            output_dir=output_dir,
            remove_background=remove_bg,
            enhance=enhance,
            create_variants=variants
        )
        
        typer.echo(f"\n✅ Photo processing complete!")
        typer.echo(f"   Original photos: {result['original_count']}")
        typer.echo(f"   Processed files: {result['processed_count']}")
        typer.echo(f"   Output directory: {result['output_directory']}")
        
        # Show processing log
        for log_entry in result['processing_log']:
            if log_entry['status'] == 'success':
                typer.echo(f"   ✅ {log_entry['message']}")
            else:
                typer.echo(f"   ❌ {log_entry['message']}")
        
    except Exception as e:
        typer.echo(f"❌ Error processing photos: {e}", err=True)
        raise typer.Exit(1)


@photo_app.command("batch")
def batch_process(
    input_dir: str = typer.Option("photos", help="Input directory with photos"),
    output_dir: str = typer.Option("processed", help="Output directory for processed photos"),
    remove_bg: bool = typer.Option(False, help="Remove background (slower for batch)"),
    enhance: bool = typer.Option(True, help="Apply image enhancement")
):
    """Batch process all photos in directory by detected SKU."""
    try:
        from thriftbot.images import batch_process_directory
        
        typer.echo(f"📷 Batch processing photos from {input_dir}...")
        
        result = batch_process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            remove_background=remove_bg,
            enhance=enhance
        )
        
        typer.echo(f"\n✅ Batch processing complete!")
        typer.echo(f"   Total photos found: {result['total_photos_found']}")
        typer.echo(f"   Matched SKUs: {len(result['matched_skus'])}")
        typer.echo(f"   Unmatched photos: {result['unmatched_photos']}")
        
        if result['matched_skus']:
            typer.echo(f"\n📝 Processed SKUs:")
            for sku in result['matched_skus']:
                if sku in result['processing_results']:
                    sku_result = result['processing_results'][sku]
                    typer.echo(f"   {sku}: {sku_result['processed_count']} files")
        
        if result['errors']:
            typer.echo(f"\n⚠️  Errors:")
            for error in result['errors']:
                typer.echo(f"   - {error}")
        
    except Exception as e:
        typer.echo(f"❌ Error in batch processing: {e}", err=True)
        raise typer.Exit(1)


@photo_app.command("analyze")
def analyze_photo(
    path: str = typer.Option(..., help="Path to photo to analyze")
):
    """Analyze photo quality and get recommendations."""
    try:
        from thriftbot.images import analyze_image_quality
        
        analysis = analyze_image_quality(path)
        
        typer.echo(f"🔍 Photo Analysis: {Path(path).name}")
        typer.echo(f"\nDimensions: {analysis['dimensions']}")
        typer.echo(f"Aspect Ratio: {analysis['aspect_ratio']}")
        typer.echo(f"Format: {analysis['format']}")
        typer.echo(f"Color Mode: {analysis['mode']}")
        
        typer.echo(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            typer.echo(f"   - {rec}")
        
    except Exception as e:
        typer.echo(f"❌ Error analyzing photo: {e}", err=True)
        raise typer.Exit(1)


@photo_app.command("suggestions")
def photo_suggestions(
    category: str = typer.Option(..., help="Item category for photo suggestions")
):
    """Get photo upload suggestions for a category."""
    try:
        from thriftbot.images import get_photo_upload_suggestions
        
        suggestions = get_photo_upload_suggestions(category)
        
        typer.echo(f"📷 Photo Upload Guide: {suggestions['category'].title()}")
        
        typer.echo(f"\n📝 Suggested Photos:")
        for i, suggestion in enumerate(suggestions['suggested_photos'], 1):
            typer.echo(f"   {i}. {suggestion}")
        
        typer.echo(f"\n💡 General Tips:")
        for tip in suggestions['general_tips']:
            typer.echo(f"   - {tip}")
        
    except Exception as e:
        typer.echo(f"\u274c Error getting suggestions: {e}", err=True)
        raise typer.Exit(1)


# Pricing commands
@pricing_app.command("analyze")
def analyze_pricing(
    sku: str = typer.Option(..., help="Item SKU to analyze pricing for")
):
    """Analyze pricing for an inventory item with market research."""
    try:
        from thriftbot.pricing import analyze_item_pricing
        
        typer.echo(f"💰 Analyzing pricing for {sku}...")
        
        analysis = analyze_item_pricing(sku)
        
        item_info = analysis['item_info']
        typer.echo(f"\n📝 Item: {item_info['brand']} {item_info['name']}")
        typer.echo(f"   Category: {item_info['category']}")
        typer.echo(f"   Condition: {item_info['condition']}")
        typer.echo(f"   Cost: ${item_info['cost']}")
        
        # Market data
        market = analysis['market_data']
        typer.echo(f"\n📈 Market Analysis ({market['total_comparables']} comparables):")
        price_range = market['price_range']
        typer.echo(f"   Range: ${price_range['min']} - ${price_range['max']}")
        typer.echo(f"   Average: ${price_range['average']}")
        typer.echo(f"   Median: ${price_range['median']}")
        
        # Pricing suggestions
        pricing = analysis['pricing_analysis']['suggested_prices']
        typer.echo(f"\n🏷️  Suggested Pricing:")
        typer.echo(f"   Conservative: ${pricing['conservative']}")
        typer.echo(f"   Competitive: ${pricing['competitive']}")
        typer.echo(f"   Aggressive: ${pricing['aggressive']}")
        
        # Profit scenarios
        typer.echo(f"\n📊 Profit Scenarios:")
        for scenario in analysis['profit_scenarios']:
            profit = scenario['profit']
            typer.echo(f"   {scenario['strategy']}: ${scenario['price']} → ${profit['net_profit']} profit ({profit['roi_percentage']}% ROI)")
        
        # Recommendations
        typer.echo(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            typer.echo(f"   - {rec}")
        
    except Exception as e:
        typer.echo(f"\u274c Error analyzing pricing: {e}", err=True)
        raise typer.Exit(1)


@pricing_app.command("breakeven")
def calculate_breakeven(
    sku: str = typer.Option(..., help="Item SKU to calculate break-even for")
):
    """Calculate break-even price for an item."""
    try:
        from thriftbot.pricing import calculate_break_even_price
        
        result = calculate_break_even_price(sku)
        
        typer.echo(f"💰 Break-even Analysis: {sku}")
        typer.echo(f"\nItem cost: ${result['item_cost']}")
        typer.echo(f"Break-even price: ${result['break_even_price']}")
        typer.echo(f"Recommended minimum: ${result['break_even_with_margin']}")
        
        fees = result['fee_breakdown']
        typer.echo(f"\nFee breakdown at break-even:")
        typer.echo(f"   Fixed fees: ${fees['fixed_fees']}")
        typer.echo(f"   Variable rate: {fees['variable_rate_percentage']}%")
        typer.echo(f"   Total estimated fees: ${fees['estimated_fees_at_break_even']}")
        
        typer.echo(f"\n✅ {result['recommendation']}")
        
    except Exception as e:
        typer.echo(f"\u274c Error calculating break-even: {e}", err=True)
        raise typer.Exit(1)


@pricing_app.command("suggest-adjustments")
def suggest_adjustments(
    sku: str = typer.Option(..., help="Item SKU to suggest price adjustments for")
):
    """Suggest price adjustments for items that aren't selling."""
    try:
        from thriftbot.pricing import suggest_price_adjustments
        
        result = suggest_price_adjustments(sku)
        
        if 'message' in result:
            typer.echo(result['message'])
            return
        
        typer.echo(f"💰 Price Adjustment Analysis: {sku}")
        typer.echo(f"Current price: ${result['current_price']}")
        typer.echo(f"Days listed: {result['days_listed']}")
        
        if result['suggestions']:
            typer.echo(f"\n💡 Suggestions:")
            for suggestion in result['suggestions']:
                urgency = "🔴" if suggestion['urgency'] == 'high' else "🟡" if suggestion['urgency'] == 'medium' else "🟢"
                typer.echo(f"   {urgency} {suggestion['type'].title()}:")
                typer.echo(f"      Current: ${suggestion['current_price']} → Suggested: ${suggestion['suggested_price']}")
                typer.echo(f"      Reason: {suggestion['reason']}")
        else:
            typer.echo(f"\n✅ No price adjustments recommended at this time")
        
        # Market context
        market = result['market_context']
        typer.echo(f"\n📈 Market context: ${market['min']} - ${market['max']} (avg: ${market['average']})")
        
    except Exception as e:
        typer.echo(f"\u274c Error suggesting adjustments: {e}", err=True)
        raise typer.Exit(1)


# Workflow commands
@workflow_app.command("pipeline")
def run_pipeline(
    sku: str = typer.Option(..., help="Item SKU to process through complete pipeline"),
    skip_photos: bool = typer.Option(False, help="Skip photo processing"),
    skip_ai: bool = typer.Option(False, help="Skip AI content generation"),
    skip_pricing: bool = typer.Option(False, help="Skip pricing analysis"),
    auto_export: bool = typer.Option(False, help="Automatically export to CSV after processing"),
    style: str = typer.Option("professional", help="AI content style: professional, casual, enthusiastic, minimalist")
):
    """Run complete processing pipeline for an item: photos → AI content → pricing → export."""
    
    typer.echo(f"🚀 Starting complete pipeline for {sku}...")
    
    pipeline_results = {
        "sku": sku,
        "steps_completed": [],
        "steps_skipped": [],
        "errors": []
    }
    
    # Step 1: Photo Processing
    if not skip_photos:
        typer.echo(f"\n📷 Step 1: Processing photos...")
        try:
            from thriftbot.images import process_item_photos, find_item_photos
            from pathlib import Path
            
            # Check if photos exist
            photo_files = find_item_photos(sku, Path("photos"))
            if photo_files:
                result = process_item_photos(
                    sku=sku,
                    input_dir="photos",
                    output_dir="processed",
                    remove_background=True,
                    enhance=True,
                    create_variants=True
                )
                typer.echo(f"   ✅ Processed {result['processed_count']} photo variants")
                pipeline_results["steps_completed"].append("photo_processing")
            else:
                typer.echo(f"   ⚠️  No photos found for {sku} - skipping photo processing")
                pipeline_results["steps_skipped"].append("photo_processing")
                
        except Exception as e:
            typer.echo(f"   ❌ Photo processing failed: {e}")
            pipeline_results["errors"].append(f"Photo processing: {e}")
    else:
        pipeline_results["steps_skipped"].append("photo_processing")
    
    # Step 2: AI Content Generation
    if not skip_ai:
        typer.echo(f"\n🤖 Step 2: Generating AI content...")
        try:
            from thriftbot.ai import generate_listing_content
            
            content = generate_listing_content(
                sku=sku,
                style=style,
                include_keywords=True,
                max_title_length=80
            )
            
            typer.echo(f"   ✅ Generated {content['generated_by']} content ({len(content['title'])} char title)")
            pipeline_results["steps_completed"].append("ai_content")
            pipeline_results["ai_content"] = {
                "title": content["title"],
                "method": content["generated_by"]
            }
            
        except Exception as e:
            typer.echo(f"   ❌ AI content generation failed: {e}")
            pipeline_results["errors"].append(f"AI content: {e}")
    else:
        pipeline_results["steps_skipped"].append("ai_content")
    
    # Step 3: Pricing Analysis
    if not skip_pricing:
        typer.echo(f"\n💰 Step 3: Analyzing pricing...")
        try:
            from thriftbot.pricing import analyze_item_pricing
            from thriftbot.db import update_item_pricing
            
            analysis = analyze_item_pricing(sku)
            
            # Update item with suggested pricing
            competitive_price = analysis["pricing_analysis"]["suggested_prices"]["competitive"]
            update_item_pricing(sku, suggested_price=competitive_price)
            
            typer.echo(f"   ✅ Suggested competitive price: ${competitive_price}")
            
            best_roi = max(analysis["profit_scenarios"], key=lambda x: x["profit"]["roi_percentage"])
            typer.echo(f"   ✅ Best ROI: {best_roi['strategy']} at ${best_roi['price']} ({best_roi['profit']['roi_percentage']}% ROI)")
            
            pipeline_results["steps_completed"].append("pricing_analysis")
            pipeline_results["pricing"] = {
                "suggested_price": competitive_price,
                "best_roi_strategy": best_roi["strategy"],
                "best_roi_price": best_roi["price"],
                "best_roi_percentage": best_roi["profit"]["roi_percentage"]
            }
            
        except Exception as e:
            typer.echo(f"   ❌ Pricing analysis failed: {e}")
            pipeline_results["errors"].append(f"Pricing analysis: {e}")
    else:
        pipeline_results["steps_skipped"].append("pricing_analysis")
    
    # Step 4: Auto Export (if requested)
    if auto_export:
        typer.echo(f"\n📤 Step 4: Exporting to CSV...")
        try:
            from thriftbot.exporters import export_to_ebay_csv
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"drafts/{sku}_pipeline_{timestamp}.csv"
            
            result = export_to_ebay_csv(output_file, include_sold=False)
            typer.echo(f"   ✅ Exported to {output_file}")
            
            pipeline_results["steps_completed"].append("csv_export")
            pipeline_results["export_file"] = output_file
            
        except Exception as e:
            typer.echo(f"   ❌ CSV export failed: {e}")
            pipeline_results["errors"].append(f"CSV export: {e}")
    
    # Pipeline Summary
    typer.echo(f"\n" + "="*60)
    typer.echo(f"🏁 PIPELINE COMPLETE: {sku}")
    typer.echo(f"="*60)
    
    typer.echo(f"\n✅ Steps completed: {len(pipeline_results['steps_completed'])}")
    for step in pipeline_results["steps_completed"]:
        typer.echo(f"   - {step.replace('_', ' ').title()}")
    
    if pipeline_results["steps_skipped"]:
        typer.echo(f"\n⏭️  Steps skipped: {len(pipeline_results['steps_skipped'])}")
        for step in pipeline_results["steps_skipped"]:
            typer.echo(f"   - {step.replace('_', ' ').title()}")
    
    if pipeline_results["errors"]:
        typer.echo(f"\n❌ Errors encountered: {len(pipeline_results['errors'])}")
        for error in pipeline_results["errors"]:
            typer.echo(f"   - {error}")
        typer.echo(f"\n⚠️  Pipeline completed with errors. Review item manually.")
    else:
        typer.echo(f"\n🎉 Pipeline completed successfully! Item ready for listing.")
    
    # Show next steps
    typer.echo(f"\n📝 Next Steps:")
    typer.echo(f"   1. Review generated content: python -m thriftbot ai describe --sku {sku}")
    typer.echo(f"   2. Check pricing: python -m thriftbot pricing analyze --sku {sku}")
    if not auto_export:
        typer.echo(f"   3. Export for eBay: python -m thriftbot export ebay-csv")
    typer.echo(f"   4. List item on eBay using generated content")


@workflow_app.command("batch-pipeline")
def batch_pipeline(
    input_dir: str = typer.Option("photos", help="Directory to scan for items by SKU"),
    skip_photos: bool = typer.Option(False, help="Skip photo processing"),
    skip_ai: bool = typer.Option(False, help="Skip AI content generation"),
    skip_pricing: bool = typer.Option(False, help="Skip pricing analysis"),
    style: str = typer.Option("professional", help="AI content style")
):
    """Run pipeline for all items found in photo directory."""
    
    try:
        from thriftbot.images import batch_process_directory, _extract_sku_from_filename
        from thriftbot.db import get_item_by_sku
        from pathlib import Path
        
        typer.echo(f"🚀 Starting batch pipeline from {input_dir}...")
        
        # Find all photos and extract SKUs
        input_path = Path(input_dir)
        all_photos = []
        for file_path in input_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}:
                all_photos.append(file_path)
        
        # Extract unique SKUs
        skus = set()
        for photo in all_photos:
            sku = _extract_sku_from_filename(photo.name)
            if sku and get_item_by_sku(sku):
                skus.add(sku)
        
        if not skus:
            typer.echo(f"   ⚠️  No valid SKUs found in {input_dir}")
            return
        
        typer.echo(f"   Found {len(skus)} items to process: {', '.join(sorted(skus))}")
        
        batch_results = {
            "total_items": len(skus),
            "successful": 0,
            "failed": 0,
            "results": {}
        }
        
        # Process each SKU through pipeline
        for i, sku in enumerate(sorted(skus), 1):
            typer.echo(f"\n{'='*40}")
            typer.echo(f"📄 Processing item {i}/{len(skus)}: {sku}")
            typer.echo(f"{'='*40}")
            
            try:
                # Run individual pipeline (reuse the logic but simplified)
                success = True
                
                # Photo processing
                if not skip_photos:
                    from thriftbot.images import process_item_photos, find_item_photos
                    
                    photo_files = find_item_photos(sku, input_path)
                    if photo_files:
                        result = process_item_photos(sku=sku, input_dir=input_dir, output_dir="processed")
                        typer.echo(f"   ✅ Photos: {result['processed_count']} files")
                    else:
                        typer.echo(f"   ⚠️  No photos found")
                
                # AI content
                if not skip_ai:
                    from thriftbot.ai import generate_listing_content
                    content = generate_listing_content(sku=sku, style=style)
                    typer.echo(f"   ✅ AI: {content['generated_by']} content generated")
                
                # Pricing
                if not skip_pricing:
                    from thriftbot.pricing import analyze_item_pricing
                    from thriftbot.db import update_item_pricing
                    
                    analysis = analyze_item_pricing(sku)
                    competitive_price = analysis["pricing_analysis"]["suggested_prices"]["competitive"]
                    update_item_pricing(sku, suggested_price=competitive_price)
                    typer.echo(f"   ✅ Pricing: ${competitive_price} suggested")
                
                batch_results["successful"] += 1
                batch_results["results"][sku] = "success"
                typer.echo(f"   ✅ {sku} completed successfully")
                
            except Exception as e:
                batch_results["failed"] += 1
                batch_results["results"][sku] = str(e)
                typer.echo(f"   ❌ {sku} failed: {e}")
                success = False
        
        # Batch Summary
        typer.echo(f"\n" + "="*60)
        typer.echo(f"🏁 BATCH PIPELINE COMPLETE")
        typer.echo(f"="*60)
        
        typer.echo(f"\nResults:")
        typer.echo(f"   Total items processed: {batch_results['total_items']}")
        typer.echo(f"   ✅ Successful: {batch_results['successful']}")
        typer.echo(f"   ❌ Failed: {batch_results['failed']}")
        
        if batch_results["failed"] > 0:
            typer.echo(f"\n❌ Failed items:")
            for sku, result in batch_results["results"].items():
                if result != "success":
                    typer.echo(f"   - {sku}: {result}")
        
        typer.echo(f"\n📝 Next steps:")
        typer.echo(f"   - Review items: python -m thriftbot item list --show-pricing")
        typer.echo(f"   - Export all: python -m thriftbot export ebay-csv")
        
    except Exception as e:
        typer.echo(f"\u274c Batch pipeline error: {e}", err=True)
        raise typer.Exit(1)


# eBay API commands
@ebay_app.command("setup")
def setup_ebay_oauth(
    sandbox: bool = typer.Option(True, help="Use sandbox environment for testing")
):
    """Set up eBay OAuth2 authentication."""
    
    try:
        from thriftbot.ebay_client import eBayAPIClient
        
        client = eBayAPIClient(sandbox=sandbox)
        
        # Generate OAuth URL
        oauth_url = client.get_oauth_url(state="thriftbot_setup")
        
        typer.echo(f"🔗 eBay OAuth2 Setup ({'Sandbox' if sandbox else 'Production'})")
        typer.echo(f"\n1. Open this URL in your browser:")
        typer.echo(f"   {oauth_url}")
        typer.echo(f"\n2. Authorize ThriftBot to access your eBay account")
        typer.echo(f"\n3. Copy the authorization code from the callback URL")
        
        # Get authorization code from user
        auth_code = typer.prompt("\nEnter the authorization code from eBay")
        
        # Exchange code for tokens
        tokens = client.exchange_code_for_tokens(auth_code)
        
        typer.echo(f"\n✅ OAuth2 setup successful!")
        typer.echo(f"\n🔐 Your tokens:")
        typer.echo(f"   Access Token: {tokens['access_token'][:20]}...")
        typer.echo(f"   Refresh Token: {tokens['refresh_token'][:20]}...")
        typer.echo(f"   Expires in: {tokens['expires_in']} seconds")
        
        typer.echo(f"\n📝 Add to your .env file:")
        typer.echo(f"   EBAY_REFRESH_TOKEN={tokens['refresh_token']}")
        
    except Exception as e:
        typer.echo(f"❌ OAuth2 setup failed: {e}", err=True)
        raise typer.Exit(1)


@ebay_app.command("list")
def create_ebay_listing(
    sku: str = typer.Option(..., help="Item SKU to list on eBay"),
    sandbox: bool = typer.Option(True, help="Use sandbox environment")
):
    """Create eBay listing directly via API."""
    
    try:
        from thriftbot.ebay_client import create_ebay_listing_from_sku, eBayAPIClient
        
        typer.echo(f"🚀 Creating eBay listing for {sku} ({'sandbox' if sandbox else 'production'})...")
        
        client = eBayAPIClient(sandbox=sandbox)
        result = create_ebay_listing_from_sku(sku, client)
        
        if result["success"]:
            typer.echo(f"\n✅ Listing created successfully!")
            typer.echo(f"   SKU: {result['sku']}")
            typer.echo(f"   Offer ID: {result['offer_id']}")
            if result.get("listing_id"):
                typer.echo(f"   Listing ID: {result['listing_id']}")
            typer.echo(f"   Status: {result['message']}")
            
            # Show next steps
            typer.echo(f"\n📝 Next Steps:")
            if sandbox:
                typer.echo(f"   - View in eBay Sandbox Seller Hub")
                typer.echo(f"   - Test with production: --no-sandbox")
            else:
                typer.echo(f"   - View in eBay Seller Hub")
                typer.echo(f"   - Monitor performance with: python -m thriftbot ebay orders")
            
        else:
            typer.echo(f"\n❌ Listing creation failed!")
            typer.echo(f"   Error: {result['error']}")
            typer.echo(f"   Message: {result['message']}")
            
    except Exception as e:
        typer.echo(f"❌ Error creating eBay listing: {e}", err=True)
        raise typer.Exit(1)


@ebay_app.command("research")
def market_research(
    keywords: str = typer.Option(..., help="Keywords to search for"),
    category: Optional[str] = typer.Option(None, help="eBay category ID"),
    limit: int = typer.Option(20, help="Number of results to show"),
    sandbox: bool = typer.Option(True, help="Use sandbox environment")
):
    """Research completed eBay listings for market data."""
    
    try:
        from thriftbot.ebay_client import eBayAPIClient
        from tabulate import tabulate
        
        typer.echo(f"🔍 Researching eBay market for: '{keywords}'...")
        
        client = eBayAPIClient(sandbox=sandbox)
        results = client.search_completed_items(keywords, category, limit)
        
        if results:
            typer.echo(f"\n📈 Found {len(results)} completed listings:")
            
            # Prepare table data
            table_data = []
            total_price = 0
            
            for item in results:
                price = item["price"]
                total_price += price
                
                table_data.append([
                    item["title"][:50] + "..." if len(item["title"]) > 50 else item["title"],
                    f"${price:.2f}",
                    item["condition"] or "N/A",
                    item["listing_type"] or "N/A"
                ])
            
            headers = ["Title", "Sold Price", "Condition", "Type"]
            typer.echo("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Summary stats
            avg_price = total_price / len(results)
            prices = [item["price"] for item in results]
            min_price = min(prices)
            max_price = max(prices)
            
            typer.echo(f"\n📊 Market Summary:")
            typer.echo(f"   Average Price: ${avg_price:.2f}")
            typer.echo(f"   Price Range: ${min_price:.2f} - ${max_price:.2f}")
            typer.echo(f"   Total Results: {len(results)}")
            
        else:
            typer.echo(f"\n⚠️  No completed listings found for '{keywords}'")
            
    except Exception as e:
        typer.echo(f"❌ Error researching market: {e}", err=True)
        raise typer.Exit(1)


@ebay_app.command("orders")
def check_orders(
    days: int = typer.Option(7, help="Days to look back for orders"),
    sandbox: bool = typer.Option(True, help="Use sandbox environment")
):
    """Check recent eBay orders and sync with inventory."""
    
    try:
        from thriftbot.ebay_client import eBayAPIClient, sync_orders_with_inventory
        from datetime import datetime, timedelta
        from tabulate import tabulate
        
        typer.echo(f"📦 Checking eBay orders from last {days} days...")
        
        client = eBayAPIClient(sandbox=sandbox)
        
        # Get recent orders
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        end_date = datetime.utcnow().isoformat() + "Z"
        
        orders = client.get_orders({
            "filter": f"creationdate:[{start_date}..{end_date}]",
            "limit": 50
        })
        
        order_list = orders.get("orders", [])
        
        if order_list:
            typer.echo(f"\n📄 Found {len(order_list)} recent orders:")
            
            table_data = []
            total_revenue = 0
            
            for order in order_list:
                order_id = order.get("orderId", "N/A")
                buyer = order.get("buyer", {}).get("username", "N/A")
                total = float(order.get("pricingSummary", {}).get("total", {}).get("value", 0))
                status = order.get("orderFulfillmentStatus", "N/A")
                
                total_revenue += total
                
                # Get item info
                items = []
                for line_item in order.get("lineItems", []):
                    sku = line_item.get("sku", "N/A")
                    title = line_item.get("title", "N/A")
                    items.append(f"{sku}: {title[:30]}...")
                
                table_data.append([
                    order_id[:15] + "..." if len(order_id) > 15 else order_id,
                    buyer,
                    f"${total:.2f}",
                    status,
                    "\n".join(items[:2])  # Show max 2 items
                ])
            
            headers = ["Order ID", "Buyer", "Total", "Status", "Items"]
            typer.echo("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
            
            typer.echo(f"\n💰 Revenue Summary:")
            typer.echo(f"   Total Revenue: ${total_revenue:.2f}")
            typer.echo(f"   Average Order: ${total_revenue/len(order_list):.2f}")
            typer.echo(f"   Orders: {len(order_list)}")
            
            # Sync with inventory
            if typer.confirm("\n🔄 Sync these orders with ThriftBot inventory?"):
                sync_result = sync_orders_with_inventory()
                
                if sync_result.get("success", True):
                    typer.echo(f"\n✅ Inventory sync complete:")
                    typer.echo(f"   Orders processed: {sync_result['orders_processed']}")
                    typer.echo(f"   Items updated: {sync_result['items_updated']}")
                    
                    if sync_result['errors']:
                        typer.echo(f"\n⚠️  Sync errors:")
                        for error in sync_result['errors']:
                            typer.echo(f"   - {error}")
                else:
                    typer.echo(f"\n❌ Sync failed: {sync_result['error']}")
            
        else:
            typer.echo(f"\n⚠️  No orders found in the last {days} days")
            
    except Exception as e:
        typer.echo(f"❌ Error checking orders: {e}", err=True)
        raise typer.Exit(1)


@ebay_app.command("status")
def check_ebay_status(
    sandbox: bool = typer.Option(True, help="Use sandbox environment")
):
    """Check eBay API connection status and account info."""
    
    try:
        from thriftbot.ebay_client import eBayAPIClient
        
        typer.echo(f"🔍 Checking eBay API status ({'sandbox' if sandbox else 'production'})...")
        
        client = eBayAPIClient(sandbox=sandbox)
        
        # Test authentication
        try:
            token = client.get_access_token()
            typer.echo(f"\n✅ Authentication: Success")
            typer.echo(f"   Access Token: {token[:20]}...")
        except Exception as e:
            typer.echo(f"\n❌ Authentication: Failed")
            typer.echo(f"   Error: {e}")
            typer.echo(f"\n💡 Run 'python -m thriftbot ebay setup' to configure OAuth2")
            return
        
        # Test API endpoints
        try:
            # Test inventory endpoint
            offers = client.get_offers()
            typer.echo(f"\n✅ Inventory API: Connected")
            typer.echo(f"   Active offers: {len(offers.get('offers', []))}")
        except Exception as e:
            typer.echo(f"\n⚠️  Inventory API: {e}")
        
        try:
            # Test orders endpoint
            orders = client.get_orders({"limit": 1})
            typer.echo(f"\n✅ Orders API: Connected")
            typer.echo(f"   Recent orders found: {orders.get('total', 0)}")
        except Exception as e:
            typer.echo(f"\n⚠️  Orders API: {e}")
        
        # Show environment info
        typer.echo(f"\n🌐 Environment Info:")
        typer.echo(f"   Mode: {'Sandbox' if sandbox else 'Production'}")
        typer.echo(f"   Sell API: {client.sell_api_base}")
        typer.echo(f"   Finding API: {client.finding_api_base}")
        
        if sandbox:
            typer.echo(f"\n💡 Ready for production? Use --no-sandbox flag")
        
    except Exception as e:
        typer.echo(f"❌ Error checking eBay status: {e}", err=True)
        raise typer.Exit(1)


@ebay_app.command("test")
def test_ebay_integration(
    sku: Optional[str] = typer.Option(None, help="Test with specific SKU"),
    sandbox: bool = typer.Option(True, help="Use sandbox environment")
):
    """Test eBay API integration with sample data."""
    
    try:
        from thriftbot.ebay_client import eBayAPIClient, _build_ebay_listing_data
        from thriftbot.db import get_inventory_items
        import json
        
        typer.echo(f"🧪 Testing eBay API integration ({'sandbox' if sandbox else 'production'})...")
        
        client = eBayAPIClient(sandbox=sandbox)
        
        # Get test item
        if sku:
            from thriftbot.db import get_item_by_sku
            item = get_item_by_sku(sku)
            if not item:
                typer.echo(f"❌ Item with SKU {sku} not found")
                return
        else:
            items = get_inventory_items()
            if not items:
                typer.echo(f"❌ No items found in inventory for testing")
                return
            item = items[0]
            sku = item.sku
        
        typer.echo(f"\n📄 Testing with item: {item.brand} {item.name} (SKU: {sku})")
        
        # Test listing data generation
        try:
            listing_data = _build_ebay_listing_data(item)
            typer.echo(f"\n✅ Listing data generation: Success")
            
            # Show preview of generated data
            inventory_item = listing_data["inventory_item"]
            offer = listing_data["offer"]
            
            typer.echo(f"\n📝 Generated Listing Preview:")
            typer.echo(f"   Title: {inventory_item['product']['title']}")
            typer.echo(f"   Price: ${offer['pricingSummary']['price']['value']}")
            typer.echo(f"   Condition: {inventory_item['condition']}")
            typer.echo(f"   Category: {offer['categoryId']}")
            
        except Exception as e:
            typer.echo(f"\n❌ Listing data generation: Failed ({e})")
            return
        
        # Test API connection
        try:
            token = client.get_access_token()
            typer.echo(f"\n✅ API Authentication: Success")
        except Exception as e:
            typer.echo(f"\n❌ API Authentication: Failed ({e})")
            return
        
        # Test dry-run listing creation
        if typer.confirm("\n🚀 Create actual test listing?"):
            try:
                result = create_ebay_listing_from_sku(sku, client)
                
                if result["success"]:
                    typer.echo(f"\n✅ Test listing created successfully!")
                    typer.echo(f"   Offer ID: {result['offer_id']}")
                    if result.get("listing_id"):
                        typer.echo(f"   Listing ID: {result['listing_id']}")
                else:
                    typer.echo(f"\n❌ Test listing failed: {result['error']}")
                    
            except Exception as e:
                typer.echo(f"\n❌ Test listing error: {e}")
        else:
            typer.echo(f"\n✅ Test completed without creating actual listing")
        
        typer.echo(f"\n🎉 eBay integration test complete!")
        
    except Exception as e:
        typer.echo(f"❌ Error testing eBay integration: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()