import pandas as pd
import os
import sys

# Add parent directory to path to import the agent modules
sys.path.append('.')  # More reliable than complex parent directory logic

# Import RetailInventorySystem
from retail_inventory_system import RetailInventorySystem
from retail_dashboard import RetailDashboard

def initialize_retail_system():
    # Initialize the retail inventory optimization system
    system = RetailInventorySystem()
    
    # Load data
    demand_data = load_demand_data()
    inventory_data = load_inventory_data()
    pricing_data = load_pricing_data()
    
    system.load_data(demand_data, inventory_data, pricing_data)
    
    # Initialize dashboard
    dashboard = RetailDashboard(system)
    
    return system, dashboard
def load_demand_data():
    """Load demand forecasting data from CSV"""
    import os
    
    # Get the directory where the current script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to dataset file
    dataset_path = os.path.join(current_dir, 'dataset', 'demand_forecasting.csv')
    
    print(f"Loading demand data from: {dataset_path}")
    
    try:
        import pandas as pd
        df = pd.read_csv(dataset_path)
        
        # Take a sample if the dataset is too large
        if len(df) > 1000:
            print(f"Dataset is large ({len(df)} rows). Sampling 1000 rows for better performance.")
            return df.sample(1000).to_dict('records')
        else:
            return df.to_dict('records')
    except Exception as e:
        print(f"Error loading demand data: {e}")
        # Return minimal sample data
        return [
            {"Product ID": 1001, "Store ID": 15, "Sales Quantity": 45, "Promotions": "Yes", "Seasonality Factors": "Holiday"},
            {"Product ID": 1001, "Store ID": 15, "Sales Quantity": 42, "Promotions": "No", "Seasonality Factors": "None"}
        ]

def load_inventory_data():
    """Load inventory monitoring data from CSV"""
    import os
    
    # Get the directory where the current script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to dataset file
    dataset_path = os.path.join(current_dir, 'dataset', 'inventory_monitoring.csv')
    
    print(f"Loading inventory data from: {dataset_path}")
    
    try:
        import pandas as pd
        df = pd.read_csv(dataset_path)
        
        # Take a sample if the dataset is too large
        if len(df) > 1000:
            print(f"Dataset is large ({len(df)} rows). Sampling 1000 rows for better performance.")
            return df.sample(1000).to_dict('records')
        else:
            return df.to_dict('records')
    except Exception as e:
        print(f"Error loading inventory data: {e}")
        # Return minimal sample data
        return [
            {"Product ID": 1001, "Store ID": 15, "Stock Levels": 78, "Reorder Point": 50, "Supplier Lead Time (days)": 5, "Stockout Frequency": 2},
            {"Product ID": 1002, "Store ID": 15, "Stock Levels": 32, "Reorder Point": 30, "Supplier Lead Time (days)": 7, "Stockout Frequency": 1}
        ]

def load_pricing_data():
    """Load pricing optimization data from CSV"""
    import os
    
    # Get the directory where the current script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to dataset file
    dataset_path = os.path.join(current_dir, 'dataset', 'pricing_optimization.csv')
    
    print(f"Loading pricing data from: {dataset_path}")
    
    try:
        import pandas as pd
        df = pd.read_csv(dataset_path)
        
        # Take a sample if the dataset is too large
        if len(df) > 1000:
            print(f"Dataset is large ({len(df)} rows). Sampling 1000 rows for better performance.")
            return df.sample(1000).to_dict('records')
        else:
            return df.to_dict('records')
    except Exception as e:
        print(f"Error loading pricing data: {e}")
        # Return minimal sample data
        return [
            {"Product ID": 1001, "Store ID": 15, "Price": 49.99, "Competitor Prices": 47.99, "Elasticity Index": 0.8, "Return Rate (%)": 2.5, "Storage Cost": 0.5},
            {"Product ID": 1002, "Store ID": 15, "Price": 29.99, "Competitor Prices": 32.99, "Elasticity Index": 1.2, "Return Rate (%)": 1.8, "Storage Cost": 0.3}
        ]
        
def main():
    # Initialize the system
    print("Initializing retail inventory optimization system...")
    system, dashboard = initialize_retail_system()
    
    # Run initial optimization
    print("Running optimization cycle...")
    action_plan = dashboard.run_optimization()
    
    # Execute immediate actions
    print("Executing recommended actions...")
    results = dashboard.execute_action_plan(action_plan)
    
    # Print results
    print("\nOptimization Results:")
    print(f"Executed Actions: {len(results['executed_actions'])}")
    print(f"Pending Actions: {len(results['pending_actions'])}")
    print(f"Failed Actions: {len(results['failed_actions'])}")
    
    print("\nSample Actions:")
    if results['executed_actions']:
        print("\nExecuted Actions:")
        for i, action in enumerate(results['executed_actions'][:3]):  # Show first 3 actions
            print(f"  {i+1}. Type: {action['action']['type']}, Priority: {action['action'].get('priority', 'medium')}")
    
    if results['pending_actions']:
        print("\nPending Actions:")
        for i, action in enumerate(results['pending_actions'][:3]):  # Show first 3 actions
            print(f"  {i+1}. Type: {action['type']}, Priority: {action.get('priority', 'medium')}")
    
    print("\nSystem initialization complete!")
    
    # Return the system and dashboard for external use
    return system, dashboard

if __name__ == "__main__":
    main()