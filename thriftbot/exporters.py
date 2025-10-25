"""
ThriftBot Data Exporters

Export functionality for eBay-compatible CSV and other formats.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from thriftbot.db import get_inventory_items, InventoryItem


def export_to_ebay_csv(
    output_path: str,
    include_sold: bool = False,
    category_filter: str = None
) -> Dict[str, Any]:
    """Export inventory to eBay-compatible CSV format."""
    
    # Get inventory items
    items = get_inventory_items()
    
    if not include_sold:
        items = [item for item in items if item.status != "sold"]
        
    if category_filter:
        items = [item for item in items if item.category.lower() == category_filter.lower()]
    
    # eBay CSV headers (standard bulk upload format)
    headers = [
        "Action(SiteID=US|Country=US|Currency=USD|Version=1193)",
        "Category",
        "Title",
        "Description", 
        "PicURL",
        "Quantity",
        "Format",
        "Duration",
        "StartPrice",
        "BuyItNowPrice",
        "ReservePrice",
        "ImmediatePayRequired",
        "PayPalEmailAddress",
        "ShippingType",
        "ShipToLocations",
        "ShippingService-1:Option",
        "ShippingService-1:Cost",
        "DispatchTimeMax",
        "Location",
        "ConditionID",
        "ConditionDescription",
        "Brand",
        "Size",
        "Color",
        "ReturnPolicy.ReturnsAcceptedOption",
        "ReturnPolicy.ReturnsWithinOption",
        "ReturnPolicy.ShippingCostPaidByOption"
    ]
    
    # Write CSV file
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for item in items:
            row = _create_ebay_csv_row(item)
            writer.writerow(row)
    
    return {
        "count": len(items),
        "path": output_path,
        "exported_at": datetime.utcnow().isoformat()
    }


def _create_ebay_csv_row(item: InventoryItem) -> List[str]:
    """Create a CSV row for eBay from an inventory item."""
    
    # Generate title and description
    title = f"{item.brand} {item.name}"
    if item.size:
        title += f" Size {item.size}"
    if item.color:
        title += f" {item.color}"
    
    # Truncate title to eBay's 80 character limit
    title = title[:80]
    
    # Basic description
    description = f"""
    <p><strong>Brand:</strong> {item.brand}</p>
    <p><strong>Item:</strong> {item.name}</p>
    <p><strong>Condition:</strong> {item.condition}</p>
    """
    
    if item.size:
        description += f"<p><strong>Size:</strong> {item.size}</p>"
    if item.color:
        description += f"<p><strong>Color:</strong> {item.color}</p>"
    
    description += """
    <p>Please see photos for exact condition and details.</p>
    <p>Fast shipping! We ship within 1 business day.</p>
    <p>Returns accepted within 30 days.</p>
    """
    
    # Determine condition ID (eBay's condition codes)
    condition_map = {
        "New": "1000",
        "New with Tags": "1000", 
        "New without Tags": "1500",
        "Excellent": "2000",
        "Very Good": "2500",
        "Good": "3000",
        "Fair": "4000",
        "Poor": "5000"
    }
    
    condition_id = condition_map.get(item.condition, "3000")  # Default to Good
    
    # Determine listing price
    listing_price = ""
    if item.listed_price:
        listing_price = str(item.listed_price)
    elif item.suggested_price:
        listing_price = str(item.suggested_price)
    
    # Create the row
    row = [
        "Add",  # Action
        "",  # Category - will be determined by eBay
        title,  # Title
        description,  # Description
        "",  # PicURL - will be uploaded separately
        "1",  # Quantity
        "FixedPrice",  # Format
        "GTC",  # Duration (Good Till Cancelled)
        "",  # StartPrice (not used for fixed price)
        listing_price,  # BuyItNowPrice
        "",  # ReservePrice
        "1",  # ImmediatePayRequired
        "",  # PayPalEmailAddress - will use default
        "Flat",  # ShippingType
        "US",  # ShipToLocations
        "USPSPriority",  # ShippingService-1:Option
        "12.99",  # ShippingService-1:Cost
        "1",  # DispatchTimeMax
        "United States",  # Location
        condition_id,  # ConditionID
        item.condition,  # ConditionDescription
        item.brand,  # Brand
        item.size or "",  # Size
        item.color or "",  # Color
        "ReturnsAccepted",  # Returns accepted
        "Days_30",  # Returns within 30 days
        "Buyer"  # Return shipping paid by buyer
    ]
    
    return row


def export_to_json(
    output_path: str,
    include_sold: bool = False,
    format_for_automation: bool = False
) -> Dict[str, Any]:
    """Export inventory to JSON format."""
    
    items = get_inventory_items()
    
    if not include_sold:
        items = [item for item in items if item.status != "sold"]
    
    if format_for_automation:
        # Format for browser automation
        export_data = {
            "export_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_items": len(items),
                "purpose": "browser_automation"
            },
            "listings": []
        }
        
        for item in items:
            listing = _create_automation_listing(item)
            export_data["listings"].append(listing)
    else:
        # Standard JSON export
        export_data = {
            "export_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_items": len(items)
            },
            "items": [_item_to_dict(item) for item in items]
        }
    
    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(export_data, jsonfile, indent=2, default=str)
    
    return {
        "count": len(items),
        "path": output_path,
        "exported_at": datetime.utcnow().isoformat()
    }


def _create_automation_listing(item: InventoryItem) -> Dict[str, Any]:
    """Create a listing object formatted for browser automation."""
    
    title = f"{item.brand} {item.name}"
    if item.size:
        title += f" Size {item.size}"
    if item.color:
        title += f" {item.color}"
    
    # Price determination
    price = None
    if item.listed_price:
        price = float(item.listed_price)
    elif item.suggested_price:
        price = float(item.suggested_price)
    
    return {
        "sku": item.sku,
        "title": title[:80],  # eBay limit
        "category": item.category,
        "brand": item.brand,
        "condition": item.condition,
        "price": price,
        "description": {
            "brand": item.brand,
            "name": item.name,
            "size": item.size,
            "color": item.color,
            "condition": item.condition
        },
        "shipping": {
            "method": "USPS Priority Mail",
            "cost": 12.99,
            "handling_time": 1
        },
        "return_policy": {
            "returns_accepted": True,
            "return_period": 30,
            "return_shipping_paid_by": "Buyer"
        },
        "photos": {
            "paths": json.loads(item.processed_photos) if item.processed_photos else [],
            "upload_required": True
        }
    }


def _item_to_dict(item: InventoryItem) -> Dict[str, Any]:
    """Convert inventory item to dictionary."""
    
    return {
        "id": item.id,
        "sku": item.sku,
        "category": item.category,
        "brand": item.brand,
        "name": item.name,
        "size": item.size,
        "color": item.color,
        "condition": item.condition,
        "cost": float(item.cost) if item.cost else None,
        "suggested_price": float(item.suggested_price) if item.suggested_price else None,
        "listed_price": float(item.listed_price) if item.listed_price else None,
        "sold_price": float(item.sold_price) if item.sold_price else None,
        "fees": {
            "listing_fee": float(item.listing_fee) if item.listing_fee else None,
            "final_value_fee": float(item.final_value_fee) if item.final_value_fee else None,
            "paypal_fee": float(item.paypal_fee) if item.paypal_fee else None,
            "total_fees": float(item.total_fees) if item.total_fees else None
        },
        "profit": {
            "gross_profit": float(item.gross_profit) if item.gross_profit else None,
            "net_profit": float(item.net_profit) if item.net_profit else None,
            "roi_percentage": float(item.roi_percentage) if item.roi_percentage else None
        },
        "status": item.status,
        "photos": {
            "original": json.loads(item.photo_paths) if item.photo_paths else [],
            "processed": json.loads(item.processed_photos) if item.processed_photos else []
        },
        "timestamps": {
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "listed_at": item.listed_at.isoformat() if item.listed_at else None,
            "sold_at": item.sold_at.isoformat() if item.sold_at else None
        }
    }


def create_sample_comps_csv():
    """Create a sample comparables CSV file for testing."""
    
    output_path = "comps/sample_comps.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    sample_data = [
        {
            "search_term": "patagonia better sweater",
            "category": "Clothing",
            "brand": "Patagonia",
            "title": "Patagonia Better Sweater Fleece Jacket Men's Medium Navy",
            "price": 45.99,
            "condition": "Good",
            "platform": "ebay",
            "status": "sold"
        },
        {
            "search_term": "patagonia better sweater", 
            "category": "Clothing",
            "brand": "Patagonia",
            "title": "Patagonia Better Sweater 1/4 Zip Pullover Women's Small Gray",
            "price": 38.50,
            "condition": "Very Good",
            "platform": "ebay",
            "status": "sold"
        },
        {
            "search_term": "levi 501 jeans",
            "category": "Clothing",
            "brand": "Levi's",
            "title": "Vintage Levi's 501 Original Fit Jeans 32x30 Blue Denim",
            "price": 28.99,
            "condition": "Good",
            "platform": "ebay", 
            "status": "active"
        }
    ]
    
    headers = ["search_term", "category", "brand", "title", "price", "condition", "platform", "status"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sample_data)
    
    return output_path