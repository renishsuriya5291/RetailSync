# In coordination_agent.py
import sys
sys.path.append('..') 

class SupplierIntegrationAgent:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.supplier_lead_times = {}
        self.supplier_performance = {}
        self.pending_orders = {}
        
    def update_supplier_data(self, inventory_data):
        # Update supplier-related information
        for row in inventory_data:
            product_id = row['Product ID']
            store_id = row['Store ID']
            key = (product_id, store_id)
            
            # Store lead time information
            self.supplier_lead_times[key] = row['Supplier Lead Time (days)']
            
            # Update supplier performance metrics
            # In a real system, we would track historical performance
            
    def process_reorder_recommendations(self, recommendations):
        orders_to_place = []
        
        for rec in recommendations:
            product_id = rec['product_id']
            store_id = rec['store_id']
            key = (product_id, store_id)
            
            # Get supplier information
            lead_time = self.supplier_lead_times.get(key, 7)  # Default to 7 days
            
            # Determine optimal order timing
            order_timing = self._determine_order_timing(rec, lead_time)
            
            # Determine optimal order quantity
            order_quantity = rec['reorder_quantity']
            
            # Add to orders list if immediate
            if order_timing == 'immediate':
                orders_to_place.append({
                    'product_id': product_id,
                    'store_id': store_id,
                    'quantity': order_quantity,
                    'expected_lead_time': lead_time,
                    'expected_delivery': self._calculate_delivery_date(lead_time)
                })
            
            # Store pending orders for future processing
            self.pending_orders[key] = {
                'timing': order_timing,
                'quantity': order_quantity,
                'recommended_date': self._calculate_order_date(order_timing)
            }
            
        return orders_to_place
    
    def get_pending_orders(self):
        # Return all pending orders
        pending = []
        
        for key, order in self.pending_orders.items():
            product_id, store_id = key
            
            if order['timing'] != 'immediate':
                pending.append({
                    'product_id': product_id,
                    'store_id': store_id,
                    'quantity': order['quantity'],
                    'recommended_date': order['recommended_date'],
                    'lead_time': self.supplier_lead_times.get(key, 7)
                })
                
        return pending
    
    def track_order_fulfillment(self, order_updates):
        # Update order tracking information
        for update in order_updates:
            product_id = update['product_id']
            store_id = update['store_id']
            key = (product_id, store_id)
            
            # Update supplier performance based on actual vs. expected delivery
            expected_lead_time = self.supplier_lead_times.get(key, 7)
            actual_lead_time = update.get('actual_lead_time')
            
            if actual_lead_time:
                # Update performance metrics
                if key not in self.supplier_performance:
                    self.supplier_performance[key] = {
                        'lead_times': [],
                        'average_lead_time': expected_lead_time,
                        'fulfillment_rate': 100.0
                    }
                
                self.supplier_performance[key]['lead_times'].append(actual_lead_time)
                
                # Recalculate average lead time
                lead_times = self.supplier_performance[key]['lead_times']
                self.supplier_performance[key]['average_lead_time'] = sum(lead_times) / len(lead_times)
                
                # Update lead time prediction
                self.supplier_lead_times[key] = self.supplier_performance[key]['average_lead_time']
    
    def _determine_order_timing(self, recommendation, lead_time):
        # Determine when to place the order
        urgency = recommendation.get('urgency', 5)
        
        if urgency >= 8:
            return 'immediate'
        elif urgency >= 5:
            return 'soon'  # Within 1-2 days
        else:
            return 'scheduled'  # According to regular schedule
    
    def _calculate_delivery_date(self, lead_time):
        # Calculate expected delivery date based on lead time
        import datetime
        return datetime.datetime.now() + datetime.timedelta(days=lead_time)
    
    def _calculate_order_date(self, timing):
        # Calculate when to place the order
        import datetime
        
        if timing == 'immediate':
            return datetime.datetime.now()
        elif timing == 'soon':
            return datetime.datetime.now() + datetime.timedelta(days=1)
        else:
            # Assume scheduled orders are placed weekly
            today = datetime.datetime.now()
            days_to_monday = (0 - today.weekday()) % 7
            next_monday = today + datetime.timedelta(days=days_to_monday)
            return next_monday