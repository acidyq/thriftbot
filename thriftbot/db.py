"""
ThriftBot Database Models and Operations

SQLModel-based database layer for inventory management and profit tracking.
"""

import os
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, DateTime, func

# Database configuration
DATABASE_URL = os.getenv("THRIFTBOT_DB", "sqlite:///thriftbot.db")
engine = create_engine(DATABASE_URL, echo=False)


class InventoryItem(SQLModel, table=True):
    """Main inventory item model with comprehensive tracking."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(index=True, unique=True)
    
    # Item details
    category: str
    brand: str
    name: str
    size: Optional[str] = None
    color: Optional[str] = None
    condition: str = "Good"
    
    # Cost tracking
    cost: Decimal = Field(decimal_places=2)
    
    # Pricing and profit
    suggested_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    listed_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    sold_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    
    # Fees (calculated automatically)
    listing_fee: Optional[Decimal] = Field(default=None, decimal_places=2)
    final_value_fee: Optional[Decimal] = Field(default=None, decimal_places=2)
    paypal_fee: Optional[Decimal] = Field(default=None, decimal_places=2)
    total_fees: Optional[Decimal] = Field(default=None, decimal_places=2)
    
    # Profit calculations
    gross_profit: Optional[Decimal] = Field(default=None, decimal_places=2)
    net_profit: Optional[Decimal] = Field(default=None, decimal_places=2)
    roi_percentage: Optional[Decimal] = Field(default=None, decimal_places=2)
    
    # Status tracking
    status: str = "inventory"  # inventory, listed, sold, returned
    
    # Photos
    photo_paths: Optional[str] = None  # JSON string of photo file paths
    processed_photos: Optional[str] = None  # JSON string of processed photo paths
    
    # eBay listing data
    ebay_listing_id: Optional[str] = None
    ebay_listing_json: Optional[str] = None  # For browser automation
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    listed_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None


class MarketComparable(SQLModel, table=True):
    """Market research data for pricing comparisons."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Search criteria
    search_term: str = Field(index=True)
    category: str
    brand: Optional[str] = None
    condition: Optional[str] = None
    
    # Comparable data
    title: str
    price: Decimal = Field(decimal_places=2)
    shipping_cost: Optional[Decimal] = Field(default=None, decimal_places=2)
    total_price: Decimal = Field(decimal_places=2)
    
    # Source info
    platform: str = "ebay"  # ebay, mercari, poshmark, etc.
    listing_url: Optional[str] = None
    seller_rating: Optional[str] = None
    
    # Status
    listing_status: str = "active"  # active, sold, ended
    
    # Timestamps
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


def init_database():
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session


def add_item_to_inventory(
    sku: str,
    category: str,
    brand: str,
    name: str,
    cost: float,
    size: Optional[str] = None,
    color: Optional[str] = None,
    condition: str = "Good"
) -> int:
    """Add a new item to inventory."""
    
    item = InventoryItem(
        sku=sku,
        category=category,
        brand=brand,
        name=name,
        size=size,
        color=color,
        condition=condition,
        cost=Decimal(str(cost))
    )
    
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item.id


def get_inventory_items(
    status: Optional[str] = None,
    category: Optional[str] = None
) -> List[InventoryItem]:
    """Get inventory items with optional filtering."""
    
    with Session(engine) as session:
        statement = select(InventoryItem)
        
        if status:
            statement = statement.where(InventoryItem.status == status)
        if category:
            statement = statement.where(InventoryItem.category == category)
            
        items = session.exec(statement).all()
        return list(items)


def get_item_by_sku(sku: str) -> Optional[InventoryItem]:
    """Get an inventory item by SKU."""
    
    with Session(engine) as session:
        statement = select(InventoryItem).where(InventoryItem.sku == sku)
        item = session.exec(statement).first()
        return item


def update_item_pricing(
    sku: str,
    suggested_price: Optional[float] = None,
    listed_price: Optional[float] = None,
    sold_price: Optional[float] = None
) -> bool:
    """Update item pricing and calculate profits."""
    
    with Session(engine) as session:
        statement = select(InventoryItem).where(InventoryItem.sku == sku)
        item = session.exec(statement).first()
        
        if not item:
            return False
            
        # Update pricing
        if suggested_price is not None:
            item.suggested_price = Decimal(str(suggested_price))
        if listed_price is not None:
            item.listed_price = Decimal(str(listed_price))
        if sold_price is not None:
            item.sold_price = Decimal(str(sold_price))
            item.status = "sold"
            item.sold_at = datetime.utcnow()
            
            # Calculate fees and profits
            _calculate_fees_and_profit(item)
        
        session.add(item)
        session.commit()
        return True


def _calculate_fees_and_profit(item: InventoryItem):
    """Calculate eBay fees and profit margins."""
    
    if not item.sold_price:
        return
        
    # eBay fee structure (approximate)
    # Final value fee: 10% of total amount (item + shipping)
    # PayPal fee: 2.9% + $0.30
    # Listing fee: $0 for basic listings
    
    sold_price = item.sold_price
    
    # Calculate fees
    item.listing_fee = Decimal("0.00")  # Basic listings are free
    item.final_value_fee = sold_price * Decimal("0.10")  # 10% final value fee
    item.paypal_fee = (sold_price * Decimal("0.029")) + Decimal("0.30")  # PayPal fees
    
    item.total_fees = item.listing_fee + item.final_value_fee + item.paypal_fee
    
    # Calculate profits
    item.gross_profit = sold_price - item.cost
    item.net_profit = item.gross_profit - item.total_fees
    
    # Calculate ROI percentage
    if item.cost > 0:
        item.roi_percentage = (item.net_profit / item.cost) * 100


def add_market_comparable(
    search_term: str,
    category: str,
    title: str,
    price: float,
    platform: str = "ebay",
    brand: Optional[str] = None,
    condition: Optional[str] = None,
    shipping_cost: Optional[float] = None,
    listing_url: Optional[str] = None
) -> int:
    """Add market comparable data."""
    
    total_price = Decimal(str(price))
    if shipping_cost:
        total_price += Decimal(str(shipping_cost))
    
    comparable = MarketComparable(
        search_term=search_term,
        category=category,
        brand=brand,
        condition=condition,
        title=title,
        price=Decimal(str(price)),
        shipping_cost=Decimal(str(shipping_cost)) if shipping_cost else None,
        total_price=total_price,
        platform=platform,
        listing_url=listing_url
    )
    
    with Session(engine) as session:
        session.add(comparable)
        session.commit()
        session.refresh(comparable)
        return comparable.id