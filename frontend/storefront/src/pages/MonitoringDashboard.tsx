import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Activity, Database, Search, Zap } from 'lucide-react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

export default function MonitoringDashboard() {
    const { data: redisHealth } = useQuery({
        queryKey: ['redis-health'],
        queryFn: () => axios.get(`${API_BASE}/monitoring/redis/health`).then(res => res.data.data),
        refetchInterval: 5000,
    })

    const { data: redisStats } = useQuery({
        queryKey: ['redis-stats'],
        queryFn: () => axios.get(`${API_BASE}/monitoring/redis/stats`).then(res => res.data.data),
        refetchInterval: 10000,
    })

    const { data: cachePerf } = useQuery({
        queryKey: ['cache-perf'],
        queryFn: () => axios.get(`${API_BASE}/monitoring/redis/cache-performance`).then(res => res.data.data),
        refetchInterval: 10000,
    })

    const { data: searchAnalytics } = useQuery({
        queryKey: ['search-analytics'],
        queryFn: () => axios.get(`${API_BASE}/search/analytics`).then(res => res.data.data),
        refetchInterval: 30000,
    })

    const { data: metricsData } = useQuery({
        queryKey: ['metrics-summary'],
        queryFn: () => axios.get(`${API_BASE}/metrics/summary`).then(res => res.data.data),
        refetchInterval: 5000,
    })

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">System Monitoring Dashboard</h1>
                <p className="text-gray-600 mt-2">Real-time performance and health metrics</p>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Redis Status</CardTitle>
                        <Activity className="h-4 w-4 text-green-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {redisHealth?.connected ? (
                                <span className="text-green-600">Healthy</span>
                            ) : (
                                <span className="text-red-600">Down</span>
                            )}
                        </div>
                        <p className="text-xs text-gray-600">
                            {redisHealth?.latency_ms ? `${redisHealth.latency_ms.toFixed(2)}ms latency` : 'No data'}
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
                        <Zap className="h-4 w-4 text-blue-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-600">
                            {cachePerf?.hit_rate_percent?.toFixed(1) || '0'}%
                        </div>
                        <p className="text-xs text-gray-600">
                            {cachePerf?.total_requests || 0} total requests
                        </p>
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
                        <p className="text-xs text-gray-600">
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
                        <p className="text-xs text-gray-600">
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
                                    <span className="text-sm text-gray-600">Hits</span>
                                    <span className="font-semibold text-green-600">{cachePerf.hits}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Misses</span>
                                    <span className="font-semibold text-red-600">{cachePerf.misses}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Miss Rate</span>
                                    <span className="font-semibold">{cachePerf.miss_rate_percent?.toFixed(2)}%</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Evicted Keys</span>
                                    <span className="font-semibold">{cachePerf.evicted_keys || 0}</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-400">Loading...</p>
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
                                {searchAnalytics.top_queries.slice(0, 5).map((item: any, idx: number) => (
                                    <div key={idx} className="flex justify-between items-center">
                                        <span className="text-sm text-gray-700">{item.query}</span>
                                        <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                                            {item.count}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-400">No search data yet</p>
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
                                    <span className="text-sm text-gray-600">Uptime</span>
                                    <span className="font-semibold">
                                        {Math.floor((metricsData.uptime_seconds || 0) / 3600)}h
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Total Requests</span>
                                    <span className="font-semibold">{metricsData.total_requests || 0}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Avg Response Time</span>
                                    <span className="font-semibold">
                                        {metricsData.avg_response_time?.toFixed(2) || 0}ms
                                    </span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-400">Loading...</p>
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
                                    <span className="text-sm text-gray-600">Connected Clients</span>
                                    <span className="font-semibold">{redisStats.connected_clients}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Commands Processed</span>
                                    <span className="font-semibold">{redisStats.total_commands_processed}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Ops/sec</span>
                                    <span className="font-semibold">{redisStats.instantaneous_ops_per_sec}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600">Peak Memory</span>
                                    <span className="font-semibold">{redisStats.used_memory_peak}</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-400">Loading...</p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
