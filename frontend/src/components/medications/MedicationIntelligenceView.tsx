'use client';

import { useState, useEffect } from 'react';
import { medicationIntelligenceService } from '@/services/medicationIntelligence';
import { medicationsService } from '@/services/medications';
import {
  UserMedicationAlert,
  MedicationVitalsCorrelation,
  Medication,
} from '@/types';
import { InteractionAlertCard } from './InteractionAlertCard';
import { MedicationCorrelationCard } from './MedicationCorrelationCard';
import { AlertTriangle, Activity, Info } from 'lucide-react';

export function MedicationIntelligenceView() {
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<UserMedicationAlert[]>([]);
  const [correlations, setCorrelations] = useState<MedicationVitalsCorrelation[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [selectedMedicationId, setSelectedMedicationId] = useState<string | null>(null);
  const [loadingCorrelations, setLoadingCorrelations] = useState(false);
  const [activeTab, setActiveTab] = useState<'alerts' | 'correlations'>('alerts');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedMedicationId) {
      loadCorrelations(selectedMedicationId);
    }
  }, [selectedMedicationId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [alertsData, medsData] = await Promise.all([
        medicationIntelligenceService.getInteractionAlerts(),
        medicationsService.getMedications(),
      ]);

      setAlerts(alertsData.alerts || []);
      setMedications(medsData.medications || []);

      // Auto-select first active medication for correlations
      const firstActiveMed = medsData.medications?.find((m) => m.is_active);
      if (firstActiveMed) {
        setSelectedMedicationId(firstActiveMed.id);
      }
    } catch (error) {
      console.error('Error loading medication intelligence:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCorrelations = async (medicationId: string) => {
    setLoadingCorrelations(true);
    try {
      const data = await medicationIntelligenceService.getMedicationVitalsCorrelations(
        medicationId,
        30
      );
      setCorrelations(data.correlations || []);
    } catch (error) {
      console.error('Error loading correlations:', error);
      // If Pro+ feature not available, show empty state
      setCorrelations([]);
    } finally {
      setLoadingCorrelations(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await medicationIntelligenceService.acknowledgeAlert(alertId);
      setAlerts(
        alerts.map((a) => (a.id === alertId ? { ...a, is_acknowledged: true } : a))
      );
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleDismissAlert = async (alertId: string) => {
    try {
      await medicationIntelligenceService.dismissAlert(alertId);
      setAlerts(alerts.filter((a) => a.id !== alertId));
    } catch (error) {
      console.error('Error dismissing alert:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  const unacknowledgedAlerts = alerts.filter((a) => !a.is_acknowledged && !a.is_dismissed);
  const criticalAlerts = alerts.filter((a) => a.severity === 'critical' && !a.is_dismissed);
  const highAlerts = alerts.filter((a) => a.severity === 'high' && !a.is_dismissed);

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
            <div>
              <p className="text-sm font-medium text-red-900 dark:text-red-200">
                Critical Alerts
              </p>
              <p className="text-2xl font-bold text-red-900 dark:text-red-100">
                {criticalAlerts.length}
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg border border-orange-200 dark:border-orange-800">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-orange-600 dark:text-orange-400" />
            <div>
              <p className="text-sm font-medium text-orange-900 dark:text-orange-200">
                High Priority
              </p>
              <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                {highAlerts.length}
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <div>
              <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                Correlations Found
              </p>
              <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                {correlations.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('alerts')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'alerts'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Interaction Alerts ({unacknowledgedAlerts.length})
          </div>
        </button>
        <button
          onClick={() => setActiveTab('correlations')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'correlations'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Vitals Correlations (Pro+)
          </div>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="text-center py-12">
              <Info className="w-16 h-16 text-green-500 dark:text-green-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No Interactions Detected
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Your current medications and supplements don't have any known interactions
              </p>
            </div>
          ) : (
            <>
              {/* Critical and High alerts first */}
              {[...criticalAlerts, ...highAlerts].map((alert) => (
                <InteractionAlertCard
                  key={alert.id}
                  alert={alert}
                  onAcknowledge={() => handleAcknowledgeAlert(alert.id)}
                  onDismiss={() => handleDismissAlert(alert.id)}
                />
              ))}

              {/* Then moderate and low */}
              {alerts
                .filter(
                  (a) =>
                    (a.severity === 'moderate' || a.severity === 'low') &&
                    !a.is_dismissed
                )
                .map((alert) => (
                  <InteractionAlertCard
                    key={alert.id}
                    alert={alert}
                    onAcknowledge={() => handleAcknowledgeAlert(alert.id)}
                    onDismiss={() => handleDismissAlert(alert.id)}
                  />
                ))}

              {/* Show acknowledged alerts at the end */}
              {alerts.filter((a) => a.is_acknowledged && !a.is_dismissed).length > 0 && (
                <div className="pt-6 mt-6 border-t border-slate-200 dark:border-slate-700">
                  <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4">
                    Acknowledged Alerts
                  </h3>
                  {alerts
                    .filter((a) => a.is_acknowledged && !a.is_dismissed)
                    .map((alert) => (
                      <InteractionAlertCard
                        key={alert.id}
                        alert={alert}
                        onDismiss={() => handleDismissAlert(alert.id)}
                      />
                    ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'correlations' && (
        <div className="space-y-4">
          {/* Medication selector */}
          {medications.filter((m) => m.is_active).length > 0 && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Select Medication
              </label>
              <select
                value={selectedMedicationId || ''}
                onChange={(e) => setSelectedMedicationId(e.target.value)}
                className="w-full max-w-md px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-slate-700 dark:text-slate-100"
              >
                {medications
                  .filter((m) => m.is_active)
                  .map((med) => (
                    <option key={med.id} value={med.id}>
                      {med.medication_name} - {med.dosage}
                    </option>
                  ))}
              </select>
            </div>
          )}

          {loadingCorrelations ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            </div>
          ) : correlations.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No Correlations Yet
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                We need at least 5 days of medication adherence data and Oura vitals to detect
                correlations
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                This is a Pro+ exclusive feature
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {correlations.map((correlation) => (
                <MedicationCorrelationCard key={correlation.id} correlation={correlation} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
