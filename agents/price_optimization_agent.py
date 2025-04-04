# In coordination_agent.py
import sys
sys.path.append('..') 
class PricingOptimizationAgent:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.price_elasticity = {}
        self.optimal_prices = {}
        self.competitor_prices = {}
        
    def update_pricing_data(self, pricing_data):
        # Update pricing information
        for row in pricing_data:
            product_id = row['Product ID']
            store_id = row['Store ID']
            key = (product_id, store_id)
            
            # Store competitor prices
            self.competitor_prices[key] = row['Competitor Prices']
            
            # Store elasticity data
            self.price_elasticity[key] = row['Elasticity Index']
            
            # Calculate optimal base price
            self.optimal_prices[key] = self._calculate_optimal_price(row)
    
    def get_price_recommendations(self, inventory_status, forecast_data):
        recommendations = []
        
        for key in self.optimal_prices:
            product_id, store_id = key
            
            # Get current inventory status
            inv_status = inventory_status.get(key, {})
            if not inv_status:
                continue
                
            # Get forecast for this product
            forecast = forecast_data.get(key, [])
            
            # Calculate price adjustment based on inventory and forecast
            base_price = self.optimal_prices[key]
            adjusted_price = self._adjust_price_for_inventory(base_price, inv_status, forecast)
            
            # Check competitor prices
            comp_price = self.competitor_prices.get(key)
            if comp_price:
                adjusted_price = self._adjust_for_competition(adjusted_price, comp_price)
            
            # Only recommend changes if there's a significant difference
            if abs(adjusted_price - base_price) / base_price > 0.05:  # 5% threshold
                recommendations.append({
                    'product_id': product_id,
                    'store_id': store_id,
                    'current_price': base_price,
                    'recommended_price': adjusted_price,
                    'adjustment_percentage': ((adjusted_price - base_price) / base_price) * 100,
                    'reason': self._get_adjustment_reason(inv_status, forecast, comp_price, base_price, adjusted_price)
                })
        
        return recommendations
    
    def _calculate_optimal_price(self, pricing_data):
        # Calculate optimal price based on elasticity
        # This is a simplified placeholder
        current_price = pricing_data['Price']
        elasticity = pricing_data['Elasticity Index']
        competitor_price = pricing_data['Competitor Prices']
        return_rate = pricing_data['Return Rate (%)']
        storage_cost = pricing_data['Storage Cost']
        
        # Simple optimal pricing formula
        # In reality, this would be much more complex
        if elasticity > 1.5:
            # High elasticity - price sensitive customers
            return min(current_price * 0.9, competitor_price * 0.95)
        elif elasticity < 0.5:
            # Low elasticity - less price sensitive
            return max(current_price * 1.1, competitor_price * 1.05)
        else:
            # Moderate elasticity
            return (current_price + competitor_price) / 2
    
    def _adjust_price_for_inventory(self, base_price, inventory_status, forecast):
        # Adjust price based on inventory levels
        status = inventory_status.get('status', 'Healthy')
        
        if status == 'Overstocked':
            # Lower price to move excess inventory
            reduction = min(0.2, 0.05 * inventory_status.get('excess_percentage', 0) / 100)
            return base_price * (1 - reduction)
        elif status == 'Low' or status == 'Critical':
            # Increase price to slow down depletion
            increase = min(0.15, 0.03 * inventory_status.get('shortage_percentage', 0) / 100)
            return base_price * (1 + increase)
        elif status == 'Stockout':
            # Set a placeholder price or mark for special handling
            return base_price * 1.2  # Higher price when back in stock
        else:
            # Healthy inventory, use base optimal price
            return base_price
    
    def _adjust_for_competition(self, price, competitor_price):
        # Adjust price to remain competitive
        # Simple strategy: ensure price is not more than 10% higher than competitors
        max_acceptable = competitor_price * 1.1
        
        if price > max_acceptable:
            return max_acceptable
        return price
    
    def _get_adjustment_reason(self, inv_status, forecast, comp_price, base_price, adjusted_price):
        # Generate explanation for price adjustment
        if adjusted_price < base_price:
            if inv_status.get('status') in ['Overstocked', 'Healthy'] and comp_price < base_price:
                return "Price reduced to remain competitive and reduce excess inventory"
            elif inv_status.get('status') == 'Overstocked':
                return "Price reduced to help clear excess inventory"
            else:
                return "Price reduced to match market conditions"
        else:
            if inv_status.get('status') in ['Low', 'Critical']:
                return "Price increased due to limited stock availability"
            elif comp_price > base_price:
                return "Price increased to align with market value"
            else:
                return "Price adjusted to optimize profit margin"