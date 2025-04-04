from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import os
import sys

# Add the current directory to the Python path
sys.path.append('.')

# Import the system initialization module
from system_initialization_data_pipeline import initialize_retail_system

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables to store processed data
dashboard_data = None
inventory_overview = None
pending_orders = []
price_recommendations = []
reorder_recommendations = []
forecast_data = []

# Initialize the retail system and dashboard
print("Pre-processing data before starting server...")
system, dashboard = initialize_retail_system()

# Process data initially
def process_initial_data():
    global dashboard_data, inventory_overview, pending_orders, price_recommendations, reorder_recommendations, forecast_data
    
    try:
        print("Processing initial data...")
        # Run initial optimization
        action_plan = dashboard.run_optimization()
        dashboard.execute_action_plan(action_plan)
        
        # Store results in memory
        inventory_overview = dashboard.get_inventory_overview()
        pending_orders = dashboard.get_pending_orders()
        price_recommendations = dashboard.get_price_recommendations()
        reorder_recommendations = dashboard.get_reorder_recommendations()
        
        # Get sample forecast
        if system.inventory_agent.stock_levels:
            first_key = next(iter(system.inventory_agent.stock_levels))
            product_id, store_id = first_key
            forecast_data = dashboard.get_demand_forecast(product_id, store_id, 14)
        
        # Combine all data for the dashboard
        dashboard_data = {
            'inventory_overview': inventory_overview,
            'pending_orders': pending_orders,
            'price_recommendations': price_recommendations,
            'reorder_recommendations': reorder_recommendations,
            'sample_forecast': forecast_data
        }
        
        print("Initial data processing complete!")
    except Exception as e:
        print(f"Error in initial data processing: {e}")

# Process data before starting the server
process_initial_data()

# Background optimization thread
def background_optimization():
    global dashboard_data, inventory_overview, pending_orders, price_recommendations, reorder_recommendations
    
    while True:
        print("Running background optimization...")
        try:
            # Run optimization
            action_plan = dashboard.run_optimization()
            results = dashboard.execute_action_plan(action_plan)
            print(f"Optimization complete, {len(action_plan.get('immediate_actions', []))} immediate actions")
            
            # Update global data
            inventory_overview = dashboard.get_inventory_overview()
            pending_orders = dashboard.get_pending_orders()
            price_recommendations = dashboard.get_price_recommendations()
            reorder_recommendations = dashboard.get_reorder_recommendations()
            
            # Update the combined dashboard data
            dashboard_data = {
                'inventory_overview': inventory_overview,
                'pending_orders': pending_orders,
                'price_recommendations': price_recommendations,
                'reorder_recommendations': reorder_recommendations,
                'sample_forecast': forecast_data
            }
        except Exception as e:
            print(f"Error in background optimization: {e}")
        
        # Sleep for 5 minutes before next optimization
        time.sleep(300)

# Start the background thread
optimization_thread = threading.Thread(target=background_optimization, daemon=True)
optimization_thread.start()

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Return all dashboard data for the frontend"""
    global dashboard_data
    try:
        if dashboard_data:
            return jsonify(dashboard_data)
        else:
            return jsonify({
                'inventory_overview': inventory_overview or {},
                'pending_orders': pending_orders or [],
                'price_recommendations': price_recommendations or [],
                'reorder_recommendations': reorder_recommendations or [],
                'sample_forecast': forecast_data or []
            })
    except Exception as e:
        print(f"Error serving dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inventory/overview', methods=['GET'])
def get_inventory_overview():
    """Return inventory overview data"""
    global inventory_overview
    try:
        return jsonify(inventory_overview or {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/price/recommendations', methods=['GET'])
def get_price_recommendations():
    """Return price change recommendations"""
    global price_recommendations
    try:
        return jsonify(price_recommendations or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reorder/recommendations', methods=['GET'])
def get_reorder_recommendations():
    """Return reorder recommendations"""
    global reorder_recommendations
    try:
        return jsonify(reorder_recommendations or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/pending', methods=['GET'])
def get_pending_orders():
    """Return pending orders"""
    global pending_orders
    try:
        return jsonify(pending_orders or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """Return demand forecast for a product-store combination"""
    try:
        product_id = int(request.args.get('product_id', 1001))
        store_id = int(request.args.get('store_id', 15))
        days = int(request.args.get('days', 14))
        
        forecast = dashboard.get_demand_forecast(product_id, store_id, days)
        return jsonify(forecast)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/actions/execute', methods=['POST'])
def execute_action():
    """Execute a specific action"""
    global dashboard_data, inventory_overview, pending_orders, price_recommendations, reorder_recommendations
    
    try:
        action_data = request.json
        if not action_data:
            return jsonify({'error': 'No action data provided'}), 400
            
        # Add the action to an action plan
        action_plan = {
            'immediate_actions': [action_data],
            'scheduled_actions': []
        }
        
        # Execute the action
        results = dashboard.execute_action_plan(action_plan)
        
        # Update global data after action execution
        inventory_overview = dashboard.get_inventory_overview()
        pending_orders = dashboard.get_pending_orders()
        price_recommendations = dashboard.get_price_recommendations()
        reorder_recommendations = dashboard.get_reorder_recommendations()
        
        # Update the combined dashboard data
        dashboard_data = {
            'inventory_overview': inventory_overview,
            'pending_orders': pending_orders,
            'price_recommendations': price_recommendations,
            'reorder_recommendations': reorder_recommendations,
            'sample_forecast': forecast_data
        }
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimization/run', methods=['POST'])
def run_optimization():
    """Run a full optimization cycle"""
    global dashboard_data, inventory_overview, pending_orders, price_recommendations, reorder_recommendations
    
    try:
        action_plan = dashboard.run_optimization()
        results = dashboard.execute_action_plan(action_plan)
        
        # Update global data after optimization
        inventory_overview = dashboard.get_inventory_overview()
        pending_orders = dashboard.get_pending_orders()
        price_recommendations = dashboard.get_price_recommendations()
        reorder_recommendations = dashboard.get_reorder_recommendations()
        
        # Update the combined dashboard data
        dashboard_data = {
            'inventory_overview': inventory_overview,
            'pending_orders': pending_orders,
            'price_recommendations': price_recommendations,
            'reorder_recommendations': reorder_recommendations,
            'sample_forecast': forecast_data
        }
        
        return jsonify({
            'action_plan': action_plan,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'API server is running'
    })

if __name__ == '__main__':
    # Get port from environment variable or use default 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting API server on port {port}...")
    
    # Run the server (in production, you would use a WSGI server like Gunicorn)
    app.run(host='0.0.0.0', port=port, debug=True)