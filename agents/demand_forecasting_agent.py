# In coordination_agent.py
import sys
sys.path.append('..') 
import numpy as np
import warnings
 
class DemandForecastingAgent:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.forecasting_models = {}
        self.seasonal_patterns = {}
        self.promotion_effects = {}
        self.historical_data = {}
        
    def train_models(self, historical_data):
        # Store historical data for fallback methods
        self.historical_data = historical_data
        
        # Group data by product and store
        grouped_data = self._group_data(historical_data)
        
        for (product_id, store_id), data in grouped_data.items():
            try:
                # Train time series model for each product-store combination
                self.forecasting_models[(product_id, store_id)] = self._train_time_series_model(data)
                
                # Identify seasonal patterns
                self.seasonal_patterns[(product_id, store_id)] = self._identify_seasonality(data)
                
                # Calculate promotion effects
                self.promotion_effects[(product_id, store_id)] = self._calculate_promotion_effect(data)
            except Exception as e:
                print(f"Warning: Error training model for product {product_id}, store {store_id}: {str(e)}")
                # Create a simple fallback model
                self.forecasting_models[(product_id, store_id)] = 'average'
    
    def forecast_demand(self, product_id, store_id, forecast_period, planned_promotions=None, external_factors=None):
        # Get the appropriate forecasting model
        model_data = self.forecasting_models.get((product_id, store_id))
        
        if model_data is None:
            # Fall back to a similar product or general model if specific model not available
            model_data = self._find_similar_model(product_id, store_id)
            
        # Generate base forecast
        if model_data == 'average':
            # Use average-based forecast
            base_forecast = self._get_average_forecast(product_id, store_id, forecast_period)
        else:
            try:
                # Try to use the trained time series model
                base_forecast = model_data.forecast(forecast_period)
                
                # Check for NaN values
                if np.isnan(base_forecast).any():
                    base_forecast = self._get_average_forecast(product_id, store_id, forecast_period)
            except Exception as e:
                print(f"Warning: Forecast failed for product {product_id}, store {store_id}: {str(e)}")
                base_forecast = self._get_average_forecast(product_id, store_id, forecast_period)
        
        # Adjust for seasonality
        seasonal_pattern = self.seasonal_patterns.get((product_id, store_id), {})
        adjusted_forecast = self._apply_seasonality(base_forecast, seasonal_pattern, forecast_period)
        
        # Adjust for planned promotions
        if planned_promotions:
            promotion_effect = self.promotion_effects.get((product_id, store_id), 1.0)
            adjusted_forecast = self._apply_promotions(adjusted_forecast, planned_promotions, promotion_effect)
        
        # Adjust for external factors
        if external_factors:
            adjusted_forecast = self._apply_external_factors(adjusted_forecast, external_factors)
            
        return adjusted_forecast
    
    def _group_data(self, data):
        # Group data by product_id and store_id
        grouped = {}
        for row in data:
            # Support different field names in the data
            product_id = row.get('Product ID', row.get('product_id', None))
            store_id = row.get('Store ID', row.get('store_id', None))
            
            if product_id is None or store_id is None:
                continue  # Skip rows without proper IDs
                
            key = (product_id, store_id)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(row)
        return grouped
    
    def _train_time_series_model(self, data):
        # Skip if too little data
        if len(data) < 10:
            return 'average'
            
        from statsmodels.tsa.arima.model import ARIMA
        
        # Extract time series data - support different field names
        sales = []
        for row in data:
            sales_value = None
            # Try different field names
            for field in ['Sales Quantity', 'sales', 'quantity', 'demand']:
                if field in row:
                    sales_value = row[field]
                    break
                    
            if sales_value is None:
                # If no recognized field, try the first numeric field
                for k, v in row.items():
                    if isinstance(v, (int, float)) and k not in ['Product ID', 'product_id', 'Store ID', 'store_id']:
                        sales_value = v
                        break
                        
            if sales_value is not None:
                sales.append(sales_value)
        
        if len(sales) < 10:
            return 'average'
            
        # Use a simpler ARIMA model to avoid convergence issues
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = ARIMA(sales, order=(1,0,0))  # Simple AR(1) model
                model_fit = model.fit()
                return model_fit
            except Exception as e:
                print(f"ARIMA model failed: {str(e)}")
                return 'average'
    
    def _identify_seasonality(self, data):
        # Extract seasonality patterns using time series decomposition
        # This is a simplified placeholder
        seasonality = {}
        
        # Check if 'Seasonality Factors' exists
        if not data or 'Seasonality Factors' not in data[0]:
            return seasonality
            
        # Extract unique seasonality factors
        for row in data:
            season_factor = row['Seasonality Factors']
            if season_factor not in seasonality and season_factor != 'None':
                # Calculate average effect of this seasonal factor
                season_sales = [r['Sales Quantity'] for r in data if r['Seasonality Factors'] == season_factor]
                non_season_sales = [r['Sales Quantity'] for r in data if r['Seasonality Factors'] == 'None']
                
                if non_season_sales:
                    avg_season = sum(season_sales) / len(season_sales)
                    avg_non_season = sum(non_season_sales) / len(non_season_sales)
                    seasonality[season_factor] = avg_season / avg_non_season if avg_non_season > 0 else 1.0
                else:
                    seasonality[season_factor] = 1.0
                    
        return seasonality
    
    def _calculate_promotion_effect(self, data):
        # Calculate the effect of promotions on sales
        # Check if 'Promotions' exists
        if not data or 'Promotions' not in data[0]:
            return 1.0
            
        promo_sales = [row['Sales Quantity'] for row in data if row['Promotions'] == 'Yes']
        non_promo_sales = [row['Sales Quantity'] for row in data if row['Promotions'] == 'No']
        
        if non_promo_sales and promo_sales:
            avg_promo = sum(promo_sales) / len(promo_sales)
            avg_non_promo = sum(non_promo_sales) / len(non_promo_sales)
            return avg_promo / avg_non_promo if avg_non_promo > 0 else 1.0
        else:
            return 1.0  # Default multiplier if no data available
    
    def _apply_seasonality(self, forecast, seasonality, period):
        # Apply seasonality factors to the forecast
        if isinstance(forecast, np.ndarray):
            adjusted_forecast = forecast.copy()
        else:
            adjusted_forecast = list(forecast)
        
        # If no seasonality data, return original forecast
        if not seasonality:
            return adjusted_forecast
            
        # Map time periods to expected seasonality factors
        for i in range(len(adjusted_forecast)):
            # Since period might not be an iterable, use the index
            applicable_factor = self._determine_seasonality_factor(i)
            
            if applicable_factor in seasonality:
                adjusted_forecast[i] *= seasonality[applicable_factor]
                
        return adjusted_forecast
    
    def _apply_promotions(self, forecast, planned_promotions, promotion_effect):
        # Apply promotion effects to the forecast
        if isinstance(forecast, np.ndarray):
            adjusted_forecast = forecast.copy()
        else:
            adjusted_forecast = list(forecast)
        
        # Handle case where forecast is not iterable
        if not planned_promotions:
            return adjusted_forecast
            
        for promo in planned_promotions:
            if 'start_time' not in promo or 'end_time' not in promo:
                continue
                
            promo_start = promo['start_time']
            promo_end = promo['end_time']
            
            # Find forecast periods that fall within promotion times
            for i in range(len(adjusted_forecast)):
                # Since the time comparison might not work directly, 
                # we'll use the index as a proxy for time
                if promo_start <= i <= promo_end:
                    adjusted_forecast[i] *= promotion_effect
                    
        return adjusted_forecast
    
    def _apply_external_factors(self, forecast, external_factors):
        # Apply effects of external factors like weather, economic indicators
        if isinstance(forecast, np.ndarray):
            adjusted_forecast = forecast.copy()
        else:
            adjusted_forecast = list(forecast)
        
        # Implementation would depend on specific external factors
        # This is a placeholder
        
        return adjusted_forecast
    
    def _find_similar_model(self, product_id, store_id):
        # Find a similar product-store model if the exact one doesn't exist
        # Placeholder implementation
        for model_key, model in self.forecasting_models.items():
            if model != 'average':
                return model
                
        return 'average'
        
    def _determine_seasonality_factor(self, time_period):
        # Determine the seasonality factor based on the time period
        # Placeholder implementation
        return "default"
        
    def _get_average_forecast(self, product_id, store_id, forecast_period):
        # Generate a forecast based on historical averages
        grouped_data = self._group_data(self.historical_data)
        data = grouped_data.get((product_id, store_id), [])
        
        if not data:
            # No historical data, return zeros
            return [0] * forecast_period
            
        # Get sales values
        sales = []
        for row in data:
            sales_value = None
            # Try different field names
            for field in ['Sales Quantity', 'sales', 'quantity', 'demand']:
                if field in row:
                    sales_value = row[field]
                    break
                    
            if sales_value is None:
                # If no recognized field, try the first numeric field
                for k, v in row.items():
                    if isinstance(v, (int, float)) and k not in ['Product ID', 'product_id', 'Store ID', 'store_id']:
                        sales_value = v
                        break
                        
            if sales_value is not None:
                sales.append(sales_value)
                
        if not sales:
            return [0] * forecast_period
            
        # Calculate average
        avg_sales = sum(sales) / len(sales)
        
        # Add some randomness to make it more realistic
        import random
        forecast = []
        for _ in range(forecast_period):
            # Add +/- 10% random variation
            forecast.append(max(0, avg_sales * (1 + (random.random() - 0.5) * 0.2)))
            
        return forecast