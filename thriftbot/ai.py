"""
ThriftBot AI Integration

AI-powered content generation for eBay listings using OpenAI.
"""

import os
from typing import Dict, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

from thriftbot.db import get_item_by_sku, InventoryItem

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_listing_content(
    sku: str,
    style: str = "professional",
    include_keywords: bool = True,
    max_title_length: int = 80
) -> Dict[str, str]:
    """Generate AI-powered title and description for an inventory item."""
    
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your-"):
        return _generate_template_content(item, style, max_title_length)
    
    try:
        # Generate AI content
        title = _generate_ai_title(item, max_title_length)
        description = _generate_ai_description(item, style, include_keywords)
        
        return {
            "title": title,
            "description": description,
            "generated_by": "ai",
            "style": style
        }
        
    except Exception as e:
        print(f"⚠️  AI generation failed: {e}")
        print("🔄 Falling back to template generation...")
        return _generate_template_content(item, style, max_title_length)


def _generate_ai_title(item: InventoryItem, max_length: int = 80) -> str:
    """Generate an optimized eBay title using AI."""
    
    prompt = f"""
    Create an optimized eBay listing title for this item:
    
    Brand: {item.brand}
    Item: {item.name}
    Category: {item.category}
    Size: {item.size or "N/A"}
    Color: {item.color or "N/A"}
    Condition: {item.condition}
    
    Requirements:
    - Maximum {max_length} characters
    - Include brand name prominently
    - Use eBay-friendly keywords for searchability
    - Include size and color if available
    - Professional tone
    - No promotional language like "LOOK!" or "WOW!"
    
    Return only the title, nothing else.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0.3
    )
    
    title = response.choices[0].message.content.strip()
    return title[:max_length]  # Ensure length limit


def _generate_ai_description(
    item: InventoryItem,
    style: str = "professional",
    include_keywords: bool = True
) -> str:
    """Generate an optimized eBay description using AI."""
    
    style_prompts = {
        "professional": "Professional and detailed, highlighting quality and value",
        "casual": "Friendly and conversational, like talking to a friend",
        "enthusiastic": "Excited and energetic, emphasizing the great find",
        "minimalist": "Clean and concise, focusing on key details only"
    }
    
    style_instruction = style_prompts.get(style, style_prompts["professional"])
    
    prompt = f"""
    Create an eBay listing description for this thrift store find:
    
    Brand: {item.brand}
    Item: {item.name}
    Category: {item.category}
    Size: {item.size or "Not specified"}
    Color: {item.color or "See photos"}
    Condition: {item.condition}
    Cost basis: ${float(item.cost)}
    
    Style: {style_instruction}
    
    Requirements:
    - Write in HTML format for eBay listings
    - Include condition details and what to expect
    - Mention fast shipping and return policy
    - {f"Include relevant search keywords naturally" if include_keywords else "Focus on description without keyword stuffing"}
    - Encourage buyers to ask questions
    - Professional but approachable tone
    - Highlight the value proposition
    - 150-300 words
    
    Structure:
    1. Item overview and key features
    2. Condition description
    3. Measurements/sizing (if applicable)
    4. Shipping and return info
    5. Call to action
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.4
    )
    
    return response.choices[0].message.content.strip()


def _generate_template_content(
    item: InventoryItem,
    style: str = "professional",
    max_title_length: int = 80
) -> Dict[str, str]:
    """Generate template-based content when AI is not available."""
    
    # Generate title
    title_parts = [item.brand, item.name]
    if item.size:
        title_parts.append(f"Size {item.size}")
    if item.color:
        title_parts.append(item.color)
    title_parts.append(item.condition)
    
    title = " ".join(title_parts)[:max_title_length]
    
    # Generate description based on style
    if style == "minimalist":
        description = f"""
        <div>
        <p><strong>{item.brand} {item.name}</strong></p>
        <p>Condition: {item.condition}</p>
        {f"<p>Size: {item.size}</p>" if item.size else ""}
        {f"<p>Color: {item.color}</p>" if item.color else ""}
        <p>Fast shipping within 1 business day.</p>
        <p>30-day returns accepted.</p>
        </div>
        """
    else:
        description = f"""
        <div>
        <h3>{item.brand} {item.name}</h3>
        
        <p>Great find from our thrift collection! This <strong>{item.brand} {item.name}</strong> 
        is in <strong>{item.condition}</strong> condition and ready for a new home.</p>
        
        <p><strong>Details:</strong></p>
        <ul>
        <li>Brand: {item.brand}</li>
        <li>Item: {item.name}</li>
        <li>Condition: {item.condition}</li>
        {f"<li>Size: {item.size}</li>" if item.size else ""}
        {f"<li>Color: {item.color}</li>" if item.color else ""}
        </ul>
        
        <p>Please review photos carefully as they are part of the description. 
        Items are gently used thrift finds and may show normal wear consistent with age and use.</p>
        
        <p><strong>Shipping & Returns:</strong></p>
        <ul>
        <li>Fast shipping within 1 business day</li>
        <li>30-day returns accepted</li>
        <li>Careful packaging to ensure safe delivery</li>
        </ul>
        
        <p>Questions? Please feel free to message us - we're happy to help!</p>
        </div>
        """
    
    return {
        "title": title,
        "description": description,
        "generated_by": "template",
        "style": style
    }


