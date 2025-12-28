/* eslint-disable react/forbid-dom-props */
import { useState } from 'react'
import { Star } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'

interface Review {
    id: string
    rating: number
    title: string
    review_text: string
    user_name: string
    is_verified_purchase: boolean
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

interface ReviewStats {
    total_reviews: number
    average_rating: number
    rating_distribution: { [key: number]: number }
    verified_purchase_percentage: number
}

interface ProductReviewsProps {
    productId: string
}

export default function ProductReviews({ productId }: ProductReviewsProps) {
    const { isAuthenticated } = useAuthStore()
    const queryClient = useQueryClient()
    const [showReviewForm, setShowReviewForm] = useState(false)
    const [rating, setRating] = useState(5)
    const [title, setTitle] = useState('')
    const [reviewText, setReviewText] = useState('')
    const [filterRating, setFilterRating] = useState<number | null>(null)
    const [verifiedOnly, setVerifiedOnly] = useState(false)

    // Fetch reviews
    const { data: reviews, isLoading: reviewsLoading } = useQuery<Review[]>({
        queryKey: ['product-reviews', productId, filterRating, verifiedOnly],
        queryFn: async () => {
            const params = new URLSearchParams()
            if (filterRating) params.append('min_rating', filterRating.toString())
            if (verifiedOnly) params.append('verified_only', 'true')

            const response = await api.get(`/api/v1/reviews/product/${productId}?${params}`)
            return response.data
        },
    })

    // Fetch review stats
    const { data: stats } = useQuery<ReviewStats>({
        queryKey: ['review-stats', productId],
        queryFn: async () => {
            const response = await api.get(`/api/v1/reviews/product/${productId}/stats`)
            return response.data
        },
    })

    // Submit review
    const submitReviewMutation = useMutation({
        mutationFn: async (reviewData: any) => {
            const response = await api.post('/api/v1/reviews/', reviewData)
            return response.data
        },
        onSuccess: () => {
            toast.success('Review submitted successfully!')
            setShowReviewForm(false)
            setRating(5)
            setTitle('')
            setReviewText('')
            queryClient.invalidateQueries({ queryKey: ['product-reviews', productId] })
            queryClient.invalidateQueries({ queryKey: ['review-stats', productId] })
        },
        onError: (error: any) => {
            toast.error(
                error.response?.data?.detail || 'Failed to submit review. Please try again'
            )
        },
    })

    // Mark review helpful
    const markHelpfulMutation = useMutation({
        mutationFn: async ({ reviewId, isHelpful }: { reviewId: string; isHelpful: boolean }) => {
            await api.post(`/api/v1/reviews/${reviewId}/helpful`, { is_helpful: isHelpful })
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['product-reviews', productId] })
        },
    })

    const handleSubmitReview = (e: React.FormEvent) => {
        e.preventDefault()

        if (!isAuthenticated) {
            toast.info('Please login to submit a review')
            return
        }

        submitReviewMutation.mutate({
            product_id: productId,
            rating,
            title,
            review_text: reviewText,
        })
    }

    const StarRating = ({ rating, size = 20 }: { rating: number; size?: number }) => {
        return (
            <div className="flex">
                {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                        key={star}
                        className={`${star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-text-tertiary'}`}
                        size={size}
                    />
                ))}
            </div>
        )
    }

    const RatingBar = ({ rating, count, total }: { rating: number; count: number; total: number }) => {
        const percentage = total > 0 ? (count / total) * 100 : 0
        const widthClass = percentage > 75 ? 'w-3/4' : percentage > 50 ? 'w-1/2' : percentage > 25 ? 'w-1/4' : 'w-0'
        return (
            <div className="flex items-center gap-2">
                <span className="w-12 text-sm text-text-primary">{rating} star</span>
                <div className="flex-1 bg-bg-tertiary rounded-full h-2 relative overflow-hidden">
                    <div
                        className={`absolute top-0 left-0 h-full bg-yellow-400 rounded-full transition-all duration-300 ${widthClass}`}
                    />
                </div>
                <span className="w-12 text-sm text-text-secondary">{count}</span>
            </div>
        )
    }

    if (reviewsLoading) {
        return <div className="text-center py-8">Loading reviews...</div>
    }

    return (
        <div className="mt-12">
            <h2 className="text-2xl font-bold mb-6">Customer Reviews</h2>

            {/* Review Summary */}
            {stats && (
                <div className="bg-bg-primary p-6 rounded-lg shadow-md mb-6 border border-border-color">
                    <div className="grid md:grid-cols-2 gap-6">
                        <div className="text-center">
                            <div className="text-5xl font-bold mb-2 text-text-primary">{stats.average_rating.toFixed(1)}</div>
                            <StarRating rating={Math.round(stats.average_rating)} size={24} />
                            <div className="text-text-secondary mt-2">
                                Based on {stats.total_reviews} reviews
                            </div>
                            <div className="text-sm text-text-tertiary mt-1">
                                {stats.verified_purchase_percentage.toFixed(0)}% verified purchases
                            </div>
                        </div>

                        <div className="space-y-2">
                            {[5, 4, 3, 2, 1].map((rating) => (
                                <RatingBar
                                    key={rating}
                                    rating={rating}
                                    count={stats.rating_distribution[rating] || 0}
                                    total={stats.total_reviews}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="flex flex-wrap gap-4 mb-6">
                <button
                    onClick={() => setShowReviewForm(!showReviewForm)}
                    className="px-4 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover"
                >
                    {showReviewForm ? 'Cancel' : 'Write a Review'}
                </button>

                <select
                    value={filterRating || ''}
                    onChange={(e) => setFilterRating(e.target.value ? Number(e.target.value) : null)}
                    aria-label="Filter reviews by rating"
                    className="px-4 py-2 border rounded-lg"
                >
                    <option value="">All Ratings</option>
                    <option value="5">5 Stars</option>
                    <option value="4">4+ Stars</option>
                    <option value="3">3+ Stars</option>
                    <option value="2">2+ Stars</option>
                    <option value="1">1+ Stars</option>
                </select>

                <label className="flex items-center gap-2">
                    <input
                        type="checkbox"
                        checked={verifiedOnly}
                        onChange={(e) => setVerifiedOnly(e.target.checked)}
                        className="rounded"
                    />
                    <span>Verified Purchases Only</span>
                </label>
            </div>

            {/* Review Form */}
            {showReviewForm && (
                <form onSubmit={handleSubmitReview} className="bg-bg-primary p-6 rounded-lg shadow-md mb-6 border border-border-color">
                    <h3 className="text-xl font-semibold mb-4 text-text-primary">Write Your Review</h3>

                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2 text-text-primary">Rating</label>
                        <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    type="button"
                                    onClick={() => setRating(star)}
                                    aria-label={`Rate ${star} star${star > 1 ? 's' : ''}`}
                                    className="focus:outline-none"
                                >
                                    <Star
                                        className={`${star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-text-tertiary'} hover:text-yellow-400`}
                                        size={32}
                                    />
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2 text-text-primary">Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full px-4 py-2 border border-border-color rounded-lg bg-bg-primary text-text-primary"
                            placeholder="Sum up your experience"
                        />
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2 text-text-primary">Review</label>
                        <textarea
                            value={reviewText}
                            onChange={(e) => setReviewText(e.target.value)}
                            rows={4}
                            className="w-full px-4 py-2 border border-border-color rounded-lg bg-bg-primary text-text-primary"
                            placeholder="Share your thoughts about this product"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={submitReviewMutation.isPending}
                        className="px-6 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover disabled:opacity-50"
                    >
                        {submitReviewMutation.isPending ? 'Submitting...' : 'Submit Review'}
                    </button>
                </form>
            )}

            {/* Reviews List */}
            <div className="space-y-4">
                {reviews && reviews.length > 0 ? (
                    reviews.map((review) => (
                        <div key={review.id} className="bg-bg-primary p-6 rounded-lg shadow-md border border-border-color">
                            <div className="flex items-start justify-between mb-2">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <StarRating rating={review.rating} size={16} />
                                        {review.is_verified_purchase && (
                                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                                                Verified Purchase
                                            </span>
                                        )}
                                    </div>
                                    <h4 className="font-semibold text-text-primary">{review.title}</h4>
                                </div>
                                <span className="text-sm text-text-tertiary">
                                    {new Date(review.created_at).toLocaleDateString()}
                                </span>
                            </div>

                            <p className="text-sm text-text-secondary mb-2">By {review.user_name}</p>
                            <p className="text-text-primary mb-4">{review.review_text}</p>

                            {/* Helpful buttons */}
                            <div className="flex items-center gap-4 text-sm">
                                <button
                                    onClick={() =>
                                        markHelpfulMutation.mutate({ reviewId: review.id, isHelpful: true })
                                    }
                                    className="text-text-secondary hover:text-theme-primary"
                                >
                                    Helpful ({review.helpful_count})
                                </button>
                                <button
                                    onClick={() =>
                                        markHelpfulMutation.mutate({ reviewId: review.id, isHelpful: false })
                                    }
                                    className="text-text-secondary hover:text-red-600"
                                >
                                    Not Helpful ({review.not_helpful_count})
                                </button>
                            </div>

                            {/* Store Response */}
                            {review.responses && review.responses.length > 0 && (
                                <div className="mt-4 ml-8 p-4 bg-bg-tertiary rounded-lg">
                                    <p className="font-semibold text-sm mb-2 text-text-primary">
                                        Response from {review.responses[0].responder_name}
                                    </p>
                                    <p className="text-sm text-text-secondary">{review.responses[0].response_text}</p>
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="text-center py-12 text-text-tertiary">
                        <p>No reviews yet. Be the first to review this product!</p>
                    </div>
                )}
            </div>
        </div>
    )
}
