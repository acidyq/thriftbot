"""
ThriftBot Pricing Analysis

Market research and pricing suggestion system for optimal eBay listing prices.
"""

import os
from typing import Dict, List, Optional, Any
from decimal import Decimal
from statistics import mean, median
from datetime import datetime, timedelta

from thriftbot.db import get_item_by_sku, InventoryItem, add_market_comparable, MarketComparable, Session, engine, select


def analyze_item_pricing(sku: str) -> Dict[str, Any]:
    """Analyze pricing for an inventory item with market research."""
    
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    # Get market comparables
    market_data = get_market_comparables(item)
    
    # Calculate suggested pricing
    pricing_analysis = calculate_pricing_suggestions(item, market_data)
    
    # Calculate potential profits at different price points
    profit_scenarios = calculate_profit_scenarios(item, pricing_analysis["suggested_prices"])
    
    return {
        "sku": sku,
        "item_info": {
            "brand": item.brand,
            "name": item.name,
            "category": item.category,
            "condition": item.condition,
            "cost": float(item.cost)
        },
        "market_data": market_data,
        "pricing_analysis": pricing_analysis,
        "profit_scenarios": profit_scenarios,
        "recommendations": generate_pricing_recommendations(item, pricing_analysis, profit_scenarios)
    }


def get_market_comparables(item: InventoryItem, limit: int = 20) -> Dict[str, Any]:
    """Get market comparable data for similar items."""
    
    with Session(engine) as session:
        # Search for similar items
        search_terms = [
            f"{item.brand} {item.name}",
            f"{item.brand}",
            item.name
        ]
        
        comparables = []
        for search_term in search_terms:
            statement = select(MarketComparable).where(
                MarketComparable.search_term.contains(search_term)
            ).limit(limit)
            
            results = session.exec(statement).all()
            comparables.extend(results)
        
        # If no data found, create sample data for demo
        if not comparables:
            comparables = generate_sample_comparables(item)
        
        # Calculate statistics
        prices = [float(comp.total_price) for comp in comparables]
        
        return {
            "total_comparables": len(comparables),
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "average": round(mean(prices), 2) if prices else 0,
                "median": round(median(prices), 2) if prices else 0
            },
            "recent_sales": [
                {
                    "title": comp.title,
                    "price": float(comp.price),
                    "total_price": float(comp.total_price),
                    "platform": comp.platform,
                    "status": comp.listing_status,
                    "scraped_date": comp.scraped_at.strftime("%Y-%m-%d") if comp.scraped_at else None
                }
                for comp in comparables[:10]  # Show top 10
            ]
        }


