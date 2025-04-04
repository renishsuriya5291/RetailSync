# In coordination_agent.py
import sys
sys.path.append('..') 

class InventoryMonitoringAgent:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.stock_levels = {}
        self.safety_stocks = {}
        self.reorder_points = {}
        self.stockout_risk = {}
        
    def update_inventory(self, inventory_data):
        # Update current inventory levels
        for row in inventory_data:
            product_id = row['Product ID']
            store_id = row['Store ID']
            key = (product_id, store_id)
            
            self.stock_levels[key] = row['Stock Levels']
            
            # Update reorder points from data or calculate if not provided
            if 'Reorder Point' in row:
                self.reorder_points[key] = row['Reorder Point']
            else:
                self.reorder_points[key] = self._calculate_reorder_point(row)
                
            # Calculate safety stock levels
            self.safety_stocks[key] = self._calculate_safety_stock(row)
            
            # Calculate stockout risk
            self.stockout_risk[key] = self._calculate_stockout_risk(row)
    
    def check_inventory_health(self, product_id, store_id):
        key = (product_id, store_id)
        
        if key not in self.stock_levels:
            return {
                'status': 'Unknown',
                'message': 'No inventory data for this product and store'
            }
        
        current_level = self.stock_levels[key]
        reorder_point = self.reorder_points.get(key, 0)
        safety_stock = self.safety_stocks.get(key, 0)
        
        if current_level <= 0:
            return {
                'status': 'Stockout',
                'message': 'Product is out of stock',
                'action': 'Immediate reorder required'
            }
        elif current_level < safety_stock:
            return {
                'status': 'Critical',
                'message': f'Inventory below safety stock ({safety_stock})',
                'action': 'Urgent reorder required'
            }
        elif current_level < reorder_point:
            return {
                'status': 'Low',
                'message': f'Inventory below reorder point ({reorder_point})',
                'action': 'Reorder recommended'
            }
        else:
            return {
                'status': 'Healthy',
                'message': 'Inventory at adequate levels',
                'action': 'No action required'
            }
    
    def get_reorder_recommendations(self, forecast_data):
        recommendations = []
        
        for key, current_level in self.stock_levels.items():
            product_id, store_id = key
            
            # Get forecast for this product-store combination
            forecast = forecast_data.get(key, [])
            
            if not forecast:
                continue
                
            # Calculate expected demand during lead time
            lead_time = self._get_lead_time(product_id, store_id)
            expected_demand = sum(forecast[:lead_time])
            
            # Check if reorder is needed
            if current_level - expected_demand < self.reorder_points.get(key, 0):
                # Calculate optimal order quantity
                optimal_quantity = self._calculate_order_quantity(key, forecast)
                
                recommendations.append({
                    'product_id': product_id,
                    'store_id': store_id,
                    'current_stock': current_level,
                    'expected_demand': expected_demand,
                    'reorder_quantity': optimal_quantity,
                    'urgency': self._calculate_urgency(current_level, expected_demand, self.safety_stocks.get(key, 0))
                })
                
        # Sort recommendations by urgency
        recommendations.sort(key=lambda x: x['urgency'], reverse=True)
        return recommendations
    
    def _calculate_safety_stock(self, inventory_data):
        # Calculate safety stock based on lead time, demand variability, and service level
        # Simplified placeholder implementation
        lead_time = inventory_data['Supplier Lead Time (days)']
        stockout_frequency = inventory_data['Stockout Frequency']
        
        # Basic safety stock calculation
        # In a real implementation, this would include statistical distribution calculations
        return lead_time * stockout_frequency * 0.5
    
    def _calculate_reorder_point(self, inventory_data):
        # Calculate reorder point based on lead time demand and safety stock
        # Simplified placeholder
        lead_time = inventory_data['Supplier Lead Time (days)']
        avg_demand = 10  # Placeholder; would be calculated from historical data
        safety_stock = self._calculate_safety_stock(inventory_data)
        
        return (lead_time * avg_demand) + safety_stock
    
    def _calculate_stockout_risk(self, inventory_data):
        # Calculate risk of stockout
        current_stock = inventory_data['Stock Levels']
        reorder_point = inventory_data['Reorder Point']
        stockout_frequency = inventory_data['Stockout Frequency']
        
        if current_stock <= 0:
            return 1.0  # Already out of stock
        elif current_stock < reorder_point:
            # Risk increases as stock approaches zero
            return 0.5 + (0.5 * (1 - (current_stock / reorder_point)))
        else:
            # Low risk if above reorder point, but consider historical stockout frequency
            base_risk = 0.1 * (stockout_frequency / 10)  # Normalize to 0-0.1 range
            return base_risk
    
    def _get_lead_time(self, product_id, store_id):
        # Get supplier lead time for this product-store combination
        # Placeholder implementation
        return 7  # Default 7 days
    
    def _calculate_order_quantity(self, key, forecast):
        # Calculate economic order quantity
        # Simplified placeholder
        product_id, store_id = key
        
        # Basic calculation: cover next 30 days of demand
        return sum(forecast[:30])
    
    def _calculate_urgency(self, current_stock, expected_demand, safety_stock):
        # Calculate urgency of reorder
        # Higher values indicate more urgent reorders
        if current_stock <= 0:
            return 10  # Highest urgency for stockouts
        elif current_stock < expected_demand:
            return 8  # Very urgent if won't cover expected demand
        elif current_stock < (expected_demand + safety_stock):
            return 5  # Moderately urgent if won't maintain safety stock
        else:
            return 3  # Normal urgency