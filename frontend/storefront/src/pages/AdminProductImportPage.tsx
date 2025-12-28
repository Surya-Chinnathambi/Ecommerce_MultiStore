import { useState } from 'react'
import { Upload, Download, AlertCircle, RefreshCw, XCircle } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface ImportResult {
    total_rows: number
    processed: number
    succeeded: number
    failed: number
    skipped: number
    errors: Array<{ row: number; error: string }>
    updated_count: number
    created_count: number
}

export default function AdminProductImportPage() {
    const [file, setFile] = useState<File | null>(null)
    const [importing, setImporting] = useState(false)
    const [importResult, setImportResult] = useState<ImportResult | null>(null)
    const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
    const [showMapping, setShowMapping] = useState(false)
    const [csvHeaders, setCsvHeaders] = useState<string[]>([])

    const productFields = [
        { key: 'name', label: 'Product Name', required: true },
        { key: 'sku', label: 'SKU/Product Code', required: false },
        { key: 'price', label: 'Selling Price', required: true },
        { key: 'cost', label: 'Cost Price', required: false },
        { key: 'quantity', label: 'Stock Quantity', required: true },
        { key: 'category', label: 'Category', required: false },
        { key: 'description', label: 'Description', required: false },
        { key: 'brand', label: 'Brand', required: false },
        { key: 'barcode', label: 'Barcode', required: false },
    ]

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0]
        if (selectedFile) {
            if (!selectedFile.name.endsWith('.csv')) {
                toast.error('Please select a CSV file')
                return
            }
            setFile(selectedFile)
            setImportResult(null)

            // Read CSV headers
            const reader = new FileReader()
            reader.onload = (e) => {
                const text = e.target?.result as string
                const firstLine = text.split('\n')[0]
                const headers = firstLine.split(',').map(h => h.trim())
                setCsvHeaders(headers)

                // Auto-map columns
                const autoMapping: Record<string, string> = {}
                headers.forEach(header => {
                    const lowerHeader = header.toLowerCase()
                    if (lowerHeader.includes('name') || lowerHeader === 'product') {
                        autoMapping['name'] = header
                    } else if (lowerHeader.includes('sku') || lowerHeader.includes('code')) {
                        autoMapping['sku'] = header
                    } else if (lowerHeader.includes('price') && !lowerHeader.includes('cost')) {
                        autoMapping['price'] = header
                    } else if (lowerHeader.includes('cost')) {
                        autoMapping['cost'] = header
                    } else if (lowerHeader.includes('quantity') || lowerHeader.includes('stock') || lowerHeader.includes('qty')) {
                        autoMapping['quantity'] = header
                    } else if (lowerHeader.includes('category')) {
                        autoMapping['category'] = header
                    } else if (lowerHeader.includes('description') || lowerHeader.includes('desc')) {
                        autoMapping['description'] = header
                    } else if (lowerHeader.includes('brand')) {
                        autoMapping['brand'] = header
                    } else if (lowerHeader.includes('barcode')) {
                        autoMapping['barcode'] = header
                    }
                })
                setColumnMapping(autoMapping)
            }
            reader.readAsText(selectedFile)
        }
    }

    const handleImport = async () => {
        if (!file) {
            toast.error('Please select a file')
            return
        }

        setImporting(true)
        const formData = new FormData()
        formData.append('file', file)
        formData.append('update_existing', 'true')
        formData.append('column_mapping', JSON.stringify(columnMapping))

        try {
            const token = useAuthStore.getState().token
            const response = await axios.post(
                `${API_BASE_URL}/billing/import/csv`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        Authorization: `Bearer ${token}`,
                    },
                    params: {
                        entity_type: 'products',
                    },
                }
            )

            setImportResult(response.data.data)

            if (response.data.data.succeeded > 0) {
                toast.success(`Successfully imported ${response.data.data.succeeded} products`)
            }

            if (response.data.data.failed > 0) {
                toast.error(`Failed to import ${response.data.data.failed} products`)
            }
        } catch (error: any) {
            console.error('Import error:', error)
            toast.error(error.response?.data?.detail || 'Failed to import products')
        } finally {
            setImporting(false)
        }
    }

    const downloadTemplate = () => {
        const headers = ['name', 'sku', 'price', 'cost', 'quantity', 'category', 'description', 'brand', 'barcode']
        const sampleData = [
            ['Sample Product', 'SKU001', '999.99', '500.00', '100', 'Electronics', 'Product description', 'Brand Name', '1234567890123']
        ]

        const csvContent = [
            headers.join(','),
            ...sampleData.map(row => row.join(','))
        ].join('\n')

        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'product_import_template.csv'
        a.click()
        window.URL.revokeObjectURL(url)
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Product Import from Billing Software</h1>
                    <p className="text-gray-600">
                        Import or update products from your billing software using CSV files
                    </p>
                </div>

                {/* Instructions Card */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
                    <h2 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        How to Import Products
                    </h2>
                    <ol className="list-decimal list-inside space-y-2 text-blue-800">
                        <li>Export products from your billing software as CSV</li>
                        <li>Or download our template and fill in your product data</li>
                        <li>Upload the CSV file below</li>
                        <li>Map CSV columns to product fields (auto-detected)</li>
                        <li>Review and confirm the import</li>
                    </ol>
                    <div className="mt-4">
                        <button
                            onClick={downloadTemplate}
                            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
                        >
                            <Download className="h-4 w-4" />
                            Download CSV Template
                        </button>
                    </div>
                </div>

                {/* File Upload Section */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-4">Upload CSV File</h2>

                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileSelect}
                            className="hidden"
                            id="csv-upload"
                        />
                        <label
                            htmlFor="csv-upload"
                            className="cursor-pointer flex flex-col items-center gap-4"
                        >
                            <Upload className="h-12 w-12 text-gray-400" />
                            {file ? (
                                <div className="text-center">
                                    <p className="font-medium text-gray-900">{file.name}</p>
                                    <p className="text-sm text-gray-500 mt-1">
                                        {(file.size / 1024).toFixed(2)} KB
                                    </p>
                                </div>
                            ) : (
                                <div>
                                    <p className="text-gray-600 mb-1">
                                        Click to upload or drag and drop
                                    </p>
                                    <p className="text-sm text-gray-500">CSV files only</p>
                                </div>
                            )}
                        </label>
                    </div>
                </div>

                {/* Column Mapping Section */}
                {file && csvHeaders.length > 0 && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-semibold">Column Mapping</h2>
                            <button
                                onClick={() => setShowMapping(!showMapping)}
                                className="text-purple-600 hover:text-purple-700 text-sm font-medium"
                            >
                                {showMapping ? 'Hide' : 'Show'} Mapping
                            </button>
                        </div>

                        {showMapping && (
                            <div className="space-y-4">
                                {productFields.map(field => (
                                    <div key={field.key} className="flex items-center gap-4">
                                        <label className="w-1/3 text-sm font-medium text-gray-700">
                                            {field.label}
                                            {field.required && (
                                                <span className="text-red-500 ml-1">*</span>
                                            )}
                                        </label>
                                        <select
                                            value={columnMapping[field.key] || ''}
                                            onChange={(e) =>
                                                setColumnMapping(prev => ({
                                                    ...prev,
                                                    [field.key]: e.target.value,
                                                }))
                                            }
                                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                            aria-label={`Map ${field.label} column`}
                                        >
                                            <option value="">-- Not Mapped --</option>
                                            {csvHeaders.map(header => (
                                                <option key={header} value={header}>
                                                    {header}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-600">
                                <strong>Auto-detected mappings:</strong> {Object.keys(columnMapping).length} fields mapped
                            </p>
                        </div>
                    </div>
                )}

                {/* Import Button */}
                {file && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-gray-900">Ready to Import</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                    Existing products will be updated, new products will be created
                                </p>
                            </div>
                            <button
                                onClick={handleImport}
                                disabled={importing}
                                className="flex items-center gap-2 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                            >
                                {importing ? (
                                    <>
                                        <RefreshCw className="h-5 w-5 animate-spin" />
                                        Importing...
                                    </>
                                ) : (
                                    <>
                                        <Upload className="h-5 w-5" />
                                        Import Products
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                )}

                {/* Import Results */}
                {importResult && (
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-semibold mb-4">Import Results</h2>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="text-center p-4 bg-gray-50 rounded-lg">
                                <p className="text-2xl font-bold text-gray-900">
                                    {importResult.total_rows}
                                </p>
                                <p className="text-sm text-gray-600">Total Rows</p>
                            </div>
                            <div className="text-center p-4 bg-green-50 rounded-lg">
                                <p className="text-2xl font-bold text-green-600">
                                    {importResult.succeeded}
                                </p>
                                <p className="text-sm text-gray-600">Succeeded</p>
                            </div>
                            <div className="text-center p-4 bg-red-50 rounded-lg">
                                <p className="text-2xl font-bold text-red-600">
                                    {importResult.failed}
                                </p>
                                <p className="text-sm text-gray-600">Failed</p>
                            </div>
                            <div className="text-center p-4 bg-yellow-50 rounded-lg">
                                <p className="text-2xl font-bold text-yellow-600">
                                    {importResult.skipped}
                                </p>
                                <p className="text-sm text-gray-600">Skipped</p>
                            </div>
                        </div>

                        <div className="flex gap-4 mb-6">
                            <div className="flex-1 p-4 bg-blue-50 rounded-lg">
                                <p className="text-sm text-gray-600">Created</p>
                                <p className="text-xl font-bold text-blue-600">
                                    {importResult.created_count}
                                </p>
                            </div>
                            <div className="flex-1 p-4 bg-purple-50 rounded-lg">
                                <p className="text-sm text-gray-600">Updated</p>
                                <p className="text-xl font-bold text-purple-600">
                                    {importResult.updated_count}
                                </p>
                            </div>
                        </div>

                        {importResult.errors && importResult.errors.length > 0 && (
                            <div>
                                <h3 className="font-semibold text-red-600 mb-3 flex items-center gap-2">
                                    <XCircle className="h-5 w-5" />
                                    Errors ({importResult.errors.length})
                                </h3>
                                <div className="max-h-64 overflow-y-auto space-y-2">
                                    {importResult.errors.map((error, idx) => (
                                        <div
                                            key={idx}
                                            className="p-3 bg-red-50 border border-red-200 rounded text-sm"
                                        >
                                            <span className="font-medium">Row {error.row}:</span>{' '}
                                            {error.error}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