def calculate_pricing_suggestions(item: InventoryItem, market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate suggested pricing based on market data and item cost."""
    
    cost = float(item.cost)
    market_average = market_data["price_range"]["average"]
    market_median = market_data["price_range"]["median"]
    market_min = market_data["price_range"]["min"]
    market_max = market_data["price_range"]["max"]
    
    # Base calculations on market data if available
    if market_average > 0:
        # Conservative pricing strategy
        conservative_price = max(cost * 2, market_average * 0.8)
        
        # Competitive pricing strategy
        competitive_price = market_median if market_median > cost * 1.5 else cost * 2
        
        # Aggressive pricing strategy
        aggressive_price = min(market_average * 1.2, market_max * 0.9)
        
    else:
        # Enhanced fallback pricing with category-specific multipliers
        category_multipliers = {
            "clothing": {"conservative": 4, "competitive": 5, "aggressive": 6},
            "electronics": {"conservative": 2, "competitive": 3, "aggressive": 4},
            "home & garden": {"conservative": 3, "competitive": 4, "aggressive": 5},
            "sports & outdoors": {"conservative": 3.5, "competitive": 4.5, "aggressive": 6},
            "collectibles": {"conservative": 4, "competitive": 6, "aggressive": 8}
        }
        
        # Determine category multiplier
        category_key = item.category.lower() if item.category else "clothing"
        multipliers = None
        for key, mult in category_multipliers.items():
            if key in category_key or category_key in key:
                multipliers = mult
                break
        
        if not multipliers:
            multipliers = category_multipliers["clothing"]  # Default to clothing
        
        # Apply category-specific multipliers
        conservative_price = cost * multipliers["conservative"]
        competitive_price = cost * multipliers["competitive"] 
        aggressive_price = cost * multipliers["aggressive"]
    
    # Condition adjustments
    condition_multipliers = {
        "New": 1.0,
        "Excellent": 0.9,
        "Very Good": 0.8,
        "Good": 0.7,
        "Fair": 0.6,
        "Poor": 0.5
    }
    
    condition_multiplier = condition_multipliers.get(item.condition, 0.7)
    
    # Apply condition adjustments
    conservative_price *= condition_multiplier
    competitive_price *= condition_multiplier
    aggressive_price *= condition_multiplier
    
    # Ensure minimum profit margins
    min_price = cost * 1.5  # Minimum 50% markup
    conservative_price = max(conservative_price, min_price)
    competitive_price = max(competitive_price, min_price)
    aggressive_price = max(aggressive_price, min_price)
    
    return {
        "suggested_prices": {
            "conservative": round(conservative_price, 2),
            "competitive": round(competitive_price, 2),
            "aggressive": round(aggressive_price, 2)
        },
        "market_position": {
            "below_market": round(market_average * 0.8, 2) if market_average > 0 else 0,
            "at_market": round(market_average, 2) if market_average > 0 else 0,
            "above_market": round(market_average * 1.2, 2) if market_average > 0 else 0
        },
        "condition_adjustment": f"{int((condition_multiplier - 1) * 100)}%" if condition_multiplier != 1 else "None"
    }


def calculate_profit_scenarios(item: InventoryItem, suggested_prices: Dict[str, float]) -> List[Dict[str, Any]]:
    """Calculate profit scenarios for different price points."""
    
    scenarios = []
    cost = float(item.cost)
    
    for strategy, price in suggested_prices.items():
        # Calculate fees (using the same logic as database model)
        listing_fee = 0.00  # Basic listings are free
        final_value_fee = price * 0.10  # 10% final value fee
        paypal_fee = (price * 0.029) + 0.30  # PayPal fees
        total_fees = listing_fee + final_value_fee + paypal_fee
        
        # Calculate profits
        gross_profit = price - cost
        net_profit = gross_profit - total_fees
        roi_percentage = (net_profit / cost) * 100 if cost > 0 else 0
        
        scenarios.append({
            "strategy": strategy.title(),
            "price": price,
            "fees": {
                "listing_fee": round(listing_fee, 2),
                "final_value_fee": round(final_value_fee, 2),
                "paypal_fee": round(paypal_fee, 2),
                "total_fees": round(total_fees, 2)
            },
            "profit": {
                "gross_profit": round(gross_profit, 2),
                "net_profit": round(net_profit, 2),
                "roi_percentage": round(roi_percentage, 1)
            }
        })
    
    return scenarios


def generate_pricing_recommendations(
    item: InventoryItem,
    pricing_analysis: Dict[str, Any],
    profit_scenarios: List[Dict[str, Any]]
) -> List[str]:
    """Generate actionable pricing recommendations."""
    
    recommendations = []
    cost = float(item.cost)
    
    # Analyze profit scenarios
    best_roi_scenario = max(profit_scenarios, key=lambda x: x["profit"]["roi_percentage"])
    
    recommendations.append(
        f"Best ROI: {best_roi_scenario['strategy']} pricing at ${best_roi_scenario['price']} "
        f"({best_roi_scenario['profit']['roi_percentage']}% ROI)"
    )
    
    # Check if any scenarios have low profit
    low_profit_scenarios = [s for s in profit_scenarios if s["profit"]["net_profit"] < cost]
    if low_profit_scenarios:
        recommendations.append(
            f"⚠️  {len(low_profit_scenarios)} pricing strategies show low profit margins"
        )
    
    # Market position recommendations
    market_avg = pricing_analysis.get("market_position", {}).get("at_market", 0)
    if market_avg > 0:
        competitive_price = pricing_analysis["suggested_prices"]["competitive"]
        if competitive_price < market_avg * 0.9:
            recommendations.append("💰 Your competitive price is below market average - good for quick sales")
        elif competitive_price > market_avg * 1.1:
            recommendations.append("⏰ Your competitive price is above market - may take longer to sell")
    
    # Category-specific recommendations
    category_tips = get_category_pricing_tips(item.category)
    recommendations.extend(category_tips)
    
    # Condition-specific recommendations
    if item.condition in ["Fair", "Poor"]:
        recommendations.append("📸 Include detailed photos of flaws to justify pricing and avoid returns")
    elif item.condition in ["New", "Excellent"]:
        recommendations.append("✨ Highlight excellent condition in title and description for premium pricing")
    
    return recommendations


def get_category_pricing_tips(category: str) -> List[str]:
    """Get category-specific pricing recommendations."""
    
    tips = {
        "clothing": [
            "🏷️  Consider brand recognition - designer brands can command higher prices",
            "📏 Size matters - popular sizes (M, L) typically sell for more",
            "🎯 Check for seasonal demand (coats in fall, swimwear in spring)"
        ],
        "electronics": [
            "🔋 Working condition is critical - test all functions before pricing",
            "📱 Check current market prices as tech depreciates quickly",
            "📦 Include all original accessories to maximize value"
        ],
        "home": [
            "🏠 Vintage and antique items may have collector value",
            "🎨 Unique or handmade items can command premium pricing",
            "📐 Large items factor in shipping costs to final price"
        ],
        "books": [
            "📚 First editions and rare books have higher value",
            "🎓 Textbooks have seasonal demand (back-to-school)",
            "⭐ Check condition carefully - book collectors are picky"
        ],
        "toys": [
            "🧸 Vintage toys from the 70s-90s can be very valuable",
            "📦 Original packaging significantly increases value",
            "🎮 Complete sets with all pieces sell for more"
        ]
    }
    
    return tips.get(category.lower(), [
        "🔍 Research similar items to understand market value",
        "💡 Unique or rare items can command higher prices"
    ])


def generate_sample_comparables(item: InventoryItem) -> List[MarketComparable]:
    """Generate sample comparable data when no real data is available."""
    
    from random import uniform, choice
    
    # Category-specific base price multipliers for realistic market pricing
    category_ranges = {
        "clothing": (4.0, 8.0),     # 4x-8x cost (e.g., $3.75 → $15-30)
        "electronics": (2.0, 5.0),  # Electronics depreciate more
        "home & garden": (3.0, 6.0),
        "sports & outdoors": (3.5, 7.0),
        "collectibles": (5.0, 12.0)
    }
    
    # Determine category
    category_key = item.category.lower() if item.category else "clothing"
    price_range = None
    for key, range_vals in category_ranges.items():
        if key in category_key or category_key in key:
            price_range = range_vals
            break
    
    if not price_range:
        price_range = category_ranges["clothing"]  # Default to clothing
    
    # Base price estimation with realistic market multipliers
    base_price = float(item.cost) * uniform(price_range[0], price_range[1])
    
    sample_data = []
    
    # Generate 5-10 sample comparables with price variation
    for i in range(7):
        price_variation = uniform(0.8, 1.4)  # More realistic variation
        price = base_price * price_variation
        
        # Create comparable entry
        comparable = MarketComparable(
            search_term=f"{item.brand} {item.name}",
            category=item.category,
            brand=item.brand,
            condition=choice(["New", "Excellent", "Very Good", "Good"]),
            title=f"{item.brand} {item.name} - {choice(['Size M', 'Great Condition', 'Vintage', 'Rare Find'])}",
            price=Decimal(str(round(price, 2))),
            shipping_cost=Decimal("0.00"),
            total_price=Decimal(str(round(price, 2))),
            platform="ebay",
            listing_status=choice(["sold", "active"]),
            scraped_at=datetime.utcnow() - timedelta(days=uniform(1, 30))
        )
        sample_data.append(comparable)
    
    return sample_data


def update_market_data_from_research(
    search_term: str,
    category: str,
    research_data: List[Dict[str, Any]]
) -> int:
    """Update market comparable data from external research."""
    
    added_count = 0
    
    for data in research_data:
        try:
            comparable_id = add_market_comparable(
                search_term=search_term,
                category=category,
                title=data.get("title", ""),
                price=data.get("price", 0),
                platform=data.get("platform", "ebay"),
                brand=data.get("brand"),
                condition=data.get("condition"),
                shipping_cost=data.get("shipping_cost"),
                listing_url=data.get("url")
            )
            added_count += 1
            
        except Exception as e:
            print(f"Failed to add comparable: {e}")
    
    return added_count


def get_pricing_history(sku: str) -> Dict[str, Any]:
    """Get pricing history for an item if it has been analyzed before."""
    
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    # This would be extended to track pricing analysis history
    # For now, return current state
    return {
        "sku": sku,
        "current_prices": {
            "suggested": float(item.suggested_price) if item.suggested_price else None,
            "listed": float(item.listed_price) if item.listed_price else None,
            "sold": float(item.sold_price) if item.sold_price else None
        },
        "history": [],  # Would track price changes over time
        "performance": {
            "days_listed": None,  # Would calculate from listed_at
            "price_changes": 0,   # Would track modifications
            "views": None,        # Would integrate with eBay API
            "watchers": None      # Would integrate with eBay API
        }
    }


def suggest_price_adjustments(sku: str) -> Dict[str, Any]:
    """Suggest price adjustments for items that aren't selling."""
    
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    suggestions = []
    current_price = float(item.listed_price) if item.listed_price else None
    
    if not current_price:
        return {"message": "Item not yet listed - no adjustments needed"}
    
    # Time-based adjustments (would use actual listing date)
    days_listed = 14  # Placeholder - would calculate from listed_at
    
    if days_listed > 30:
        # Suggest price reduction for old listings
        new_price = current_price * 0.9
        suggestions.append({
            "type": "price_reduction",
            "current_price": current_price,
            "suggested_price": round(new_price, 2),
            "reason": "Listed for over 30 days - consider 10% price reduction",
            "urgency": "medium"
        })
    
    elif days_listed > 60:
        # More aggressive reduction
        new_price = current_price * 0.8
        suggestions.append({
            "type": "aggressive_reduction",
            "current_price": current_price,
            "suggested_price": round(new_price, 2),
            "reason": "Listed for over 60 days - consider significant price reduction or auction format",
            "urgency": "high"
        })
    
    # Market comparison adjustments
    market_data = get_market_comparables(item, limit=10)
    market_avg = market_data["price_range"]["average"]
    
    if market_avg > 0 and current_price > market_avg * 1.2:
        suggestions.append({
            "type": "market_adjustment",
            "current_price": current_price,
            "suggested_price": round(market_avg, 2),
            "reason": f"Current price is {int((current_price/market_avg-1)*100)}% above market average",
            "urgency": "medium"
        })
    
    return {
        "sku": sku,
        "current_price": current_price,
        "days_listed": days_listed,
        "suggestions": suggestions,
        "market_context": market_data["price_range"]
    }


def calculate_break_even_price(sku: str) -> Dict[str, Any]:
    """Calculate break-even price considering all costs and fees."""
    
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    cost = float(item.cost)
    
    # Calculate minimum price to break even
    # Price = (Cost + Fixed Fees) / (1 - Variable Fee Rate)
    # eBay: 10% final value fee + PayPal: 2.9% + $0.30
    
    fixed_fees = 0.30  # PayPal fixed fee
    variable_rate = 0.10 + 0.029  # eBay + PayPal variable rates
    
    break_even_price = (cost + fixed_fees) / (1 - variable_rate)
    
    # Add small margin for true break-even
    break_even_with_margin = break_even_price * 1.05  # 5% buffer
    
    return {
        "sku": sku,
        "item_cost": cost,
        "break_even_price": round(break_even_price, 2),
        "break_even_with_margin": round(break_even_with_margin, 2),
        "fee_breakdown": {
            "fixed_fees": fixed_fees,
            "variable_rate_percentage": round(variable_rate * 100, 1),
            "estimated_fees_at_break_even": round(break_even_price * variable_rate + fixed_fees, 2)
        },
        "recommendation": f"Minimum listing price: ${round(break_even_with_margin, 2)}"
    }