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

# AI commands (for future implementation)
ai_app = typer.Typer(help="AI-powered content generation")
app.add_typer(ai_app, name="ai")


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
def list_items():
    """List all inventory items."""
    # TODO: Implement item listing
    typer.echo("📋 Item listing functionality coming soon...")


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


if __name__ == "__main__":
    app()