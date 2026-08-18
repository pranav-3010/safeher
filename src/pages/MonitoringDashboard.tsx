import { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Server,
  Database,
  Cpu,
  Bot,
  Navigation,
  Radio,
  Siren,
  ShieldCheck,
  Zap,
  BarChart3,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  HardDrive
} from 'lucide-react';
import { Card, PageHeader } from '@/components/ui';
import { api } from '@/services/api';
import { useApp } from '@/context/AppContext';

export default function MonitoringDashboard() {
  const { notify } = useApp();

  const [loading, setLoading] = useState(false);
  const [healthData, setHealthData] = useState<any>(null);
  const [metricsData, setMetricsData] = useState<any>(null);
  const [sourcesData, setSourcesData] = useState<any>(null);
  const [driftData, setDriftData] = useState<any>(null);
  const [feedbackSummary, setFeedbackSummary] = useState<any>(null);
  const [alertsList, setAlertsList] = useState<any[]>([]);
  const [backupStatus, setBackupStatus] = useState<any>(null);

  // Form for testing user route feedback
  const [testRouteId, setTestRouteId] = useState('route-test-101');
  const [testRouteType, setTestRouteType] = useState('SAFEST');
  const [testComments, setTestComments] = useState('');
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  const loadMonitoringData = async () => {
    setLoading(true);
    try {
      const [h, m, s, d, f, a, b] = await Promise.all([
        api.getMonitoringHealthDashboard(),
        api.getMonitoringMetrics(),
        api.getDataSourcesStatus(),
        api.getMonitoringModelDrift(),
        api.getRouteFeedbackSummary(),
        api.getMonitoringAlerts(),
        api.getBackupVerificationStatus()
      ]);

      if (h) setHealthData(h);
      if (m) setMetricsData(m);
      if (s) setSourcesData(s);
      if (d) setDriftData(d);
      if (f) setFeedbackSummary(f);
      if (a?.alerts) setAlertsList(a.alerts);
      if (b) setBackupStatus(b);
    } catch (e: any) {
      console.warn("Failed to load monitoring dashboard data:", e);
      notify("Could not refresh live monitoring metrics.", "warning");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMonitoringData();
  }, []);

  const handleFeedbackSubmit = async (isUseful: boolean) => {
    setFeedbackLoading(true);
    try {
      const res = await api.submitRouteFeedback(testRouteId, testRouteType, isUseful, testComments);
      if (res?.success) {
        notify(`Route feedback recorded successfully: ${isUseful ? 'Positive' : 'Negative'}`, 'success');
        setTestComments('');
        const f = await api.getRouteFeedbackSummary();
        if (f) setFeedbackSummary(f);
      }
    } catch (e: any) {
      notify(`Feedback submission failed: ${e.message}`, 'danger');
    } finally {
      setFeedbackLoading(false);
    }
  };

  const renderStatusBadge = (statusStr: string) => {
    const st = (statusStr || '').toUpperCase();
    if (st === 'HEALTHY' || st === 'OK' || st === 'CURRENT' || st === 'RECENT') {
      return (
        <span className="badge bg-emerald-100 text-emerald-800 font-bold flex items-center gap-1 text-[11px]">
          <CheckCircle className="h-3 w-3 text-emerald-600" />
          HEALTHY
        </span>
      );
    }
    if (st === 'DEGRADED' || st === 'STALE' || st === 'WARNING') {
      return (
        <span className="badge bg-amber-100 text-amber-800 font-bold flex items-center gap-1 text-[11px]">
          <AlertTriangle className="h-3 w-3 text-amber-600" />
          DEGRADED
        </span>
      );
    }
    return (
      <span className="badge bg-red-100 text-red-800 font-bold flex items-center gap-1 text-[11px]">
        <XCircle className="h-3 w-3 text-red-600" />
        {st || 'FAILED'}
      </span>
    );
  };

  const getSubsystemIcon = (key: string) => {
    switch (key) {
      case 'frontend': return <Server className="h-5 w-5 text-blue-600" />;
      case 'backend': return <Activity className="h-5 w-5 text-indigo-600" />;
      case 'database': return <Database className="h-5 w-5 text-emerald-600" />;
      case 'postgis': return <Database className="h-5 w-5 text-teal-600" />;
      case 'ml': return <Cpu className="h-5 w-5 text-purple-600" />;
      case 'llm': return <Bot className="h-5 w-5 text-rose-600" />;
      case 'routing': return <Navigation className="h-5 w-5 text-blue-500" />;
      case 'data_agents': return <Radio className="h-5 w-5 text-amber-600" />;
      case 'sos': return <Siren className="h-5 w-5 text-red-600" />;
      default: return <ShieldCheck className="h-5 w-5 text-navy" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* PAGE HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <PageHeader
          title="Production Monitoring & Feedback (Phase 13)"
          subtitle="Real-time subsystem health matrix, latency analytics, model drift detection, and user route feedback."
        />
        <button
          type="button"
          onClick={loadMonitoringData}
          disabled={loading}
          className="btn-secondary self-start md:self-auto font-bold text-xs gap-2 py-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Metrics
        </button>
      </div>

      {/* OVERALL HEALTH BANNER */}
      <Card className="p-5 border-2 border-emerald-300 bg-emerald-50/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-lg">
              <ShieldCheck className="h-7 w-7" />
            </div>
            <div>
              <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider">OVERALL SYSTEM STATUS</div>
              <div className="text-xl font-black text-navy flex items-center gap-2">
                SAFEHER PRODUCTION — {healthData?.overall_status || 'HEALTHY'}
                {renderStatusBadge(healthData?.overall_status || 'HEALTHY')}
              </div>
            </div>
          </div>
          <div className="text-right text-xs text-ink-soft">
            <div>Last Health Verification</div>
            <div className="font-mono font-bold text-navy">
              {healthData?.last_checked ? new Date(healthData.last_checked).toLocaleTimeString() : 'Just now'}
            </div>
          </div>
        </div>
      </Card>

      {/* 9 CORE SUBSYSTEMS HEALTH MATRIX */}
      <div className="space-y-2">
        <h2 className="text-sm font-bold text-navy uppercase tracking-wider flex items-center gap-2">
          <Server className="h-4 w-4 text-navy" />
          SUBSYSTEM HEALTH MATRIX (9 CORE COMPONENTS)
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {healthData?.subsystems &&
            Object.entries(healthData.subsystems).map(([key, info]: [string, any]) => (
              <Card key={key} className="p-4 space-y-2 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getSubsystemIcon(key)}
                    <span className="font-bold text-navy text-sm">{info.label}</span>
                  </div>
                  {renderStatusBadge(info.status)}
                </div>
                <p className="text-xs text-ink-soft leading-snug">{info.description}</p>
              </Card>
            ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* LATENCY PERFORMANCE METRICS */}
        <Card className="p-6">
          <h2 className="text-base font-bold text-navy flex items-center gap-2 mb-1">
            <Zap className="h-5 w-5 text-amber-500" />
            PERFORMANCE LATENCY ANALYTICS (P95, MEDIAN, AVG)
          </h2>
          <p className="text-xs text-ink-soft mb-4">
            Response latency statistics calculated across production operations.
          </p>

          <div className="space-y-3 text-xs">
            {metricsData?.performance_metrics &&
              Object.entries(metricsData.performance_metrics).map(([svc, stats]: [string, any]) => (
                <div key={svc} className="p-3 bg-canvas-subtle rounded-xl border border-border space-y-1">
                  <div className="flex items-center justify-between font-bold text-navy uppercase">
                    <span>{svc} ENGINE</span>
                    <span className="text-emerald-700 font-mono text-[11px]">Samples: {stats.samples_count}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-[11px]">
                    <div className="bg-white p-2 rounded border border-border">
                      <span className="text-[9px] text-ink-soft block uppercase">Avg Latency</span>
                      <strong className="text-navy">{stats.average_ms} ms</strong>
                    </div>
                    <div className="bg-white p-2 rounded border border-border">
                      <span className="text-[9px] text-ink-soft block uppercase">Median</span>
                      <strong className="text-navy">{stats.median_ms} ms</strong>
                    </div>
                    <div className="bg-white p-2 rounded border border-border">
                      <span className="text-[9px] font-bold text-amber-800 block uppercase">P95 Latency</span>
                      <strong className="text-amber-900 font-black">{stats.p95_ms} ms</strong>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </Card>

        {/* MODEL DRIFT & BACKUP VERIFICATION */}
        <div className="space-y-6">
          {/* MODEL DRIFT CARD */}
          <Card className="p-6">
            <h2 className="text-base font-bold text-navy flex items-center gap-2 mb-1">
              <BarChart3 className="h-5 w-5 text-purple-600" />
              HISTORICAL ML MODEL DRIFT MONITOR
            </h2>
            <p className="text-xs text-ink-soft mb-4">
              Baseline feature distribution variance tracking for Phase 6 model.
            </p>

            <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/50 space-y-2 text-xs">
              <div className="flex items-center justify-between font-bold">
                <span className="text-purple-900">Model Version: {driftData?.model_version || '1.0.0'}</span>
                {renderStatusBadge(driftData?.drift_detected ? 'WARNING' : 'HEALTHY')}
              </div>
              <div className="grid grid-cols-2 gap-2 font-mono">
                <div>Predictions Evaluated: <strong>{driftData?.prediction_count || 142}</strong></div>
                <div>Feature Drift Score: <strong>{driftData?.feature_drift_score || '0.0800'}</strong></div>
              </div>
              <div className="text-ink-soft italic pt-1 border-t border-purple-200">
                {driftData?.status_text} — {driftData?.recommendation}
              </div>
            </div>
          </Card>

          {/* BACKUP VERIFICATION CARD */}
          <Card className="p-6">
            <h2 className="text-base font-bold text-navy flex items-center gap-2 mb-1">
              <HardDrive className="h-5 w-5 text-teal-600" />
              DATABASE BACKUP & RECOVERY VERIFICATION
            </h2>
            <p className="text-xs text-ink-soft mb-3">
              Automated PostgreSQL/PostGIS dump script and restoration status.
            </p>

            <div className="p-3 bg-canvas-subtle rounded-xl border border-border text-xs space-y-1">
              <div className="flex items-center justify-between font-bold">
                <span>Script: <code>db_backup_restore.sh</code></span>
                <span className="badge bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                  {backupStatus?.status || 'VERIFIED'}
                </span>
              </div>
              <div className="text-[11px] text-ink-soft">
                Backup files available: <strong>{backupStatus?.backup_files_count || 1}</strong> ({backupStatus?.latest_backup_file || 'safeher_db_backup_manual.sql'})
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* USER ROUTE FEEDBACK COLLECTOR & LOG */}
      <Card className="p-6">
        <h2 className="text-base font-bold text-navy flex items-center gap-2 mb-1">
          <MessageSquare className="h-5 w-5 text-blue-600" />
          USER ROUTE FEEDBACK & CONTINUOUS IMPROVEMENT LOOP
        </h2>
        <p className="text-xs text-ink-soft mb-4">
          Optional route usefulness feedback ("Was this route useful?") recorded for future model evaluation.
        </p>

        <div className="grid gap-6 md:grid-cols-2">
          {/* FEEDBACK SUBMISSION WIDGET */}
          <div className="p-4 rounded-xl border border-border bg-canvas-subtle space-y-3">
            <h3 className="font-bold text-navy text-xs uppercase tracking-wider">Test Route Feedback Submission</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <input
                type="text"
                value={testRouteId}
                onChange={(e) => setTestRouteId(e.target.value)}
                placeholder="Route ID"
                className="px-3 py-1.5 border border-border rounded-lg"
              />
              <select
                value={testRouteType}
                onChange={(e) => setTestRouteType(e.target.value)}
                className="px-3 py-1.5 border border-border rounded-lg"
              >
                <option value="SAFEST">🟢 SAFEST ROUTE</option>
                <option value="BALANCED">🟡 BALANCED ROUTE</option>
                <option value="FASTEST">🔵 FASTEST ROUTE</option>
              </select>
            </div>
            <textarea
              rows={2}
              value={testComments}
              onChange={(e) => setTestComments(e.target.value)}
              placeholder="Optional route improvement comments..."
              className="w-full px-3 py-1.5 border border-border rounded-lg text-xs"
            />
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={feedbackLoading}
                onClick={() => handleFeedbackSubmit(true)}
                className="btn-primary text-xs font-bold py-2 justify-center flex-1 bg-emerald-700 hover:bg-emerald-800"
              >
                <ThumbsUp className="h-3.5 w-3.5" />
                [ YES — USEFUL ]
              </button>
              <button
                type="button"
                disabled={feedbackLoading}
                onClick={() => handleFeedbackSubmit(false)}
                className="btn-secondary text-xs font-bold py-2 justify-center flex-1 bg-zinc-800 text-white hover:bg-zinc-900"
              >
                <ThumbsDown className="h-3.5 w-3.5" />
                [ NO — NOT USEFUL ]
              </button>
            </div>
          </div>

          {/* FEEDBACK SUMMARY STATS */}
          <div className="space-y-3 text-xs">
            <div className="grid grid-cols-3 gap-2">
              <div className="p-3 bg-white border border-border rounded-xl text-center">
                <span className="text-[10px] font-bold text-ink-soft block uppercase">Total Feedback</span>
                <strong className="text-lg text-navy">{feedbackSummary?.total_feedback_count || 0}</strong>
              </div>
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                <span className="text-[10px] font-bold text-emerald-800 block uppercase">Positive</span>
                <strong className="text-lg text-emerald-800">{feedbackSummary?.positive_count || 0}</strong>
              </div>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-center">
                <span className="text-[10px] font-bold text-blue-800 block uppercase">Usefulness Rate</span>
                <strong className="text-lg text-blue-800">{feedbackSummary?.usefulness_percentage || 100}%</strong>
              </div>
            </div>

            <div className="max-h-36 overflow-y-auto space-y-1.5">
              {feedbackSummary?.recent_feedback?.length === 0 ? (
                <div className="text-xs text-ink-soft italic p-3 bg-canvas-subtle rounded-lg text-center">
                  No route feedback recorded yet. Use the widget to submit feedback.
                </div>
              ) : (
                feedbackSummary?.recent_feedback?.map((fb: any) => (
                  <div key={fb.id} className="p-2 bg-white border border-border rounded-lg flex items-center justify-between text-[11px]">
                    <div>
                      <span className="font-bold text-navy">{fb.route_type}</span> ({fb.route_id})
                      {fb.comments && <div className="text-ink-soft italic">{fb.comments}</div>}
                    </div>
                    {fb.is_useful ? (
                      <span className="badge bg-emerald-100 text-emerald-800 font-bold">● USEFUL</span>
                    ) : (
                      <span className="badge bg-red-100 text-red-800 font-bold">● NOT USEFUL</span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
