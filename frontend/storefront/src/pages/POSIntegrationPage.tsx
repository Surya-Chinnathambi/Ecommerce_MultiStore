import { useState, useEffect } from 'react';
import { Settings, Database, FileSpreadsheet, Wifi, WifiOff, RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import api from '../lib/api';

interface POSConfig {
    pos_type: string;
    connection_type: string;
    mysql_host?: string;
    mysql_port?: number;
    mysql_user?: string;
    mysql_password?: string;
    mysql_database?: string;
    sqlite_path?: string;
    export_folder?: string;
    sync_interval_minutes: number;
    inventory_sync_interval_minutes: number;
    auto_sync_enabled: boolean;
}

interface SyncStatus {
    connection_status: string;
    last_sync_at?: string;
    products_synced: number;
    inventory_synced: number;
    sync_in_progress: boolean;
    errors: string[];
}

interface SupportedPOS {
    id: string;
    name: string;
    description: string;
    connection_types: string[];
    status: string;
}

export default function POSIntegrationPage() {
    const [activeTab, setActiveTab] = useState<'setup' | 'status' | 'logs'>('setup');
    const [posType, setPosType] = useState('kasapos');
    const [connectionType, setConnectionType] = useState('mysql');
    const [config, setConfig] = useState<POSConfig>({
        pos_type: 'kasapos',
        connection_type: 'mysql',
        mysql_host: 'localhost',
        mysql_port: 3306,
        mysql_user: 'root',
        mysql_password: '',
        mysql_database: 'kasapos',
        sqlite_path: '',
        export_folder: '',
        sync_interval_minutes: 5,
        inventory_sync_interval_minutes: 1,
        auto_sync_enabled: true
    });
    const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
    const [supportedPOS, setSupportedPOS] = useState<SupportedPOS[]>([]);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string; products_found?: number } | null>(null);
    const [testing, setTesting] = useState(false);
    const [saving, setSaving] = useState(false);
    const [syncing, setSyncing] = useState(false);

    useEffect(() => {
        fetchSupportedPOS();
        fetchSyncStatus();
    }, []);

    const fetchSupportedPOS = async () => {
        try {
            const response = await api.get('/pos-integration/supported-pos');
            if (response.data.success) {
                setSupportedPOS(response.data.data);
            }
        } catch (error) {
            console.error('Failed to fetch supported POS:', error);
        }
    };

    const fetchSyncStatus = async () => {
        try {
            const response = await api.get('/pos-integration/status/current-store');
            if (response.data.success) {
                setSyncStatus(response.data.data);
            }
        } catch (error) {
            console.error('Failed to fetch sync status:', error);
        }
    };

    const testConnection = async () => {
        setTesting(true);
        setTestResult(null);

        try {
            const response = await api.post('/pos-integration/test-connection', {
                pos_type: posType,
                connection_type: connectionType,
                mysql_host: config.mysql_host,
                mysql_port: config.mysql_port,
                mysql_user: config.mysql_user,
                mysql_password: config.mysql_password,
                mysql_database: config.mysql_database,
                sqlite_path: config.sqlite_path,
                export_folder: config.export_folder
            });

            if (response.data.success) {
                setTestResult(response.data.data);
            }
        } catch (error) {
            setTestResult({ success: false, message: 'Connection test failed' });
        } finally {
            setTesting(false);
        }
    };

    const saveConfig = async () => {
        setSaving(true);
        try {
            const response = await api.post('/pos-integration/config', {
                ...config,
                pos_type: posType,
                connection_type: connectionType,
                store_id: 'current-store' // Replace with actual store ID
            });

            if (response.data.success) {
                alert('Configuration saved successfully!');
            }
        } catch (error) {
            alert('Failed to save configuration');
        } finally {
            setSaving(false);
        }
    };

    const triggerSync = async (syncType: string) => {
        setSyncing(true);
        try {
            const response = await api.post(`/pos-integration/trigger-sync/current-store?sync_type=${syncType}`);
            if (response.data.success) {
                alert(`${syncType} sync triggered successfully!`);
                fetchSyncStatus();
            }
        } catch (error) {
            alert('Failed to trigger sync');
        } finally {
            setSyncing(false);
        }
    };

    const ConnectionTypeIcon = ({ type }: { type: string }) => {
        switch (type) {
            case 'mysql':
            case 'sqlite':
                return <Database className="h-5 w-5" />;
            case 'csv':
            case 'excel':
                return <FileSpreadsheet className="h-5 w-5" />;
            case 'api':
                return <Wifi className="h-5 w-5" />;
            default:
                return <Settings className="h-5 w-5" />;
        }
    };

    return (
        <div className="min-h-screen bg-bg-secondary p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-text-primary mb-2">
                        POS Integration
                    </h1>
                    <p className="text-text-secondary">
                        Connect your billing software to sync products, inventory, and sales
                    </p>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {[
                        { id: 'setup', label: 'Setup', icon: Settings },
                        { id: 'status', label: 'Status', icon: Wifi },
                        { id: 'logs', label: 'Sync Logs', icon: Clock }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as 'setup' | 'status' | 'logs')}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${activeTab === tab.id
                                ? 'bg-theme-primary text-white'
                                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-primary'
                                }`}
                        >
                            <tab.icon className="h-4 w-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Setup Tab */}
                {activeTab === 'setup' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* POS Selection */}
                        <div className="lg:col-span-1">
                            <div className="card p-6">
                                <h2 className="text-lg font-semibold text-text-primary mb-4">
                                    Select POS Software
                                </h2>
                                <div className="space-y-3">
                                    {supportedPOS.map(pos => (
                                        <button
                                            key={pos.id}
                                            onClick={() => pos.status === 'available' && setPosType(pos.id)}
                                            disabled={pos.status !== 'available'}
                                            className={`w-full p-4 rounded-xl border-2 text-left transition-all ${posType === pos.id
                                                ? 'border-theme-primary bg-theme-primary/10'
                                                : pos.status === 'available'
                                                    ? 'border-border-color hover:border-theme-primary/50'
                                                    : 'border-border-color opacity-50 cursor-not-allowed'
                                                }`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="font-semibold text-text-primary">{pos.name}</span>
                                                {pos.status === 'coming_soon' && (
                                                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                                                        Coming Soon
                                                    </span>
                                                )}
                                                {posType === pos.id && (
                                                    <CheckCircle className="h-5 w-5 text-theme-primary" />
                                                )}
                                            </div>
                                            <p className="text-sm text-text-secondary mt-1">{pos.description}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Configuration */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Connection Type */}
                            <div className="card p-6">
                                <h2 className="text-lg font-semibold text-text-primary mb-4">
                                    Connection Method
                                </h2>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {['mysql', 'sqlite', 'csv', 'excel'].map(type => (
                                        <button
                                            key={type}
                                            onClick={() => setConnectionType(type)}
                                            className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${connectionType === type
                                                ? 'border-theme-primary bg-theme-primary/10'
                                                : 'border-border-color hover:border-theme-primary/50'
                                                }`}
                                        >
                                            <ConnectionTypeIcon type={type} />
                                            <span className="text-sm font-medium text-text-primary uppercase">
                                                {type}
                                            </span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Connection Settings */}
                            <div className="card p-6">
                                <h2 className="text-lg font-semibold text-text-primary mb-4">
                                    Connection Settings
                                </h2>

                                {connectionType === 'mysql' && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                                Host
                                            </label>
                                            <input
                                                type="text"
                                                value={config.mysql_host}
                                                onChange={e => setConfig({ ...config, mysql_host: e.target.value })}
                                                className="input"
                                                placeholder="localhost"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                                Port
                                            </label>
                                            <input
                                                type="number"
                                                value={config.mysql_port}
                                                onChange={e => setConfig({ ...config, mysql_port: parseInt(e.target.value) })}
                                                className="input"
                                                placeholder="3306"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                                Username
                                            </label>
                                            <input
                                                type="text"
                                                value={config.mysql_user}
                                                onChange={e => setConfig({ ...config, mysql_user: e.target.value })}
                                                className="input"
                                                placeholder="root"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                                Password
                                            </label>
                                            <input
                                                type="password"
                                                value={config.mysql_password}
                                                onChange={e => setConfig({ ...config, mysql_password: e.target.value })}
                                                className="input"
                                                placeholder="••••••••"
                                            />
                                        </div>
                                        <div className="md:col-span-2">
                                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                                Database Name
                                            </label>
                                            <input
                                                type="text"
                                                value={config.mysql_database}
                                                onChange={e => setConfig({ ...config, mysql_database: e.target.value })}
                                                className="input"
                                                placeholder="kasapos"
                                            />
                                        </div>
                                    </div>
                                )}

                                {connectionType === 'sqlite' && (
                                    <div>
                                        <label className="block text-sm font-medium text-text-secondary mb-1">
                                            Database File Path
                                        </label>
                                        <input
                                            type="text"
                                            value={config.sqlite_path}
                                            onChange={e => setConfig({ ...config, sqlite_path: e.target.value })}
                                            className="input"
                                            placeholder="C:\KasaPOS\data\kasapos.db"
                                        />
                                        <p className="text-sm text-text-tertiary mt-1">
                                            Full path to your KasaPOS SQLite database file
                                        </p>
                                    </div>
                                )}

                                {(connectionType === 'csv' || connectionType === 'excel') && (
                                    <div>
                                        <label className="block text-sm font-medium text-text-secondary mb-1">
                                            Export Folder Path
                                        </label>
                                        <input
                                            type="text"
                                            value={config.export_folder}
                                            onChange={e => setConfig({ ...config, export_folder: e.target.value })}
                                            className="input"
                                            placeholder="C:\KasaPOS\exports"
                                        />
                                        <p className="text-sm text-text-tertiary mt-1">
                                            Folder where KasaPOS exports product/inventory files
                                        </p>
                                    </div>
                                )}

                                {/* Test Connection Button */}
                                <div className="mt-6 flex items-center gap-4">
                                    <button
                                        onClick={testConnection}
                                        disabled={testing}
                                        className="btn btn-secondary flex items-center gap-2"
                                    >
                                        {testing ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Wifi className="h-4 w-4" />
                                        )}
                                        Test Connection
                                    </button>

                                    {testResult && (
                                        <div className={`flex items-center gap-2 ${testResult.success ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {testResult.success ? (
                                                <CheckCircle className="h-5 w-5" />
                                            ) : (
                                                <XCircle className="h-5 w-5" />
                                            )}
                                            <span className="text-sm">
                                                {testResult.message}
                                                {testResult.products_found !== undefined && (
                                                    <span className="ml-2 font-medium">
                                                        ({testResult.products_found} products found)
                                                    </span>
                                                )}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Sync Settings */}
                            <div className="card p-6">
                                <h2 className="text-lg font-semibold text-text-primary mb-4">
                                    Sync Settings
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-text-secondary mb-1" htmlFor="productSyncInterval">
                                            Product Sync Interval
                                        </label>
                                        <select
                                            id="productSyncInterval"
                                            title="Product Sync Interval"
                                            value={config.sync_interval_minutes}
                                            onChange={e => setConfig({ ...config, sync_interval_minutes: parseInt(e.target.value) })}
                                            className="input"
                                        >
                                            <option value={1}>Every 1 minute</option>
                                            <option value={5}>Every 5 minutes</option>
                                            <option value={10}>Every 10 minutes</option>
                                            <option value={15}>Every 15 minutes</option>
                                            <option value={30}>Every 30 minutes</option>
                                            <option value={60}>Every hour</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-text-secondary mb-1" htmlFor="inventorySyncInterval">
                                            Inventory Sync Interval
                                        </label>
                                        <select
                                            id="inventorySyncInterval"
                                            title="Inventory Sync Interval"
                                            value={config.inventory_sync_interval_minutes}
                                            onChange={e => setConfig({ ...config, inventory_sync_interval_minutes: parseInt(e.target.value) })}
                                            className="input"
                                        >
                                            <option value={1}>Every 1 minute</option>
                                            <option value={2}>Every 2 minutes</option>
                                            <option value={5}>Every 5 minutes</option>
                                        </select>
                                        <p className="text-sm text-text-tertiary mt-1">
                                            During business hours (9 AM - 10 PM)
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-4 flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        id="autoSync"
                                        checked={config.auto_sync_enabled}
                                        onChange={e => setConfig({ ...config, auto_sync_enabled: e.target.checked })}
                                        className="h-4 w-4 rounded border-border-color text-theme-primary focus:ring-theme-primary"
                                    />
                                    <label htmlFor="autoSync" className="text-sm text-text-primary">
                                        Enable automatic sync
                                    </label>
                                </div>
                            </div>

                            {/* Save Button */}
                            <div className="flex justify-end">
                                <button
                                    onClick={saveConfig}
                                    disabled={saving}
                                    className="btn btn-primary flex items-center gap-2"
                                >
                                    {saving ? (
                                        <RefreshCw className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <CheckCircle className="h-4 w-4" />
                                    )}
                                    Save Configuration
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Status Tab */}
                {activeTab === 'status' && (
                    <div className="space-y-6">
                        {/* Connection Status Card */}
                        <div className="card p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-lg font-semibold text-text-primary">
                                    Sync Status
                                </h2>
                                <button
                                    onClick={fetchSyncStatus}
                                    className="btn btn-ghost btn-sm"
                                    title="Refresh sync status"
                                    aria-label="Refresh sync status"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div className="text-center p-4 bg-bg-tertiary rounded-xl">
                                    <div className={`inline-flex p-3 rounded-full mb-2 ${syncStatus?.connection_status === 'connected'
                                        ? 'bg-green-100 text-green-600'
                                        : 'bg-red-100 text-red-600'
                                        }`}>
                                        {syncStatus?.connection_status === 'connected' ? (
                                            <Wifi className="h-6 w-6" />
                                        ) : (
                                            <WifiOff className="h-6 w-6" />
                                        )}
                                    </div>
                                    <p className="text-sm text-text-secondary">Connection</p>
                                    <p className="font-semibold text-text-primary capitalize">
                                        {syncStatus?.connection_status || 'Not Configured'}
                                    </p>
                                </div>

                                <div className="text-center p-4 bg-bg-tertiary rounded-xl">
                                    <div className="inline-flex p-3 rounded-full bg-blue-100 text-blue-600 mb-2">
                                        <Clock className="h-6 w-6" />
                                    </div>
                                    <p className="text-sm text-text-secondary">Last Sync</p>
                                    <p className="font-semibold text-text-primary">
                                        {syncStatus?.last_sync_at
                                            ? new Date(syncStatus.last_sync_at).toLocaleTimeString()
                                            : 'Never'}
                                    </p>
                                </div>

                                <div className="text-center p-4 bg-bg-tertiary rounded-xl">
                                    <div className="inline-flex p-3 rounded-full bg-purple-100 text-purple-600 mb-2">
                                        <Database className="h-6 w-6" />
                                    </div>
                                    <p className="text-sm text-text-secondary">Products Synced</p>
                                    <p className="font-semibold text-text-primary">
                                        {syncStatus?.products_synced || 0}
                                    </p>
                                </div>

                                <div className="text-center p-4 bg-bg-tertiary rounded-xl">
                                    <div className={`inline-flex p-3 rounded-full mb-2 ${syncStatus?.sync_in_progress
                                        ? 'bg-yellow-100 text-yellow-600'
                                        : 'bg-green-100 text-green-600'
                                        }`}>
                                        {syncStatus?.sync_in_progress ? (
                                            <RefreshCw className="h-6 w-6 animate-spin" />
                                        ) : (
                                            <CheckCircle className="h-6 w-6" />
                                        )}
                                    </div>
                                    <p className="text-sm text-text-secondary">Status</p>
                                    <p className="font-semibold text-text-primary">
                                        {syncStatus?.sync_in_progress ? 'Syncing...' : 'Ready'}
                                    </p>
                                </div>
                            </div>

                            {/* Errors */}
                            {syncStatus?.errors && syncStatus.errors.length > 0 && (
                                <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl">
                                    <div className="flex items-center gap-2 text-red-600 mb-2">
                                        <AlertTriangle className="h-5 w-5" />
                                        <span className="font-medium">Sync Errors</span>
                                    </div>
                                    <ul className="text-sm text-red-600 space-y-1">
                                        {syncStatus.errors.map((error, idx) => (
                                            <li key={idx}>• {error}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        {/* Manual Sync Actions */}
                        <div className="card p-6">
                            <h2 className="text-lg font-semibold text-text-primary mb-4">
                                Manual Sync
                            </h2>
                            <div className="flex flex-wrap gap-3">
                                <button
                                    onClick={() => triggerSync('delta')}
                                    disabled={syncing}
                                    className="btn btn-secondary flex items-center gap-2"
                                >
                                    <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                                    Delta Sync
                                </button>
                                <button
                                    onClick={() => triggerSync('inventory_only')}
                                    disabled={syncing}
                                    className="btn btn-secondary flex items-center gap-2"
                                >
                                    <Database className="h-4 w-4" />
                                    Inventory Only
                                </button>
                                <button
                                    onClick={() => triggerSync('full')}
                                    disabled={syncing}
                                    className="btn btn-ghost flex items-center gap-2"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                    Full Sync
                                </button>
                            </div>
                            <p className="text-sm text-text-tertiary mt-3">
                                <strong>Delta:</strong> Only changed products |
                                <strong> Inventory:</strong> Stock levels only |
                                <strong> Full:</strong> All products (slower)
                            </p>
                        </div>
                    </div>
                )}

                {/* Logs Tab */}
                {activeTab === 'logs' && (
                    <div className="card p-6">
                        <h2 className="text-lg font-semibold text-text-primary mb-4">
                            Recent Sync Logs
                        </h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border-color">
                                        <th className="text-left py-3 px-4 font-medium text-text-secondary">Time</th>
                                        <th className="text-left py-3 px-4 font-medium text-text-secondary">Type</th>
                                        <th className="text-left py-3 px-4 font-medium text-text-secondary">Products</th>
                                        <th className="text-left py-3 px-4 font-medium text-text-secondary">Created</th>
                                        <th className="text-left py-3 px-4 font-medium text-text-secondary">Updated</th>
                                        <th className="text-left py-3 px-4 font-medium text-text-secondary">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {[
                                        { time: '10:00 AM', type: 'delta', products: 50, created: 5, updated: 45, status: 'success' },
                                        { time: '9:55 AM', type: 'inventory', products: 150, created: 0, updated: 150, status: 'success' },
                                        { time: '9:50 AM', type: 'inventory', products: 148, created: 0, updated: 148, status: 'success' },
                                        { time: '9:45 AM', type: 'delta', products: 12, created: 2, updated: 10, status: 'success' },
                                    ].map((log, idx) => (
                                        <tr key={idx} className="border-b border-border-color hover:bg-bg-tertiary">
                                            <td className="py-3 px-4 text-text-primary">{log.time}</td>
                                            <td className="py-3 px-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${log.type === 'delta'
                                                    ? 'bg-blue-100 text-blue-700'
                                                    : log.type === 'inventory'
                                                        ? 'bg-purple-100 text-purple-700'
                                                        : 'bg-gray-100 text-gray-700'
                                                    }`}>
                                                    {log.type}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-text-primary">{log.products}</td>
                                            <td className="py-3 px-4 text-green-600">+{log.created}</td>
                                            <td className="py-3 px-4 text-blue-600">{log.updated}</td>
                                            <td className="py-3 px-4">
                                                <span className="flex items-center gap-1 text-green-600">
                                                    <CheckCircle className="h-4 w-4" />
                                                    {log.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div >
    );
}
