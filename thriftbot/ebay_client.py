"""
ThriftBot eBay API Client

Complete eBay API integration for direct listing management and market research.
"""

import os
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

from thriftbot.db import get_item_by_sku, InventoryItem, update_item_pricing

# Load environment variables
load_dotenv()


class eBayAPIClient:
    """Complete eBay API client for Sell API and Finding API integration."""
    
    def __init__(self, sandbox: bool = True):
        """Initialize eBay API client.
        
        Args:
            sandbox: Use sandbox environment for testing (default: True)
        """
        self.sandbox = sandbox
        
        # API Configuration
        if sandbox:
            self.sell_api_base = "https://api.sandbox.ebay.com/sell"
            self.finding_api_base = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
            self.auth_base = "https://auth.sandbox.ebay.com/oauth/api_token"
        else:
            self.sell_api_base = "https://api.ebay.com/sell"
            self.finding_api_base = "https://svcs.ebay.com/services/search/FindingService/v1"
            self.auth_base = "https://auth.ebay.com/oauth/api_token"
        
        # Credentials from environment
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("EBAY_REDIRECT_URI", "https://localhost:3000/callback")
        self.refresh_token = os.getenv("EBAY_REFRESH_TOKEN")
        
        # Runtime state
        self.access_token = None
        self.token_expires_at = None
        
        # Validate configuration
        if not all([self.client_id, self.client_secret]):
            raise ValueError("eBay API credentials not found. Please check your .env file.")
    
    def get_access_token(self) -> str:
        """Get or refresh access token for API calls."""
        
        # Check if current token is still valid
        if (self.access_token and self.token_expires_at and 
            datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)):
            return self.access_token
        
        # Get new token
        if self.refresh_token:
            return self._refresh_access_token()
        else:
            raise ValueError("No refresh token available. Please complete OAuth2 flow first.")
    
    def _refresh_access_token(self) -> str:
        """Refresh access token using refresh token."""
        
        # Prepare request
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": "https://api.ebay.com/oauth/api_scope/sell.marketing "
                    "https://api.ebay.com/oauth/api_scope/sell.inventory "
                    "https://api.ebay.com/oauth/api_scope/sell.account "
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment "
                    "https://api.ebay.com/oauth/api_scope/sell.finances"
        }
        
        response = requests.post(self.auth_base, headers=headers, data=data, auth=auth)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 7200)  # Default 2 hours
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            return self.access_token
        else:
            raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")
    
    def get_oauth_url(self, state: str = None) -> str:
        """Get OAuth2 authorization URL for initial setup."""
        
        auth_url = f"https://auth.{'sandbox.' if self.sandbox else ''}ebay.com/oauth2/authorize"
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "https://api.ebay.com/oauth/api_scope/sell.marketing "
                    "https://api.ebay.com/oauth/api_scope/sell.inventory "
                    "https://api.ebay.com/oauth/api_scope/sell.account "
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment "
                    "https://api.ebay.com/oauth/api_scope/sell.finances"
        }
        
        if state:
            params["state"] = state
        
        # Build URL
        param_string = "&".join([f"{k}={requests.utils.quote(v)}" for k, v in params.items()])
        return f"{auth_url}?{param_string}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, str]:
        """Exchange authorization code for access and refresh tokens."""
        
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(self.auth_base, headers=headers, data=data, auth=auth)
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Store tokens
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            expires_in = token_data.get("expires_in", 7200)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in
            }
        else:
            raise Exception(f"Failed to exchange code: {response.status_code} - {response.text}")
    
    def _make_api_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make authenticated API request to eBay."""
        
        token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        url = f"{self.sell_api_base}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code in [200, 201, 204]:
            return response.json() if response.content else {}
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    # Inventory Management API
    def create_inventory_item(self, sku: str, item_data: Dict) -> Dict:
        """Create or update inventory item."""
        
        endpoint = f"/inventory/v1/inventory_item/{sku}"
        return self._make_api_request("PUT", endpoint, data=item_data)
    
    def get_inventory_item(self, sku: str) -> Dict:
        """Get inventory item details."""
        
        endpoint = f"/inventory/v1/inventory_item/{sku}"
        return self._make_api_request("GET", endpoint)
    
    def delete_inventory_item(self, sku: str) -> Dict:
        """Delete inventory item."""
        
        endpoint = f"/inventory/v1/inventory_item/{sku}"
        return self._make_api_request("DELETE", endpoint)
    
    # Offer Management (Listings)
    def create_offer(self, sku: str, offer_data: Dict) -> Dict:
        """Create listing offer for inventory item."""
        
        endpoint = "/sell/inventory/v1/offer"
        offer_data["sku"] = sku
        return self._make_api_request("POST", endpoint, data=offer_data)
    
    def publish_offer(self, offer_id: str) -> Dict:
        """Publish offer to eBay marketplace."""
        
        endpoint = f"/sell/inventory/v1/offer/{offer_id}/publish"
        return self._make_api_request("POST", endpoint)
    
    def get_offers(self, sku: str = None) -> Dict:
        """Get offers for SKU or all offers."""
        
        endpoint = "/sell/inventory/v1/offer"
        params = {"sku": sku} if sku else {}
        return self._make_api_request("GET", endpoint, params=params)
    
    def update_offer(self, offer_id: str, offer_data: Dict) -> Dict:
        """Update existing offer."""
        
        endpoint = f"/sell/inventory/v1/offer/{offer_id}"
        return self._make_api_request("PUT", endpoint, data=offer_data)
    
    def delete_offer(self, offer_id: str) -> Dict:
        """Delete offer."""
        
        endpoint = f"/sell/inventory/v1/offer/{offer_id}"
        return self._make_api_request("DELETE", endpoint)
    
    # Order Management
    def get_orders(self, filter_params: Dict = None) -> Dict:
        """Get seller orders."""
        
        endpoint = "/sell/fulfillment/v1/order"
        return self._make_api_request("GET", endpoint, params=filter_params)
    
    def get_order(self, order_id: str) -> Dict:
        """Get specific order details."""
        
        endpoint = f"/sell/fulfillment/v1/order/{order_id}"
        return self._make_api_request("GET", endpoint)
    
    def ship_order(self, order_id: str, shipment_data: Dict) -> Dict:
        """Mark order as shipped."""
        
        endpoint = f"/sell/fulfillment/v1/order/{order_id}/shipping_fulfillment"
        return self._make_api_request("POST", endpoint, data=shipment_data)
    
    # Market Research (Finding API)
    def search_completed_items(self, keywords: str, category_id: str = None, limit: int = 100) -> List[Dict]:
        """Search completed/sold listings for market research."""
        
        # Finding API uses different authentication and format
        headers = {
            "X-EBAY-SOA-SECURITY-APPNAME": self.client_id,
            "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems"
        }
        
        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.client_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": keywords,
            "entries-per-page": min(limit, 100),
            "sold-items-only": "true"
        }
        
        if category_id:
            params["categoryId"] = category_id
        
        response = requests.get(self.finding_api_base, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            search_result = data.get("findCompletedItemsResponse", [{}])[0]
            items = search_result.get("searchResult", [{}])[0].get("item", [])
            
            # Parse and return simplified results
            results = []
            for item in items:
                result = {
                    "title": item.get("title", [""])[0],
                    "price": float(item.get("sellingStatus", [{}])[0].get("currentPrice", [{"@currencyId": "USD", "__value__": "0"}])[0].get("__value__", 0)),
                    "end_time": item.get("listingInfo", [{}])[0].get("endTime", [""])[0],
                    "condition": item.get("condition", [{}])[0].get("conditionDisplayName", [""])[0],
                    "listing_type": item.get("listingInfo", [{}])[0].get("listingType", [""])[0],
                    "item_id": item.get("itemId", [""])[0]
                }
                results.append(result)
            
            return results
        else:
            raise Exception(f"Finding API request failed: {response.status_code} - {response.text}")


# High-level integration functions
def create_ebay_listing_from_sku(sku: str, client: eBayAPIClient = None) -> Dict[str, Any]:
    """Create complete eBay listing from ThriftBot inventory item."""
    
    if not client:
        client = eBayAPIClient()
    
    # Get item from database
    item = get_item_by_sku(sku)
    if not item:
        raise ValueError(f"Item with SKU {sku} not found")
    
    # Generate listing data
    listing_data = _build_ebay_listing_data(item)
    
    try:
        # Step 1: Create inventory item
        inventory_result = client.create_inventory_item(sku, listing_data["inventory_item"])
        
        # Step 2: Create offer
        offer_result = client.create_offer(sku, listing_data["offer"])
        offer_id = offer_result.get("offerId")
        
        # Step 3: Publish offer
        if offer_id:
            publish_result = client.publish_offer(offer_id)
            
            # Update database with eBay listing info
            if publish_result.get("listingId"):
                # This would update the database with eBay listing ID
                pass
            
            return {
                "success": True,
                "sku": sku,
                "offer_id": offer_id,
                "listing_id": publish_result.get("listingId"),
                "message": "Listing created successfully"
            }
        else:
            raise Exception("Failed to create offer")
    
    except Exception as e:
        return {
            "success": False,
            "sku": sku,
            "error": str(e),
            "message": "Failed to create listing"
        }


def _build_ebay_listing_data(item: InventoryItem) -> Dict[str, Any]:
    """Build eBay API listing data from inventory item."""
    
    # Generate AI content if not already done
    from thriftbot.ai import generate_listing_content
    
    try:
        content = generate_listing_content(item.sku)
        title = content["title"]
        description = content["description"]
    except:
        # Fallback to basic title/description
        title = f"{item.brand} {item.name}"
        if item.size:
            title += f" Size {item.size}"
        if item.color:
            title += f" {item.color}"
        title += f" {item.condition}"
        
        description = f"<p>{item.brand} {item.name} in {item.condition} condition.</p>"
    
    # Determine price
    price = float(item.suggested_price) if item.suggested_price else float(item.cost) * 2
    
    # Build listing data structure
    inventory_item = {
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "condition": _map_condition_to_ebay(item.condition),
        "product": {
            "title": title[:80],  # eBay 80 char limit
            "description": description,
            "aspects": {
                "Brand": [item.brand],
                "Type": [item.name],
                "Size": [item.size] if item.size else [],
                "Color": [item.color] if item.color else []
            }
        }
    }
    
    offer = {
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "listingDuration": "GTC",  # Good Till Cancelled
        "pricingSummary": {
            "price": {
                "value": str(price),
                "currency": "USD"
            }
        },
        "listingPolicies": {
            "fulfillmentPolicyId": None,  # Would need to be set
            "paymentPolicyId": None,      # Would need to be set
            "returnPolicyId": None        # Would need to be set
        },
        "categoryId": _guess_ebay_category(item.category),
        "merchantLocationKey": "default_location"
    }
    
    return {
        "inventory_item": inventory_item,
        "offer": offer
    }


def _map_condition_to_ebay(condition: str) -> str:
    """Map ThriftBot condition to eBay condition ID."""
    
    condition_map = {
        "New": "NEW",
        "New with Tags": "NEW_WITH_TAGS",
        "New without Tags": "NEW_WITHOUT_TAGS",
        "Excellent": "EXCELLENT_REFURBISHED",
        "Very Good": "VERY_GOOD_REFURBISHED",
        "Good": "GOOD_REFURBISHED",
        "Fair": "ACCEPTABLE",
        "Poor": "FOR_PARTS_OR_NOT_WORKING"
    }
    
    return condition_map.get(condition, "GOOD_REFURBISHED")


def _guess_ebay_category(category: str) -> str:
    """Guess eBay category ID from ThriftBot category."""
    
    # This is a simplified mapping - in production would use eBay's category API
    category_map = {
        "clothing": "11450",     # Clothing, Shoes & Accessories > Men's Clothing
        "electronics": "58058",  # Consumer Electronics
        "home": "11700",         # Home & Garden
        "books": "267",          # Books
        "toys": "220"            # Toys & Hobbies
    }
    
    return category_map.get(category.lower(), "99")  # Other category


def sync_orders_with_inventory() -> Dict[str, Any]:
    """Sync eBay orders with ThriftBot inventory status."""
    
    client = eBayAPIClient()
    
    try:
        # Get recent orders
        orders = client.get_orders({
            "filter": "creationdate:[2024-01-01T00:00:00.000Z..2025-12-31T23:59:59.999Z]",
            "limit": 50
        })
        
        sync_results = {
            "orders_processed": 0,
            "items_updated": 0,
            "errors": []
        }
        
        # Process each order
        for order in orders.get("orders", []):
            try:
                # Update inventory status for sold items
                for line_item in order.get("lineItems", []):
                    sku = line_item.get("sku")
                    if sku:
                        # Update database - mark as sold
                        item = get_item_by_sku(sku)
                        if item:
                            sold_price = float(line_item.get("total", {}).get("value", 0))
                            update_item_pricing(sku, sold_price=sold_price)
                            sync_results["items_updated"] += 1
                
                sync_results["orders_processed"] += 1
                
            except Exception as e:
                sync_results["errors"].append(f"Order {order.get('orderId', 'unknown')}: {str(e)}")
        
        return sync_results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to sync orders"
        }