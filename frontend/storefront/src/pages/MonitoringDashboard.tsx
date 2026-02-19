import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Activity, Database, Search, Zap, RefreshCw } from 'lucide-react'
import { api } from '../lib/api'

export default function MonitoringDashboard() {
    const [countdown, setCountdown] = useState(5)

    const { data: redisHealth, dataUpdatedAt: rhUpdated } = useQuery({
        queryKey: ['redis-health'],
        queryFn: () => api.get('/monitoring/redis/health').then(res => res.data.data),
        refetchInterval: 5000,
    })

    const { data: redisStats } = useQuery<any>({
        queryKey: ['redis-stats'],
        queryFn: () => api.get('/monitoring/redis/stats').then(res => res.data.data),
        refetchInterval: 10000,
    })

    const { data: cachePerf } = useQuery({
        queryKey: ['cache-perf'],
        queryFn: () => api.get('/monitoring/redis/cache-performance').then(res => res.data.data),
        refetchInterval: 10000,
    })

    const { data: searchAnalytics } = useQuery({
        queryKey: ['search-analytics'],
        queryFn: () => api.get('/search/analytics').then(res => res.data.data),
        refetchInterval: 30000,
    })

    const { data: metricsData } = useQuery({
        queryKey: ['metrics-summary'],
        queryFn: () => api.get('/metrics/summary').then(res => res.data.data),
        refetchInterval: 5000,
    })

    // Countdown to next key refresh (5 second cycle matches redis health)
    useEffect(() => {
        setCountdown(5)
        const t = setInterval(() => setCountdown(c => c <= 1 ? 5 : c - 1), 1000)
        return () => clearInterval(t)
    }, [rhUpdated])

    const hitRate = cachePerf?.hit_rate_percent ?? 0
    const hitRateColor = hitRate >= 80 ? 'text-green-600' : hitRate >= 50 ? 'text-yellow-600' : 'text-red-600'
    const hitRateBg = hitRate >= 80 ? 'bg-green-500' : hitRate >= 50 ? 'bg-yellow-500' : 'bg-red-500'

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-text-primary">System Monitoring Dashboard</h1>
                        <p className="text-text-secondary mt-2 flex items-center gap-2">
                            Real-time performance and health metrics
                            <span className="inline-flex items-center gap-1.5 text-xs text-text-tertiary bg-bg-tertiary rounded-full px-2.5 py-0.5 border border-border-color">
                                <RefreshCw className="h-3 w-3 animate-spin" style={{ animationDuration: '4s' }} />
                                Next refresh in {countdown}s
                            </span>
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`flex items-center gap-1.5 text-sm font-semibold px-3 py-1.5 rounded-full border ${redisHealth?.connected
                                ? 'bg-green-500/10 text-green-600 border-green-500/20'
                                : 'bg-red-500/10 text-red-600 border-red-500/20'
                            }`}>
                            <span className={`h-2 w-2 rounded-full ${redisHealth?.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                                }`} />
                            {redisHealth?.connected ? 'All Systems Operational' : 'Service Degraded'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Redis Status</CardTitle>
                        <Activity className={`h-4 w-4 ${redisHealth?.connected ? 'text-green-600' : 'text-red-600'}`} />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {redisHealth?.connected ? (
                                <span className="text-green-600">Healthy</span>
                            ) : (
                                <span className="text-red-600">Down</span>
                            )}
                        </div>
                        <p className="text-xs text-text-tertiary">
                            {redisHealth?.latency_ms ? `${redisHealth.latency_ms.toFixed(2)}ms latency` : 'No data'}
                        </p>
                        <div className={`mt-2 inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${redisHealth?.connected ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'
                            }`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${redisHealth?.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                            {redisHealth?.connected ? 'Connected' : 'Disconnected'}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
                        <Zap className={`h-4 w-4 ${hitRateColor}`} />
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${hitRateColor}`}>
                            {hitRate.toFixed(1)}%
                        </div>
                        <p className="text-xs text-text-tertiary mb-2">
                            {cachePerf?.total_requests || 0} total requests
                        </p>
                        <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                            <style dangerouslySetInnerHTML={{ __html: `.hr-bar{width:${Math.min(100, hitRate).toFixed(1)}%}` }} />
                            <div className={`hr-bar h-full rounded-full transition-all duration-500 ${hitRateBg}`} />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Searches</CardTitle>
                        <Search className="h-4 w-4 text-purple-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-purple-600">
                            {searchAnalytics?.total_searches || 0}
                        </div>
                        <p className="text-xs text-text-tertiary">
                            {searchAnalytics?.unique_queries || 0} unique queries
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                        <Database className="h-4 w-4 text-orange-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-orange-600">
                            {redisStats?.used_memory || 'N/A'}
                        </div>
                        <p className="text-xs text-text-tertiary">
                            Version {redisStats?.version || 'Unknown'}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Cache Performance */}
                <Card>
                    <CardHeader>
                        <CardTitle>Cache Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {cachePerf ? (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Hits</span>
                                    <span className="font-semibold text-green-500">{cachePerf.hits}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Misses</span>
                                    <span className="font-semibold text-red-500">{cachePerf.misses}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Miss Rate</span>
                                    <span className="font-semibold text-text-primary">{cachePerf.miss_rate_percent?.toFixed(2)}%</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Evicted Keys</span>
                                    <span className="font-semibold text-text-primary">{cachePerf.evicted_keys || 0}</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-text-tertiary">Loading...</p>
                        )}
                    </CardContent>
                </Card>

                {/* Popular Searches */}
                <Card>
                    <CardHeader>
                        <CardTitle>Popular Searches</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {searchAnalytics?.top_queries?.length > 0 ? (
                            <div className="space-y-3">
                                {(() => {
                                    const maxCount = Math.max(...searchAnalytics.top_queries.slice(0, 5).map((i: any) => i.count), 1)
                                    return searchAnalytics.top_queries.slice(0, 5).map((item: any, idx: number) => (
                                        <div key={idx}>
                                            <div className="flex justify-between items-center mb-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-bold text-text-tertiary w-4">#{idx + 1}</span>
                                                    <span className="text-sm text-text-primary">{item.query}</span>
                                                </div>
                                                <span className="badge bg-theme-primary/10 text-theme-primary">{item.count}</span>
                                            </div>
                                            <div className="h-1 bg-bg-tertiary rounded-full overflow-hidden">
                                                <style dangerouslySetInnerHTML={{ __html: `.sq-${idx}{width:${((item.count / maxCount) * 100).toFixed(1)}%}` }} />
                                                <div className={`sq-${idx} h-full rounded-full bg-theme-primary/60`} />
                                            </div>
                                        </div>
                                    ))
                                })()}
                            </div>
                        ) : (
                            <p className="text-text-tertiary">No search data yet</p>
                        )}
                    </CardContent>
                </Card>

                {/* System Info */}
                <Card>
                    <CardHeader>
                        <CardTitle>System Information</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {metricsData ? (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Uptime</span>
                                    <span className="font-semibold text-text-primary">
                                        {Math.floor((metricsData.uptime_seconds || 0) / 3600)}h
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Total Requests</span>
                                    <span className="font-semibold text-text-primary">{metricsData.total_requests || 0}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Avg Response Time</span>
                                    <span className="font-semibold text-text-primary">
                                        {metricsData.avg_response_time?.toFixed(2) || 0}ms
                                    </span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-text-tertiary">Loading...</p>
                        )}
                    </CardContent>
                </Card>

                {/* Redis Server Stats */}
                <Card>
                    <CardHeader>
                        <CardTitle>Redis Server</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {redisStats ? (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Connected Clients</span>
                                    <span className="font-semibold text-text-primary">{redisStats.connected_clients}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Commands Processed</span>
                                    <span className="font-semibold text-text-primary">{redisStats.total_commands_processed}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Ops/sec</span>
                                    <span className="font-semibold text-text-primary">{redisStats.instantaneous_ops_per_sec}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-text-secondary">Peak Memory</span>
                                    <span className="font-semibold text-text-primary">{redisStats.used_memory_peak}</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-text-tertiary">Loading...</p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
