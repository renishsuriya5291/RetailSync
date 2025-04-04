import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Package, AlertTriangle, DollarSign, TrendingUp, ShoppingCart, Truck, RefreshCw } from 'lucide-react';

// API URL - Change this to match your backend server
const API_URL = 'http://localhost:5000/api';

const App = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for dashboard data
  const [inventoryStatus, setInventoryStatus] = useState({
    total_stores: 0,
    total_products: 0,
    product_store_combinations: 0,
    status_counts: {
      Healthy: 0,
      Low: 0,
      Critical: 0,
      Stockout: 0
    }
  });

  const [pendingOrders, setPendingOrders] = useState([]);
  const [priceRecommendations, setPriceRecommendations] = useState([]);
  const [reorderRecommendations, setReorderRecommendations] = useState([]);
  const [forecastData, setForecastData] = useState([]);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Function to load all dashboard data
  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log("Fetching dashboard data from API...");
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const response = await fetch(`${API_URL}/dashboard`, {
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}`);
      }

      const data = await response.json();
      console.log("Dashboard data received:", data);

      if (data.error) {
        throw new Error(data.error);
      }

      // Update state with received data
      if (data.inventory_overview) {
        setInventoryStatus(data.inventory_overview);
      }

      if (data.pending_orders) {
        setPendingOrders(data.pending_orders);
      }

      if (data.price_recommendations) {
        setPriceRecommendations(data.price_recommendations);
      }

      if (data.reorder_recommendations) {
        setReorderRecommendations(data.reorder_recommendations);
      }

      if (data.sample_forecast) {
        setForecastData(data.sample_forecast);
      }

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      if (err.name === 'AbortError') {
        setError('Request timed out. The server may be taking too long to process the data.');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // Function to fetch specific forecasts
  const loadForecast = async (productId, storeId) => {
    try {
      const response = await fetch(`${API_URL}/forecast?product_id=${productId}&store_id=${storeId}`);
      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setForecastData(data);
    } catch (err) {
      console.error('Error loading forecast:', err);
      setError(err.message);
    }
  };

  // Function to run optimization
  const runOptimization = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/optimization/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Reload dashboard data after optimization
      await loadDashboardData();

      // Show success notification
      alert('Optimization completed successfully');

    } catch (err) {
      console.error('Error running optimization:', err);
      setError(err.message);
      alert(`Optimization failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Function to apply price change
  const applyPriceChange = async (recommendation) => {
    try {
      const response = await fetch(`${API_URL}/actions/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: 'price_change',
          details: recommendation,
          priority: recommendation.adjustment_percentage > 10 ? 'high' : 'medium'
        })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Remove the applied recommendation from the list
      setPriceRecommendations(prev =>
        prev.filter(r => !(r.product_id === recommendation.product_id && r.store_id === recommendation.store_id))
      );

      // Show success notification
      alert('Price change applied successfully');

    } catch (err) {
      console.error('Error applying price change:', err);
      alert(`Failed to apply price change: ${err.message}`);
    }
  };

  // Function to place order
  const placeOrder = async (recommendation) => {
    try {
      const response = await fetch(`${API_URL}/actions/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: 'place_order',
          details: {
            product_id: recommendation.product_id,
            store_id: recommendation.store_id,
            quantity: recommendation.reorder_quantity,
            expected_lead_time: 7, // Default value
            expected_delivery: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
          },
          priority: recommendation.urgency === 'critical' || recommendation.urgency === 'high' ? 'high' : 'medium'
        })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Remove the applied recommendation from the list
      setReorderRecommendations(prev =>
        prev.filter(r => !(r.product_id === recommendation.product_id && r.store_id === recommendation.store_id))
      );

      // Add the new order to pending orders
      setPendingOrders(prev => [
        ...prev,
        {
          id: Date.now(), // Temporary ID
          product_id: recommendation.product_id,
          store_id: recommendation.store_id,
          quantity: recommendation.reorder_quantity,
          expected_delivery: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          status: 'Processing'
        }
      ]);

      // Show success notification
      alert('Order placed successfully');

    } catch (err) {
      console.error('Error placing order:', err);
      alert(`Failed to place order: ${err.message}`);
    }
  };
  // Generate notifications based on data
  const generateNotifications = () => {
    const notifications = [];

    // Check for stockouts
    if (inventoryStatus.status_counts.Stockout > 0) {
      notifications.push({
        id: 1,
        type: 'alert',
        message: `${inventoryStatus.status_counts.Stockout} products currently out of stock`,
        time: 'Just now'
      });
    }

    // Check for critical stock levels
    if (inventoryStatus.status_counts.Critical > 0) {
      notifications.push({
        id: 2,
        type: 'warning',
        message: `${inventoryStatus.status_counts.Critical} products at critical stock levels`,
        time: 'Just now'
      });
    }

    // Add notifications about price recommendations
    if (priceRecommendations.length > 0) {
      const increaseCount = priceRecommendations.filter(r => r.adjustment_percentage > 0).length;
      const decreaseCount = priceRecommendations.filter(r => r.adjustment_percentage < 0).length;

      if (increaseCount > 0) {
        notifications.push({
          id: 3,
          type: 'info',
          message: `${increaseCount} products recommended for price increase`,
          time: 'Just now'
        });
      }

      if (decreaseCount > 0) {
        notifications.push({
          id: 4,
          type: 'info',
          message: `${decreaseCount} products recommended for price decrease`,
          time: 'Just now'
        });
      }
    }

    // Add notifications about pending orders
    if (pendingOrders.length > 0) {
      notifications.push({
        id: 5,
        type: 'info',
        message: `${pendingOrders.length} orders in progress`,
        time: 'Just now'
      });
    }

    // If we have no notifications, add a default one
    if (notifications.length === 0) {
      notifications.push({
        id: 6,
        type: 'success',
        message: 'System running normally',
        time: 'Just now'
      });
    }

    return notifications;
  };

  const notifications = generateNotifications();

  // Transform inventory status into chart data
  const inventoryHealthData = [
    { name: 'Healthy', value: inventoryStatus.status_counts.Healthy },
    { name: 'Low', value: inventoryStatus.status_counts.Low },
    { name: 'Critical', value: inventoryStatus.status_counts.Critical },
    { name: 'Stockout', value: inventoryStatus.status_counts.Stockout },
  ];

  const COLORS = ['#4caf50', '#ff9800', '#f44336', '#9e9e9e'];

  // Loading overlay
  const renderLoading = () => (
    loading && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-lg flex items-center space-x-4">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
          <p className="text-lg">Loading...</p>
        </div>
      </div>
    )
  );

  // Error message
  const renderError = () => (
    error && (
      <div className="max-w-7xl mx-auto mt-4 px-4 sm:px-6 lg:px-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    )
  );

  const renderOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-blue-100 text-blue-600">
            <Package size={24} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">Total Products</p>
            <p className="text-2xl font-semibold">{inventoryStatus.total_products}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-green-100 text-green-600">
            <ShoppingCart size={24} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">Total Stores</p>
            <p className="text-2xl font-semibold">{inventoryStatus.total_stores}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
            <AlertTriangle size={24} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">Stock Alerts</p>
            <p className="text-2xl font-semibold">{inventoryStatus.status_counts.Critical + inventoryStatus.status_counts.Stockout}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center">
          <div className="p-3 rounded-full bg-purple-100 text-purple-600">
            <DollarSign size={24} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">Price Changes</p>
            <p className="text-2xl font-semibold">{priceRecommendations.length}</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderInventoryHealth = () => (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <h2 className="text-lg font-semibold mb-4">Inventory Health</h2>
      <div className="flex flex-col md:flex-row">
        <div className="w-full md:w-1/2 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={inventoryHealthData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                fill="#8884d8"
                paddingAngle={5}
                dataKey="value"
              >
                {inventoryHealthData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="w-full md:w-1/2 flex flex-col justify-center">
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
              <div>
                <p className="text-sm text-gray-600">Healthy</p>
                <p className="font-semibold">{inventoryStatus.status_counts.Healthy}</p>
              </div>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-yellow-500 rounded mr-2"></div>
              <div>
                <p className="text-sm text-gray-600">Low</p>
                <p className="font-semibold">{inventoryStatus.status_counts.Low}</p>
              </div>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
              <div>
                <p className="text-sm text-gray-600">Critical</p>
                <p className="font-semibold">{inventoryStatus.status_counts.Critical}</p>
              </div>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-gray-500 rounded mr-2"></div>
              <div>
                <p className="text-sm text-gray-600">Stockout</p>
                <p className="font-semibold">{inventoryStatus.status_counts.Stockout}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderForecastChart = () => (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <h2 className="text-lg font-semibold mb-4">Demand Forecast (Next 14 Days)</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={forecastData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="forecast" stroke="#8884d8" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderPriceRecommendations = () => (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Price Change Recommendations</h2>
        <button
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm flex items-center disabled:bg-blue-400"
          onClick={loadDashboardData}
          disabled={loading}
        >
          <RefreshCw size={16} className="mr-1" />
          Refresh
        </button>
      </div>

      {priceRecommendations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No price change recommendations at this time
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Store ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recommended</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Change %</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {priceRecommendations.map((item) => (
                <tr key={`${item.product_id}-${item.store_id}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.product_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.store_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.current_price?.toFixed(2) || '0.00'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.recommended_price?.toFixed(2) || '0.00'}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm ${(item.adjustment_percentage || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {(item.adjustment_percentage || 0) >= 0 ? '+' : ''}{(item.adjustment_percentage || 0).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.reason || 'Optimized pricing'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      className="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs mr-2"
                      onClick={() => applyPriceChange(item)}
                      disabled={loading}
                    >
                      Apply
                    </button>
                    <button
                      className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-2 py-1 rounded text-xs"
                      onClick={() => {
                        setPriceRecommendations(prev =>
                          prev.filter(r => !(r.product_id === item.product_id && r.store_id === item.store_id))
                        );
                      }}
                    >
                      Ignore
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderReorderRecommendations = () => (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Reorder Recommendations</h2>
        <button
          className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-md text-sm flex items-center disabled:bg-green-400"
          onClick={() => {
            // Place orders for all recommendations
            reorderRecommendations.forEach(item => placeOrder(item));
          }}
          disabled={loading || reorderRecommendations.length === 0}
        >
          <Truck size={16} className="mr-1" />
          Order All
        </button>
      </div>

      {reorderRecommendations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No reorder recommendations at this time
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Store ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Stock</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expected Demand</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recommended Qty</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Urgency</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reorderRecommendations.map((item) => (
                <tr key={`${item.product_id}-${item.store_id}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.product_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.store_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.current_stock}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.expected_demand}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.reorder_quantity}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 text-xs rounded-full ${item.urgency === 'critical' ? 'bg-red-100 text-red-800' :
                      item.urgency === 'high' ? 'bg-orange-100 text-orange-800' :
                        item.urgency === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                      }`}>
                      {typeof item.urgency === 'string'
                        ? item.urgency.charAt(0).toUpperCase() + item.urgency.slice(1)
                        : 'Medium'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      className="bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded text-xs mr-2"
                      onClick={() => placeOrder(item)}
                      disabled={loading}
                    >
                      Order
                    </button>
                    <button
                      className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-2 py-1 rounded text-xs"
                      onClick={() => {
                        setReorderRecommendations(prev =>
                          prev.filter(r => !(r.product_id === item.product_id && r.store_id === item.store_id))
                        );
                      }}
                    >
                      Ignore
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderNotifications = () => (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">Recent Notifications</h2>
      <div className="space-y-4">
        {notifications.map((notification) => (
          <div key={notification.id} className={`flex items-start p-3 border-l-4 bg-gray-50 rounded-r-md ${notification.type === 'alert' ? 'border-red-500' :
            notification.type === 'warning' ? 'border-yellow-500' :
              notification.type === 'info' ? 'border-blue-500' :
                'border-green-500'
            }`}>
            <div className="flex-1">
              <p className="text-sm">{notification.message}</p>
              <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="bg-gray-100 min-h-screen">
      {renderLoading()}
      {renderError()}

      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Retail Inventory Optimization</h1>
            <div className="flex items-center space-x-4">
              <button
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:bg-blue-400"
                onClick={runOptimization}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Run Optimization'}
              </button>
              <button
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:bg-green-400"
                onClick={loadDashboardData}
                disabled={loading}
              >
                Refresh Data
              </button>
            </div>
          </div>
        </div>
      </header>
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-4 text-sm font-medium ${activeTab === 'overview' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('inventory')}
              className={`px-3 py-4 text-sm font-medium ${activeTab === 'inventory' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Inventory Management
            </button>
            <button
              onClick={() => setActiveTab('pricing')}
              className={`px-3 py-4 text-sm font-medium ${activeTab === 'pricing' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Pricing Optimization
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`px-3 py-4 text-sm font-medium ${activeTab === 'orders' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Order Management
            </button>
            <button
              onClick={() => setActiveTab('forecast')}
              className={`px-3 py-4 text-sm font-medium ${activeTab === 'forecast' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Demand Forecasting
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <div>
            {renderOverview()}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {renderInventoryHealth()}
              {renderNotifications()}
            </div>
          </div>
        )}

        {activeTab === 'inventory' && (
          <div>
            {renderInventoryHealth()}
            {renderReorderRecommendations()}
          </div>
        )}

        {activeTab === 'pricing' && (
          <div>
            {renderPriceRecommendations()}
          </div>
        )}

        {activeTab === 'orders' && (
          <div>
            {renderReorderRecommendations()}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
              <h2 className="text-lg font-semibold mb-4">Pending Orders</h2>
              {pendingOrders.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No pending orders at this time
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order ID</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product ID</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Store ID</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expected Delivery</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {pendingOrders.map((order) => (
                        <tr key={order.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {order.order_id || `ORD-${order.id || Math.floor(Math.random() * 90000) + 10000}`}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.product_id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.store_id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.quantity}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.expected_delivery}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 text-xs rounded-full ${order.status === 'In Transit' ? 'bg-blue-100 text-blue-800' :
                              order.status === 'Processing' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                              {order.status || 'Processing'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'forecast' && (
          <div>
            {renderForecastChart()}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
              <h2 className="text-lg font-semibold mb-4">Product Selection</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Product ID</label>
                  <input
                    type="number"
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter product ID"
                    min="1000"
                    id="product-id"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Store ID</label>
                  <input
                    type="number"
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter store ID"
                    min="10"
                    id="store-id"
                  />
                </div>
              </div>
              <div className="mt-4">
                <button
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium"
                  onClick={() => {
                    const productId = document.getElementById('product-id').value;
                    const storeId = document.getElementById('store-id').value;

                    if (productId && storeId) {
                      loadForecast(productId, storeId);
                    } else
                      if (productId && storeId) {
                        loadForecast(productId, storeId);
                      } else {
                        alert('Please enter both Product ID and Store ID');
                      }
                  }}
                  disabled={loading}
                >
                  Generate Forecast
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;