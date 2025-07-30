import React, { useState } from 'react';
import { useAlerts } from '../contexts/AlertContext';

const EnhancedAlertCard = ({ alert }) => {
  const { executeAlertAction, acknowledgeAlert } = useAlerts();
  const [isExecuting, setIsExecuting] = useState(false);
  const [executingAction, setExecutingAction] = useState(null);
  const [showActions, setShowActions] = useState(false);

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'high':
        return 'bg-orange-100 border-orange-500 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'low':
        return 'bg-blue-100 border-blue-500 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'critical':
        return '🚨';
      case 'high':
        return '⚠️';
      case 'medium':
        return '⚡';
      case 'low':
        return 'ℹ️';
      default:
        return '📋';
    }
  };

  const handleExecuteAction = async (actionId, actionName) => {
    try {
      setIsExecuting(true);
      setExecutingAction(actionId);
      
      console.log(`🎯 Executing action: ${actionName} for alert: ${alert.title}`);
      
      const result = await executeAlertAction(alert.id, actionId, {}, 'dashboard_user');
      
      if (result.success) {
        console.log(`✅ Action executed successfully:`, result);
        // Show success message (you could add a toast notification here)
        alert(`✅ Action "${actionName}" executed successfully!`);
      } else {
        console.error(`❌ Action failed:`, result);
        alert(`❌ Action "${actionName}" failed: ${result.error}`);
      }
      
    } catch (error) {
      console.error(`❌ Error executing action:`, error);
      alert(`❌ Error executing "${actionName}": ${error.message}`);
    } finally {
      setIsExecuting(false);
      setExecutingAction(null);
    }
  };

  const handleAcknowledge = async () => {
    try {
      setIsExecuting(true);
      
      await acknowledgeAlert(alert.id, 'dashboard_user');
      console.log(`✅ Alert acknowledged: ${alert.title}`);
      
    } catch (error) {
      console.error(`❌ Error acknowledging alert:`, error);
      alert(`❌ Error acknowledging alert: ${error.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (error) {
      return timestamp;
    }
  };

  // Get available actions from alert metadata or default actions
  const availableActions = alert.available_actions || alert.metadata?.recommended_actions || [];
  const hasActions = availableActions.length > 0;

  return (
    <div className={`border-l-4 p-4 mb-4 rounded-lg shadow-sm ${getPriorityColor(alert.priority)}`}>
      {/* Alert Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <span className="text-2xl">{getPriorityIcon(alert.priority)}</span>
          <div className="flex-1">
            <h3 className="font-semibold text-lg">{alert.title}</h3>
            <p className="text-sm opacity-75 mt-1">{alert.message}</p>
            
            {/* Alert Metadata */}
            <div className="flex items-center space-x-4 mt-2 text-xs opacity-60">
              <span>🏢 {alert.department}</span>
              <span>🕒 {formatTimestamp(alert.timestamp || alert.created_at)}</span>
              <span className={`px-2 py-1 rounded-full ${alert.priority === 'critical' ? 'bg-red-200' : alert.priority === 'high' ? 'bg-orange-200' : 'bg-yellow-200'}`}>
                {alert.priority.toUpperCase()}
              </span>
              {alert.status && (
                <span className="px-2 py-1 rounded-full bg-gray-200">
                  {alert.status.toUpperCase()}
                </span>
              )}
            </div>

            {/* Alert Details */}
            {alert.metadata && (
              <div className="mt-3 text-sm">
                {alert.metadata.occupancy_rate && (
                  <div className="flex items-center space-x-2">
                    <span>📊 Occupancy:</span>
                    <span className="font-medium">{alert.metadata.occupancy_rate}%</span>
                    <span>({alert.metadata.occupied_beds}/{alert.metadata.total_beds} beds)</span>
                  </div>
                )}
                {alert.metadata.available_beds !== undefined && (
                  <div className="flex items-center space-x-2 mt-1">
                    <span>🛏️ Available:</span>
                    <span className="font-medium">{alert.metadata.available_beds} beds</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {alert.status !== 'acknowledged' && (
            <button
              onClick={handleAcknowledge}
              disabled={isExecuting}
              className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExecuting ? '⏳' : '👍'} Acknowledge
            </button>
          )}
          
          {hasActions && (
            <button
              onClick={() => setShowActions(!showActions)}
              className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
            >
              🎯 Actions ({availableActions.length})
            </button>
          )}
        </div>
      </div>

      {/* Expandable Actions Section */}
      {showActions && hasActions && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="font-medium text-sm mb-3">🎯 Available Actions:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {availableActions.map((action, index) => {
              const actionId = typeof action === 'object' ? action.id : `action_${index}`;
              const actionName = typeof action === 'object' ? action.name : action;
              const actionDescription = typeof action === 'object' ? action.description : action;
              const requiresConfirmation = typeof action === 'object' ? action.requires_confirmation : false;
              
              return (
                <button
                  key={actionId}
                  onClick={() => {
                    if (requiresConfirmation) {
                      if (window.confirm(`Are you sure you want to execute "${actionName}"?\n\n${actionDescription}`)) {
                        handleExecuteAction(actionId, actionName);
                      }
                    } else {
                      handleExecuteAction(actionId, actionName);
                    }
                  }}
                  disabled={isExecuting}
                  className={`p-3 text-left text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed ${
                    executingAction === actionId ? 'bg-blue-100 border-blue-300' : 'border-gray-300'
                  }`}
                >
                  <div className="font-medium">
                    {executingAction === actionId ? '⏳ ' : '🎯 '}
                    {actionName}
                    {requiresConfirmation && ' ⚠️'}
                  </div>
                  {actionDescription && actionDescription !== actionName && (
                    <div className="text-xs text-gray-600 mt-1">{actionDescription}</div>
                  )}
                </button>
              );
            })}
          </div>
          
          {/* Quick Actions for Common Alert Types */}
          {alert.type === 'capacity_critical' && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <h5 className="font-medium text-xs mb-2">⚡ Quick Actions:</h5>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleExecuteAction('expedite_discharge', 'Expedite Discharge')}
                  disabled={isExecuting}
                  className="px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
                >
                  🏃‍♂️ Expedite Discharge
                </button>
                <button
                  onClick={() => handleExecuteAction('activate_overflow', 'Activate Overflow')}
                  disabled={isExecuting}
                  className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                >
                  🚨 Activate Overflow
                </button>
                <button
                  onClick={() => handleExecuteAction('notify_administration', 'Notify Admin')}
                  disabled={isExecuting}
                  className="px-3 py-1 text-xs bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
                >
                  📢 Notify Admin
                </button>
              </div>
            </div>
          )}

          {alert.type === 'bed_available' && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <h5 className="font-medium text-xs mb-2">⚡ Quick Actions:</h5>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleExecuteAction('auto_assign', 'Auto-Assign Patient')}
                  disabled={isExecuting}
                  className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                >
                  🤖 Auto-Assign Patient
                </button>
                <button
                  onClick={() => handleExecuteAction('notify_admissions', 'Notify Admissions')}
                  disabled={isExecuting}
                  className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  📞 Notify Admissions
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommended Actions from Metadata */}
      {alert.metadata?.recommended_actions && !showActions && (
        <div className="mt-3 text-xs">
          <span className="font-medium">💡 Recommended: </span>
          <span className="text-gray-600">
            {alert.metadata.recommended_actions.slice(0, 2).join(', ')}
            {alert.metadata.recommended_actions.length > 2 && '...'}
          </span>
        </div>
      )}
    </div>
  );
};

export default EnhancedAlertCard;