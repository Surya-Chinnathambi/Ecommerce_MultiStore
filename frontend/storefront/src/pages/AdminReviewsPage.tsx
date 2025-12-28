import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Star, CheckCircle, XCircle, Trash2, MessageSquare, Search } from 'lucide-react'
import api from '@/lib/api'
import { toast } from '@/components/ui/Toaster'

interface Review {
    id: string
    product_id: string
    user_id: string
    user_name: string
    rating: number
    title: string
    review_text: string
    is_verified_purchase: boolean
    is_approved: boolean
    is_featured: boolean
    helpful_count: number
    not_helpful_count: number
    created_at: string
    responses: Array<{
        id: string
        responder_name: string
        response_text: string
        created_at: string
    }>
}

export default function AdminReviewsPage() {
    const queryClient = useQueryClient()
    const [filterStatus, setFilterStatus] = useState<'all' | 'approved' | 'pending'>('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedReview, setSelectedReview] = useState<Review | null>(null)
    const [responseText, setResponseText] = useState('')
    const [responderName, setResponderName] = useState('Store Manager')

    // Fetch all reviews
    const { data: reviewsData, isLoading } = useQuery({
        queryKey: ['admin-reviews', filterStatus, searchQuery],
        queryFn: async () => {
            const params: any = {}
            if (filterStatus === 'approved') params.is_approved = true
            if (filterStatus === 'pending') params.is_approved = false
            if (searchQuery) params.search = searchQuery

            const response = await api.get('/reviews/', { params })
            return response.data.data as Review[]
        },
    })

    // Approve/Reject review
    const toggleApprovalMutation = useMutation({
        mutationFn: async ({ reviewId, isApproved }: { reviewId: string; isApproved: boolean }) => {
            const response = await api.put(`/reviews/${reviewId}`, { is_approved: isApproved })
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-reviews'] })
            toast.success('Review status updated')
        },
        onError: () => {
            toast.error('Failed to update review status')
        },
    })

    // Toggle featured status
    const toggleFeaturedMutation = useMutation({
        mutationFn: async ({ reviewId, isFeatured }: { reviewId: string; isFeatured: boolean }) => {
            const response = await api.put(`/reviews/${reviewId}`, { is_featured: isFeatured })
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-reviews'] })
            toast.success('Featured status updated')
        },
        onError: () => {
            toast.error('Failed to update featured status')
        },
    })

    // Delete review
    const deleteReviewMutation = useMutation({
        mutationFn: async (reviewId: string) => {
            const response = await api.delete(`/reviews/${reviewId}`)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-reviews'] })
            toast.success('Review deleted')
        },
        onError: () => {
            toast.error('Failed to delete review')
        },
    })

    // Submit store response
    const submitResponseMutation = useMutation({
        mutationFn: async ({ reviewId, responseData }: { reviewId: string; responseData: any }) => {
            const response = await api.post(`/reviews/${reviewId}/response`, responseData)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-reviews'] })
            setSelectedReview(null)
            setResponseText('')
            toast.success('Response posted')
        },
        onError: () => {
            toast.error('Failed to post response')
        },
    })

    const handleSubmitResponse = (reviewId: string) => {
        if (!responseText.trim()) {
            toast.error('Please enter a response')
            return
        }
        submitResponseMutation.mutate({
            reviewId,
            responseData: {
                response_text: responseText,
                responder_name: responderName,
            },
        })
    }

    const filteredReviews = reviewsData || []

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse space-y-4">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-32 bg-bg-tertiary rounded-lg" />
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-text-primary">Review Management</h1>
                <p className="text-text-secondary mt-2">Manage customer reviews, approve, feature, and respond</p>
            </div>

            {/* Filters */}
            <div className="bg-bg-primary rounded-lg shadow-md p-6 mb-6 border border-border-color">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Search */}
                    <div className="md:col-span-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                            <input
                                type="text"
                                placeholder="Search reviews..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                    </div>

                    {/* Status Filter */}
                    <div>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value as any)}
                            aria-label="Filter by review status"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="all">All Reviews</option>
                            <option value="approved">Approved</option>
                            <option value="pending">Pending Approval</option>
                        </select>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t">
                    <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">{filteredReviews.length}</p>
                        <p className="text-sm text-gray-600">Total Reviews</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                            {filteredReviews.filter((r) => r.is_approved).length}
                        </p>
                        <p className="text-sm text-gray-600">Approved</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-yellow-600">
                            {filteredReviews.filter((r) => !r.is_approved).length}
                        </p>
                        <p className="text-sm text-gray-600">Pending</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                            {filteredReviews.filter((r) => r.is_featured).length}
                        </p>
                        <p className="text-sm text-gray-600">Featured</p>
                    </div>
                </div>
            </div>

            {/* Reviews List */}
            <div className="space-y-4">
                {filteredReviews.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-md p-12 text-center">
                        <MessageSquare className="mx-auto h-16 w-16 text-gray-300 mb-4" />
                        <p className="text-xl text-gray-600">No reviews found</p>
                        <p className="text-gray-500 mt-2">Reviews will appear here once customers start reviewing products</p>
                    </div>
                ) : (
                    filteredReviews.map((review) => (
                        <div key={review.id} className="bg-white rounded-lg shadow-md p-6">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    {/* Rating & User */}
                                    <div className="flex items-center gap-4 mb-2">
                                        <div className="flex items-center">
                                            {[...Array(5)].map((_, i) => (
                                                <Star
                                                    key={i}
                                                    size={16}
                                                    className={
                                                        i < review.rating
                                                            ? 'fill-yellow-400 text-yellow-400'
                                                            : 'text-gray-300'
                                                    }
                                                />
                                            ))}
                                        </div>
                                        <span className="font-semibold text-gray-900">{review.user_name}</span>
                                        {review.is_verified_purchase && (
                                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                                                Verified Purchase
                                            </span>
                                        )}
                                        {review.is_featured && (
                                            <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded">
                                                Featured
                                            </span>
                                        )}
                                    </div>

                                    {/* Review Content */}
                                    {review.title && <h3 className="font-semibold text-lg mb-2">{review.title}</h3>}
                                    {review.review_text && <p className="text-gray-700 mb-3">{review.review_text}</p>}

                                    {/* Metadata */}
                                    <div className="flex items-center gap-4 text-sm text-gray-500">
                                        <span>{new Date(review.created_at).toLocaleDateString()}</span>
                                        <span>👍 {review.helpful_count}</span>
                                        <span>👎 {review.not_helpful_count}</span>
                                    </div>

                                    {/* Store Responses */}
                                    {review.responses && review.responses.length > 0 && (
                                        <div className="mt-4 pl-4 border-l-4 border-purple-200 bg-purple-50 p-4 rounded">
                                            {review.responses.map((response) => (
                                                <div key={response.id}>
                                                    <p className="font-semibold text-purple-700">
                                                        {response.responder_name}
                                                    </p>
                                                    <p className="text-gray-700 mt-1">{response.response_text}</p>
                                                    <p className="text-xs text-gray-500 mt-2">
                                                        {new Date(response.created_at).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="flex flex-col gap-2 ml-4">
                                    {/* Approve/Reject */}
                                    <button
                                        onClick={() =>
                                            toggleApprovalMutation.mutate({
                                                reviewId: review.id,
                                                isApproved: !review.is_approved,
                                            })
                                        }
                                        aria-label={review.is_approved ? 'Reject review' : 'Approve review'}
                                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${review.is_approved
                                            ? 'bg-green-100 text-green-700 hover:bg-green-200'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                    >
                                        {review.is_approved ? (
                                            <CheckCircle size={20} />
                                        ) : (
                                            <XCircle size={20} />
                                        )}
                                    </button>

                                    {/* Toggle Featured */}
                                    <button
                                        onClick={() =>
                                            toggleFeaturedMutation.mutate({
                                                reviewId: review.id,
                                                isFeatured: !review.is_featured,
                                            })
                                        }
                                        aria-label="Toggle featured status"
                                        className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
                                    >
                                        <Star size={20} className={review.is_featured ? 'fill-purple-700' : ''} />
                                    </button>

                                    {/* Respond */}
                                    <button
                                        onClick={() => setSelectedReview(review)}
                                        aria-label="Respond to review"
                                        className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                                    >
                                        <MessageSquare size={20} />
                                    </button>

                                    {/* Delete */}
                                    <button
                                        onClick={() => {
                                            if (window.confirm('Are you sure you want to delete this review?')) {
                                                deleteReviewMutation.mutate(review.id)
                                            }
                                        }}
                                        aria-label="Delete review"
                                        className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                                    >
                                        <Trash2 size={20} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Response Modal */}
            {selectedReview && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-2xl w-full p-6">
                        <h2 className="text-2xl font-bold mb-4">Respond to Review</h2>

                        <div className="bg-gray-50 p-4 rounded-lg mb-4">
                            <div className="flex items-center gap-2 mb-2">
                                {[...Array(5)].map((_, i) => (
                                    <Star
                                        key={i}
                                        size={16}
                                        className={
                                            i < selectedReview.rating
                                                ? 'fill-yellow-400 text-yellow-400'
                                                : 'text-gray-300'
                                        }
                                    />
                                ))}
                                <span className="font-semibold">{selectedReview.user_name}</span>
                            </div>
                            {selectedReview.title && <h3 className="font-semibold mb-2">{selectedReview.title}</h3>}
                            <p className="text-gray-700">{selectedReview.review_text}</p>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-2">Your Name</label>
                            <input
                                type="text"
                                value={responderName}
                                onChange={(e) => setResponderName(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                placeholder="Store Manager"
                            />
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-2">Your Response</label>
                            <textarea
                                value={responseText}
                                onChange={(e) => setResponseText(e.target.value)}
                                rows={4}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                placeholder="Thank you for your review..."
                            />
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => handleSubmitResponse(selectedReview.id)}
                                disabled={submitResponseMutation.isPending}
                                className="flex-1 bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                            >
                                {submitResponseMutation.isPending ? 'Posting...' : 'Post Response'}
                            </button>
                            <button
                                onClick={() => {
                                    setSelectedReview(null)
                                    setResponseText('')
                                }}
                                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
