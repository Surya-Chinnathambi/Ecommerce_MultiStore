import React, { useState, useEffect } from 'react';
import { Plus, RefreshCw, Download, Settings, Trash2, Play } from 'lucide-react';
import { billingApi, BillingIntegration, BillingProvider } from '../lib/billing-api';
import { useAuthStore } from '../store/authStore';
import { toast } from '../components/ui/Toaster';

const BillingIntegrationPage: React.FC = () => {
    const { token } = useAuthStore();
    const [integrations, setIntegrations] = useState<BillingIntegration[]>([]);
    const [providers, setProviders] = useState<BillingProvider[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [integrationsData, providersData] = await Promise.all([
                billingApi.listIntegrations(token!),
                billingApi.getProviders()
            ]);
            setIntegrations(integrationsData);
            setProviders(providersData.providers);
        } catch (error) {
            toast.error('Failed to load billing integrations');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleSync = async (integrationId: string) => {
        try {
            await billingApi.syncIntegration(token!, integrationId, {
                entity_types: ['invoice', 'product'],
                direction: 'push'
            });
            toast.success('Sync completed successfully');
            loadData();
        } catch (error: any) {
            toast.error(error.message || 'Sync failed');
        }
    };

    const handleDelete = async (integrationId: string) => {
        if (!confirm('Are you sure you want to delete this integration?')) return;

        try {
            await billingApi.deleteIntegration(token!, integrationId);
            toast.success('Integration deleted');
            loadData();
        } catch (error) {
            toast.error('Failed to delete integration');
        }
    };

    const handleExportCSV = async (entityType: 'invoice' | 'product' | 'customer') => {
        try {
            const result = await billingApi.exportToCSV(token!, entityType);

            // Create download link
            const link = document.createElement('a');
            link.href = result.file_url;
            link.download = result.file_name;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            toast.success(`Exported ${result.row_count} records`);
        } catch (error) {
            toast.error('Export failed');
        }
    };

    const getProviderInfo = (providerId: string) => {
        return providers.find(p => p.id === providerId);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Billing Integration</h1>
                <p className="text-gray-600">Connect your e-commerce platform with billing software</p>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <button
                    onClick={() => toast.info('Create integration modal coming soon')}
                    className="flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    New Integration
                </button>
                <button
                    onClick={() => handleExportCSV('invoice')}
                    className="flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors"
                >
                    <Download className="w-5 h-5" />
                    Export Invoices
                </button>
                <button
                    onClick={() => handleExportCSV('product')}
                    className="flex items-center justify-center gap-2 bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 transition-colors"
                >
                    <Download className="w-5 h-5" />
                    Export Products
                </button>
                <button
                    onClick={loadData}
                    className="flex items-center justify-center gap-2 bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 transition-colors"
                >
                    <RefreshCw className="w-5 h-5" />
                    Refresh
                </button>
            </div>

            {/* Integrations List */}
            {integrations.length === 0 ? (
                <div className="bg-white rounded-lg shadow-md p-12 text-center">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Settings className="w-8 h-8 text-blue-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No Integrations Yet</h3>
                    <p className="text-gray-600 mb-6">Get started by creating your first billing integration</p>
                    <button
                        onClick={() => toast.info('Create integration modal coming soon')}
                        className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        <Plus className="w-5 h-5" />
                        Create Integration
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {integrations.map((integration) => {
                        const providerInfo = getProviderInfo(integration.provider);
                        return (
                            <div key={integration.id} className="bg-white rounded-lg shadow-md p-6">
                                {/* Header */}
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
                                            {integration.is_active ? (
                                                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                                    Active
                                                </span>
                                            ) : (
                                                <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                                                    Inactive
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-600">{providerInfo?.name || integration.provider}</p>
                                    </div>
                                    <button
                                        onClick={() => handleDelete(integration.id)}
                                        className="text-red-600 hover:text-red-700 p-2"
                                        title="Delete integration"
                                        aria-label="Delete integration"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Stats */}
                                <div className="grid grid-cols-3 gap-4 mb-4 py-4 border-y border-gray-200">
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1">Total Syncs</p>
                                        <p className="text-lg font-semibold text-gray-900">{integration.total_syncs}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1">Success</p>
                                        <p className="text-lg font-semibold text-green-600">{integration.successful_syncs}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1">Failed</p>
                                        <p className="text-lg font-semibold text-red-600">{integration.failed_syncs}</p>
                                    </div>
                                </div>

                                {/* Details */}
                                <div className="space-y-2 mb-4">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-600">Direction:</span>
                                        <span className="font-medium text-gray-900 capitalize">{integration.sync_direction}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-600">Auto-sync:</span>
                                        <span className="font-medium text-gray-900">
                                            {integration.auto_sync ? `Every ${integration.sync_frequency_minutes} min` : 'Manual'}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-600">Entities:</span>
                                        <span className="font-medium text-gray-900">
                                            {integration.sync_entities?.join(', ') || 'None'}
                                        </span>
                                    </div>
                                    {integration.last_sync_at && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-gray-600">Last sync:</span>
                                            <span className="font-medium text-gray-900">
                                                {new Date(integration.last_sync_at).toLocaleString()}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => handleSync(integration.id)}
                                        disabled={!integration.is_active}
                                        className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Play className="w-4 h-4" />
                                        Sync Now
                                    </button>
                                    <button
                                        onClick={() => toast.info('Sync logs viewer coming soon')}
                                        className="flex-1 flex items-center justify-center gap-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
                                    >
                                        View Logs
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Info Panel */}
            <div className="mt-8 bg-blue-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">Supported Providers</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {providers.map((provider) => (
                        <div key={provider.id} className="bg-white rounded p-3">
                            <p className="font-medium text-sm text-gray-900">{provider.name}</p>
                            <p className="text-xs text-gray-500 mt-1">
                                {provider.requires_oauth ? 'OAuth2' : 'Direct'}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default BillingIntegrationPage;