def suggest_keywords(item: InventoryItem, count: int = 10) -> List[str]:
    """Suggest relevant keywords for the item using AI."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your-"):
        return _get_template_keywords(item, count)
    
    try:
        prompt = f"""
        Generate {count} relevant eBay search keywords for this item:
        
        Brand: {item.brand}
        Item: {item.name}
        Category: {item.category}
        Size: {item.size or "N/A"}
        Color: {item.color or "N/A"}
        
        Requirements:
        - Focus on what buyers would search for
        - Include brand, item type, and key attributes
        - Mix specific and general terms
        - No duplicate or overly similar keywords
        - Return as a comma-separated list
        
        Example: vintage, authentic, designer, size medium, navy blue, cotton
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content.strip()
        # Handle both comma-separated and numbered list responses
        if keywords_text.startswith("1."):
            # Handle numbered list format
            lines = keywords_text.split("\n")
            keywords = []
            for line in lines:
                if ". " in line:
                    keyword = line.split(". ", 1)[1].strip()
                    if keyword:
                        keywords.append(keyword)
        else:
            # Handle comma-separated format
            keywords = [k.strip() for k in keywords_text.split(",")]
        
        return keywords[:count]
        
    except Exception as e:
        print(f"⚠️  AI keyword generation failed: {e}")
        return _get_template_keywords(item, count)


def _get_template_keywords(item: InventoryItem, count: int = 10) -> List[str]:
    """Generate template keywords when AI is not available."""
    
    keywords = [
        item.brand.lower(),
        item.name.lower(),
        item.category.lower(),
        item.condition.lower()
    ]
    
    if item.size:
        keywords.extend([item.size.lower(), f"size {item.size.lower()}"])
    if item.color:
        keywords.extend([item.color.lower()])
    
    # Add generic keywords based on category
    category_keywords = {
        "clothing": ["fashion", "style", "apparel", "wear"],
        "electronics": ["tech", "gadget", "device"],
        "home": ["decor", "household", "interior"],
        "books": ["literature", "reading", "educational"],
        "toys": ["play", "kids", "children", "fun"]
    }
    
    category_key = item.category.lower()
    if category_key in category_keywords:
        keywords.extend(category_keywords[category_key])
    
    # Remove duplicates and return requested count
    unique_keywords = list(dict.fromkeys(keywords))  # Preserve order while removing dupes
    return unique_keywords[:count]


def analyze_title_optimization(title: str) -> Dict[str, any]:
    """Analyze a title for eBay optimization."""
    
    analysis = {
        "length": len(title),
        "max_length": 80,
        "length_ok": len(title) <= 80,
        "word_count": len(title.split()),
        "has_brand": False,
        "has_size": False,
        "has_color": False,
        "has_condition": False,
        "suggestions": []
    }
    
    title_lower = title.lower()
    
    # Check for common elements
    common_brands = ["nike", "adidas", "apple", "samsung", "levi", "patagonia", "north face"]
    analysis["has_brand"] = any(brand in title_lower for brand in common_brands)
    
    size_indicators = ["size", "small", "medium", "large", "xl", "xs", "s", "m", "l"]
    analysis["has_size"] = any(size in title_lower for size in size_indicators)
    
    color_words = ["black", "white", "red", "blue", "green", "yellow", "pink", "gray", "brown"]
    analysis["has_color"] = any(color in title_lower for color in color_words)
    
    condition_words = ["new", "excellent", "good", "fair", "used", "vintage"]
    analysis["has_condition"] = any(condition in title_lower for condition in condition_words)
    
    # Generate suggestions
    if not analysis["length_ok"]:
        analysis["suggestions"].append(f"Title too long by {len(title) - 80} characters")
    
    if not analysis["has_brand"]:
        analysis["suggestions"].append("Consider including brand name for better searchability")
    
    if len(title) < 50:
        analysis["suggestions"].append("Title could be longer to include more keywords")
    
    return analysis