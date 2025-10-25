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
    use_ai: bool = typer.Option(False, help="Use AI for description generation")
):
    """Generate item title and description."""
    # TODO: Implement AI description generation
    if use_ai:
        typer.echo("🤖 AI description generation coming soon...")
    else:
        typer.echo("📝 Template-based description generation coming soon...")


if __name__ == "__main__":
    app()