# In coordination_agent.py
import sys
sys.path.append('..')  # May be needed to access parent directory

class CoordinationAgent:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.demand_agent = None
        self.inventory_agent = None
        self.pricing_agent = None
        self.supplier_agent = None
        self.decisions = {}
        self.conflicts = {}
        
    def register_agents(self, demand_agent, inventory_agent, pricing_agent, supplier_agent):
        self.demand_agent = demand_agent
        self.inventory_agent = inventory_agent
        self.pricing_agent = pricing_agent
        self.supplier_agent = supplier_agent
    
    def coordinate_actions(self):
        # Step 1: Get forecasts from demand agent
        forecasts = self._get_demand_forecasts()
        
        # Step 2: Get inventory status from inventory agent
        inventory_status = self._get_inventory_status()
        
        # Step 3: Get reorder recommendations
        reorder_recommendations = self.inventory_agent.get_reorder_recommendations(forecasts)
        
        # Step 4: Get pricing recommendations
        pricing_recommendations = self.pricing_agent.get_price_recommendations(inventory_status, forecasts)
        
        # Step 5: Process supplier orders
        orders_to_place = self.supplier_agent.process_reorder_recommendations(reorder_recommendations)
        
        # Step 6: Reconcile conflicts between pricing and inventory decisions
        reconciled_decisions = self._reconcile_decisions(
            reorder_recommendations,
            pricing_recommendations,
            inventory_status,
            forecasts
        )
        
        # Step 7: Generate final action plan
        action_plan = self._generate_action_plan(reconciled_decisions, orders_to_place)
        
        return action_plan
    
    def _get_demand_forecasts(self):
        # Collect demand forecasts for all product-store combinations
        forecasts = {}
        
        # In a real implementation, this would query all relevant products
        # For simplicity, we're using a placeholder approach
        for product_id in range(1000, 2000):
            for store_id in range(10, 20):
                forecast = self.demand_agent.forecast_demand(
                    product_id, 
                    store_id, 
                    forecast_period=30  # 30-day forecast
                )
                forecasts[(product_id, store_id)] = forecast
                
        return forecasts
    
    def _get_inventory_status(self):
        # Collect inventory status for all product-store combinations
        status = {}
        
        # In a real implementation, this would query all relevant products
        # For simplicity, we're using a placeholder approach
        for product_id in range(1000, 2000):
            for store_id in range(10, 20):
                status[(product_id, store_id)] = self.inventory_agent.check_inventory_health(
                    product_id, 
                    store_id
                )
                
        return status
    
    def _reconcile_decisions(self, reorder_recs, pricing_recs, inventory_status, forecasts):
        # Reconcile potentially conflicting decisions
        reconciled = {
            'reorder': [],
            'pricing': []
        }
        
        # Process reorder recommendations
        for rec in reorder_recs:
            product_id = rec['product_id']
            store_id = rec['store_id']
            key = (product_id, store_id)
            
            # Check for conflicts with pricing recommendations
            pricing_rec = next((p for p in pricing_recs if p['product_id'] == product_id and p['store_id'] == store_id), None)
            
            if pricing_rec and pricing_rec['adjustment_percentage'] < -10:
                # If price is being significantly reduced, adjust order quantity
                # to account for expected higher demand
                elasticity = self.pricing_agent.price_elasticity.get(key, 1.0)
                price_change = pricing_rec['adjustment_percentage'] / 100
                demand_change = -price_change * elasticity  # Negative price change = positive demand change
                
                # Adjust reorder quantity
                rec['reorder_quantity'] = int(rec['reorder_quantity'] * (1 + demand_change))
                
            # Add to reconciled decisions
            reconciled['reorder'].append(rec)
        
        # Process pricing recommendations
        for rec in pricing_recs:
            product_id = rec['product_id']
            store_id = rec['store_id']
            key = (product_id, store_id)
            
            # Check inventory status
            status = inventory_status.get(key, {}).get('status', 'Healthy')
            
            if status == 'Stockout' and rec['adjustment_percentage'] < 0:
                # Don't lower prices for out-of-stock items
                continue
            elif status in ['Critical', 'Low'] and rec['adjustment_percentage'] < 0:
                # For low stock, moderate price decreases
                rec['recommended_price'] = rec['current_price'] * 0.95
                rec['adjustment_percentage'] = -5.0
                rec['reason'] += " (limited to 5% reduction due to low stock)"
            
            # Add to reconciled decisions
            reconciled['pricing'].append(rec)
            
        return reconciled
    
    def _generate_action_plan(self, reconciled_decisions, orders_to_place):
        # Generate final action plan with priorities
        action_plan = {
            'immediate_actions': [],
            'scheduled_actions': [],
            'monitoring_actions': []
        }
        
        # Process orders that need to be placed immediately
        for order in orders_to_place:
            action_plan['immediate_actions'].append({
                'type': 'place_order',
                'details': order,
                'priority': 'high'
            })
        
        # Process price changes
        for price_change in reconciled_decisions['pricing']:
            # Determine priority
            priority = 'medium'
            if abs(price_change['adjustment_percentage']) > 15:
                priority = 'high'
            
            # Determine timing
            timing = 'scheduled' if priority == 'medium' else 'immediate'
            
            action_plan[f'{timing}_actions'].append({
                'type': 'price_change',
                'details': price_change,
                'priority': priority
            })
        
        # Add monitoring actions for potentially problematic items
        # In a real system, these would be generated based on risk assessment
        
        return action_plan