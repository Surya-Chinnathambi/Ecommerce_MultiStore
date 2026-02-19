import React, { useState, useEffect } from 'react';
import { Plus, RefreshCw, Download, Settings, Trash2, Play } from 'lucide-react';
import { billingApi, BillingIntegration, BillingProvider } from '../lib/billing-api';
import { toast } from '../components/ui/Toaster';

const BillingIntegrationPage: React.FC = () => {
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
                billingApi.listIntegrations(),
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
            await billingApi.syncIntegration(integrationId, {
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
            await billingApi.deleteIntegration(integrationId);
            toast.success('Integration deleted');
            loadData();
        } catch (error) {
            toast.error('Failed to delete integration');
        }
    };

    const handleExportCSV = async (entityType: 'invoice' | 'product' | 'customer') => {
        try {
            const result = await billingApi.exportToCSV(entityType);

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
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary"></div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-text-primary mb-2">Billing Integration</h1>
                <p className="text-text-secondary">Connect your e-commerce platform with billing software</p>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <button
                    onClick={() => toast.info('Create integration modal coming soon')}
                    className="btn btn-primary flex items-center justify-center gap-2 py-3"
                >
                    <Plus className="w-5 h-5" />
                    New Integration
                </button>
                <button
                    onClick={() => handleExportCSV('invoice')}
                    className="btn flex items-center justify-center gap-2 py-3 bg-green-500/10 text-green-500 hover:bg-green-500/20"
                >
                    <Download className="w-5 h-5" />
                    Export Invoices
                </button>
                <button
                    onClick={() => handleExportCSV('product')}
                    className="btn flex items-center justify-center gap-2 py-3 bg-theme-primary/10 text-theme-primary hover:bg-theme-primary/20"
                >
                    <Download className="w-5 h-5" />
                    Export Products
                </button>
                <button
                    onClick={loadData}
                    className="btn btn-secondary flex items-center justify-center gap-2 py-3"
                >
                    <RefreshCw className="w-5 h-5" />
                    Refresh
                </button>
            </div>

            {/* Integrations List */}
            {integrations.length === 0 ? (
                <div className="card p-12 text-center">
                    <div className="w-16 h-16 bg-theme-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Settings className="w-8 h-8 text-theme-primary" />
                    </div>
                    <h3 className="text-xl font-semibold text-text-primary mb-2">No Integrations Yet</h3>
                    <p className="text-text-secondary mb-6">Get started by creating your first billing integration</p>
                    <button
                        onClick={() => toast.info('Create integration modal coming soon')}
                        className="btn btn-primary inline-flex items-center gap-2 px-6 py-3"
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
                            <div key={integration.id} className="card">
                                {/* Header */}
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="text-lg font-semibold text-text-primary">{integration.name}</h3>
                                            {integration.is_active ? (
                                                <span className="badge bg-green-500/10 text-green-500">
                                                    Active
                                                </span>
                                            ) : (
                                                <span className="badge bg-bg-tertiary text-text-secondary">
                                                    Inactive
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-text-secondary">{providerInfo?.name || integration.provider}</p>
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
                                <div className="grid grid-cols-3 gap-4 mb-4 py-4 border-y border-border-color">
                                    <div>
                                        <p className="text-xs text-text-tertiary mb-1">Total Syncs</p>
                                        <p className="text-lg font-semibold text-text-primary">{integration.total_syncs}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-text-tertiary mb-1">Success</p>
                                        <p className="text-lg font-semibold text-green-500">{integration.successful_syncs}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-text-tertiary mb-1">Failed</p>
                                        <p className="text-lg font-semibold text-red-500">{integration.failed_syncs}</p>
                                    </div>
                                </div>

                                {/* Details */}
                                <div className="space-y-2 mb-4">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-text-secondary">Direction:</span>
                                        <span className="font-medium text-text-primary capitalize">{integration.sync_direction}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-text-secondary">Auto-sync:</span>
                                        <span className="font-medium text-text-primary">
                                            {integration.auto_sync ? `Every ${integration.sync_frequency_minutes} min` : 'Manual'}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-text-secondary">Entities:</span>
                                        <span className="font-medium text-text-primary">
                                            {integration.sync_entities?.join(', ') || 'None'}
                                        </span>
                                    </div>
                                    {integration.last_sync_at && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-text-secondary">Last sync:</span>
                                            <span className="font-medium text-text-primary">
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
                                        className="btn btn-primary flex-1 flex items-center justify-center gap-2 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Play className="w-4 h-4" />
                                        Sync Now
                                    </button>
                                    <button
                                        onClick={() => toast.info('Sync logs viewer coming soon')}
                                        className="btn btn-secondary flex-1 flex items-center justify-center gap-2 py-2"
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
            <div className="mt-8 rounded-lg p-6 bg-theme-primary/10 border border-border-color">
                <h3 className="text-lg font-semibold text-text-primary mb-2">Supported Providers</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {providers.map((provider) => (
                        <div key={provider.id} className="bg-bg-primary border border-border-color rounded p-3">
                            <p className="font-medium text-sm text-text-primary">{provider.name}</p>
                            <p className="text-xs text-text-tertiary mt-1">
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
