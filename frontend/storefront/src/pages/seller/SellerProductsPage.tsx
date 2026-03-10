import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { sellerApi } from '@/lib/api'
import { Package, Plus, Edit3 } from 'lucide-react'
import { toast } from '@/components/ui/Toaster'
import DataGrid from '@/components/ui/DataGrid'
import PaginationControls from '@/components/ui/PaginationControls'
import EmptyState from '@/components/ui/EmptyState'
import RowActions, { RowActionButton } from '@/components/ui/RowActions'

export default function SellerProductsPage() {
    const qc = useQueryClient()
    const [page, setPage] = useState(1)
    const [showForm, setShowForm] = useState(false)
    const [editId, setEditId] = useState<string | null>(null)
    const [form, setForm] = useState({ product_id: '', price: '', stock: '', dispatch_days: '2', return_days: '7' })
    const [saving, setSaving] = useState(false)

    const { data, isLoading } = useQuery({
        queryKey: ['seller-products', page],
        queryFn: () => sellerApi.getProducts(page).then((r) => r.data),
    })

    const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

    const handleSave = async () => {
        if (!form.product_id || !form.price || !form.stock) {
            toast.error('Product ID, price and stock are required')
            return
        }
        setSaving(true)
        try {
            if (editId) {
                await sellerApi.updateProduct(editId, {
                    price: parseFloat(form.price),
                    stock: parseInt(form.stock),
                    dispatch_days: parseInt(form.dispatch_days),
                    return_days: parseInt(form.return_days),
                })
                toast.success('Listing updated')
            } else {
                await sellerApi.listProduct({
                    product_id: form.product_id,
                    price: parseFloat(form.price),
                    stock: parseInt(form.stock),
                    dispatch_days: parseInt(form.dispatch_days),
                    return_days: parseInt(form.return_days),
                })
                toast.success('Product listed')
            }
            qc.invalidateQueries({ queryKey: ['seller-products'] })
            setShowForm(false)
            setEditId(null)
            setForm({ product_id: '', price: '', stock: '', dispatch_days: '2', return_days: '7' })
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Failed to save')
        } finally {
            setSaving(false)
        }
    }

    const products: any[] = data?.data ?? []
    const total: number = data?.meta?.total ?? 0
    const totalPages = Math.max(1, Math.ceil(total / 20))

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h1 className="text-2xl font-bold text-text-primary">My Listings</h1>
                    <button
                        onClick={() => { setShowForm(!showForm); setEditId(null) }}
                        className="btn btn-primary"
                    >
                        <Plus className="h-4 w-4" />
                        List New Product
                    </button>
                </div>

                {/* Add/Edit Form */}
                {showForm && (
                    <div className="card p-6 mb-6">
                        <h2 className="text-lg font-bold text-text-primary mb-4">
                            {editId ? 'Update Listing' : 'List New Product'}
                        </h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            {!editId && (
                                <div className="col-span-2 md:col-span-3">
                                    <label className="label">Product ID *</label>
                                    <input className="input" value={form.product_id}
                                        onChange={(e) => set('product_id', e.target.value)}
                                        placeholder="UUID of the product from catalog" />
                                </div>
                            )}
                            <div>
                                <label className="label">Your Price (₹) *</label>
                                <input className="input" title="Price" type="number" min="0" step="0.01" placeholder="0"
                                    value={form.price} onChange={(e) => set('price', e.target.value)} />
                            </div>
                            <div>
                                <label className="label">Stock *</label>
                                <input className="input" title="Stock quantity" type="number" min="0" placeholder="0"
                                    value={form.stock} onChange={(e) => set('stock', e.target.value)} />
                            </div>
                            <div>
                                <label className="label">Dispatch Days</label>
                                <input className="input" title="Dispatch days" type="number" min="1" max="7" placeholder="2"
                                    value={form.dispatch_days} onChange={(e) => set('dispatch_days', e.target.value)} />
                            </div>
                            <div>
                                <label className="label">Return Days</label>
                                <select title="Return days" className="input" value={form.return_days}
                                    onChange={(e) => set('return_days', e.target.value)}>
                                    {[0, 7, 10, 15, 30].map((d) => (
                                        <option key={d} value={d}>{d === 0 ? 'No Returns' : `${d} days`}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-4">
                            <button onClick={() => setShowForm(false)} className="btn btn-ghost">Cancel</button>
                            <button onClick={handleSave} disabled={saving} className="btn btn-primary">
                                {saving ? 'Saving...' : (editId ? 'Update' : 'List Product')}
                            </button>
                        </div>
                    </div>
                )}

                {/* Product list */}
                {isLoading ? (
                    <div className="space-y-3">
                        {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
                    </div>
                ) : products.length === 0 ? (
                    <EmptyState
                        icon={<Package className="h-12 w-12" />}
                        title="No listings yet"
                        description="List your first product to start selling."
                    />
                ) : (
                    <DataGrid
                        className="card overflow-hidden"
                        footer={
                            <PaginationControls
                                page={page}
                                totalPages={totalPages}
                                onPrev={() => setPage(p => Math.max(1, p - 1))}
                                onNext={() => setPage(p => Math.min(totalPages, p + 1))}
                            />
                        }
                    >
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border-color bg-bg-tertiary/30">
                                    <th className="text-left px-4 py-3 font-semibold text-text-secondary">Product</th>
                                    <th className="text-right px-4 py-3 font-semibold text-text-secondary">Price</th>
                                    <th className="text-right px-4 py-3 font-semibold text-text-secondary">Stock</th>
                                    <th className="text-right px-4 py-3 font-semibold text-text-secondary">Dispatch</th>
                                    <th className="text-right px-4 py-3 font-semibold text-text-secondary">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products.map((p: any) => (
                                    <tr key={p.id} className="border-b border-border-color last:border-0 hover:bg-bg-tertiary/20 transition-colors">
                                        <td className="px-4 py-3">
                                            <p className="font-medium text-text-primary">{p.product_id}</p>
                                            <p className="text-xs text-text-tertiary">Returns: {p.return_days}d</p>
                                        </td>
                                        <td className="px-4 py-3 text-right font-semibold text-text-primary">
                                            ₹{p.price?.toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <span className={`font-medium ${p.stock === 0 ? 'text-red-500' : p.stock < 10 ? 'text-orange-500' : 'text-green-600'}`}>
                                                {p.stock}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right text-text-secondary">
                                            {p.dispatch_days}d
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <RowActions>
                                                <RowActionButton
                                                    aria-label="Edit listing"
                                                    title="Edit listing"
                                                    tone="primary"
                                                    iconOnly
                                                    icon={<Edit3 className="h-4 w-4" />}
                                                    onClick={() => {
                                                        setEditId(p.id)
                                                        setForm({
                                                            product_id: p.product_id,
                                                            price: String(p.price),
                                                            stock: String(p.stock),
                                                            dispatch_days: String(p.dispatch_days),
                                                            return_days: String(p.return_days),
                                                        })
                                                        setShowForm(true)
                                                    }}
                                                />
                                            </RowActions>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </DataGrid>
                )}
            </div>
        </div>
    )
}
