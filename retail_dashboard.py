import sys
import datetime
sys.path.append('.')  # Add current directory to path

class RetailDashboard:
    def __init__(self, retail_system):
        self.retail_system = retail_system
        
    def get_inventory_overview(self):
        # Get overview of inventory status across stores
        stores = set()
        products = set()
        statuses = {
            'Healthy': 0,
            'Low': 0,
            'Critical': 0,
            'Stockout': 0
        }
        
        # Collect data from inventory agent
        for key, level in self.retail_system.inventory_agent.stock_levels.items():
            product_id, store_id = key
            products.add(product_id)
            stores.add(store_id)
            
            status = self.retail_system.inventory_agent.check_inventory_health(product_id, store_id)
            statuses[status['status']] = statuses.get(status['status'], 0) + 1
        
        return {
            'total_stores': len(stores),
            'total_products': len(products),
            'product_store_combinations': len(self.retail_system.inventory_agent.stock_levels),
            'status_counts': statuses
        }
    
    def get_pending_orders(self):
        # Get pending orders from supplier agent
        return self.retail_system.supplier_agent.get_pending_orders()
    
    def get_price_recommendations(self):
        # Run optimization to get price recommendations
        action_plan = self.retail_system.run_optimization_cycle()
        
        # Extract price change recommendations
        price_recommendations = []
        for action in action_plan.get('immediate_actions', []) + action_plan.get('scheduled_actions', []):
            if action['type'] == 'price_change':
                price_recommendations.append(action['details'])
                
        return price_recommendations
    
    def get_reorder_recommendations(self):
        # This would use data from the inventory agent
        # For now, we'll simulate the data
        forecasts = {}
        for key in self.retail_system.inventory_agent.stock_levels:
            product_id, store_id = key
            forecast = self.retail_system.demand_agent.forecast_demand(product_id, store_id, 30)
            forecasts[key] = forecast
            
        return self.retail_system.inventory_agent.get_reorder_recommendations(forecasts)
    
    def get_demand_forecast(self, product_id, store_id, days=30):
        # Get demand forecast for specific product and store
        forecast = self.retail_system.demand_agent.forecast_demand(
            product_id, 
            store_id, 
            forecast_period=days
        )
        
        # Format for display
        result = []
        start_date = datetime.datetime.now()
        
        for i, value in enumerate(forecast):
            date = start_date + datetime.timedelta(days=i)
            result.append({
                'date': date.strftime('%Y-%m-%d'),
                'forecast': round(value, 2)
            })
            
        return result
    
    def run_optimization(self):
        # Run optimization cycle and return action plan
        return self.retail_system.run_optimization_cycle()
    
    def execute_action_plan(self, action_plan):
        # Execute the given action plan
        return self.retail_system.execute_actions(action_plan)
    
    def to_dict(self):
        """Convert dashboard data to dictionary for API responses"""
        try:
            inventory_overview = self.get_inventory_overview()
            pending_orders = self.get_pending_orders()
            price_recommendations = self.get_price_recommendations()
            reorder_recommendations = self.get_reorder_recommendations()
            
            # Get sample forecast for a product-store combination
            sample_forecast = []
            if self.retail_system.inventory_agent.stock_levels:
                first_key = next(iter(self.retail_system.inventory_agent.stock_levels))
                product_id, store_id = first_key
                sample_forecast = self.get_demand_forecast(product_id, store_id, 14)
            
            return {
                'inventory_overview': inventory_overview,
                'pending_orders': pending_orders,
                'price_recommendations': price_recommendations,
                'reorder_recommendations': reorder_recommendations,
                'sample_forecast': sample_forecast
            }
        except Exception as e:
            return {
                'error': str(e)
            }