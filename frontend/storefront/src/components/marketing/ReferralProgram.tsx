import { useEffect, useState } from 'react'
import { Copy, Gift, Users, MessageCircle, Mail, Check } from 'lucide-react'
import { marketingApi } from '@/lib/marketing-api'

interface ReferralCode {
    code: string
    referrer_reward: number
    referee_reward: number
    max_uses?: number
    times_used: number
}

interface ReferralStats {
    total_referrals: number
    successful_referrals: number
    pending_referrals: number
    total_rewards_earned: number
    total_rewards_pending: number
}

export default function ReferralProgram() {
    const [referralCode, setReferralCode] = useState<ReferralCode | null>(null)
    const [stats, setStats] = useState<ReferralStats | null>(null)
    const [copied, setCopied] = useState(false)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchReferralData()
    }, [])

    const fetchReferralData = async () => {
        try {
            const [codeResponse, statsResponse] = await Promise.all([
                marketingApi.getMyReferralCode(),
                marketingApi.getReferralStats(),
            ])

            if (codeResponse.data.referral_code) {
                setReferralCode(codeResponse.data.referral_code)
            }
            if (statsResponse.data) {
                setStats(statsResponse.data)
            }
        } catch (error) {
            console.error('Error fetching referral data:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleCopy = async () => {
        if (!referralCode) return

        try {
            await navigator.clipboard.writeText(referralCode.code)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        } catch (error) {
            console.error('Failed to copy:', error)
        }
    }

    const shareViaWhatsApp = () => {
        if (!referralCode) return
        const message = `Join me on this amazing platform! Use my referral code ${referralCode.code} and get ₹${referralCode.referee_reward} off on your first order! ${window.location.origin}`
        window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank')
    }

    const shareViaEmail = () => {
        if (!referralCode) return
        const subject = 'Get ₹' + referralCode.referee_reward + ' off on your first order!'
        const body = `Hey!\n\nI wanted to share this amazing platform with you. Use my referral code ${referralCode.code} to get ₹${referralCode.referee_reward} off on your first order!\n\nSign up here: ${window.location.origin}\n\nHappy shopping!`
        window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
            </div>
        )
    }

    if (!referralCode) {
        return null
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="text-center mb-8">
                <Gift className="w-16 h-16 mx-auto mb-4 text-theme-primary" />
                <h1 className="text-3xl font-bold bg-gradient-to-r from-theme-primary to-theme-accent bg-clip-text text-transparent mb-2">
                    Refer & Earn
                </h1>
                <p className="text-text-secondary">
                    Share the love and earn ₹{referralCode.referrer_reward} for every friend who makes their first purchase!
                </p>
            </div>

            {/* Referral Code Card */}
            <div className="bg-gradient-to-br from-theme-primary to-theme-accent rounded-2xl p-8 text-white mb-6 shadow-2xl">
                <div className="text-center">
                    <p className="text-sm opacity-90 mb-2">Your Referral Code</p>
                    <div className="flex items-center justify-center gap-4 mb-4">
                        <span className="text-4xl font-bold tracking-wider bg-white/20 px-6 py-3 rounded-lg backdrop-blur-sm">
                            {referralCode.code}
                        </span>
                    </div>
                    <button
                        onClick={handleCopy}
                        className="bg-white text-theme-primary px-6 py-2 rounded-full font-semibold hover:bg-bg-tertiary transition-all duration-300 flex items-center gap-2 mx-auto"
                    >
                        {copied ? (
                            <>
                                <Check className="w-5 h-5" />
                                Copied!
                            </>
                        ) : (
                            <>
                                <Copy className="w-5 h-5" />
                                Copy Code
                            </>
                        )}
                    </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/20">
                    <div className="text-center">
                        <p className="text-sm opacity-90">You Get</p>
                        <p className="text-2xl font-bold">₹{referralCode.referrer_reward}</p>
                    </div>
                    <div className="text-center">
                        <p className="text-sm opacity-90">Friend Gets</p>
                        <p className="text-2xl font-bold">₹{referralCode.referee_reward}</p>
                    </div>
                </div>
            </div>

            {/* Share Buttons */}
            <div className="bg-bg-primary rounded-xl shadow-lg p-6 mb-6 border border-border-color">
                <h3 className="font-semibold text-lg mb-4 text-center text-text-primary">Share with Friends</h3>
                <div className="flex flex-wrap gap-4 justify-center">
                    <button
                        onClick={shareViaWhatsApp}
                        className="flex items-center gap-2 px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all duration-300 transform hover:scale-105"
                    >
                        <MessageCircle className="w-5 h-5" />
                        WhatsApp
                    </button>
                    <button
                        onClick={shareViaEmail}
                        className="flex items-center gap-2 px-6 py-3 bg-theme-primary hover:bg-theme-primary-hover text-white rounded-lg transition-all duration-300 transform hover:scale-105"
                    >
                        <Mail className="w-5 h-5" />
                        Email
                    </button>
                </div>
            </div>

            {/* Stats */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-bg-primary rounded-xl shadow-lg p-6 text-center border border-border-color">
                        <Users className="w-8 h-8 mx-auto mb-2 text-theme-primary" />
                        <p className="text-2xl font-bold text-text-primary">{stats.total_referrals}</p>
                        <p className="text-sm text-text-secondary">Total Referrals</p>
                    </div>
                    <div className="bg-bg-primary rounded-xl shadow-lg p-6 text-center border border-border-color">
                        <Check className="w-8 h-8 mx-auto mb-2 text-green-600" />
                        <p className="text-2xl font-bold text-text-primary">{stats.successful_referrals}</p>
                        <p className="text-sm text-text-secondary">Successful</p>
                    </div>
                    <div className="bg-bg-primary rounded-xl shadow-lg p-6 text-center border border-border-color">
                        <Gift className="w-8 h-8 mx-auto mb-2 text-theme-accent" />
                        <p className="text-2xl font-bold text-text-primary">₹{stats.total_rewards_earned}</p>
                        <p className="text-sm text-text-secondary">Earned</p>
                    </div>
                    <div className="bg-bg-primary rounded-xl shadow-lg p-6 text-center border border-border-color">
                        <Gift className="w-8 h-8 mx-auto mb-2 text-orange-600" />
                        <p className="text-2xl font-bold text-text-primary">₹{stats.total_rewards_pending}</p>
                        <p className="text-sm text-text-secondary">Pending</p>
                    </div>
                </div>
            )}

            {/* How it Works */}
            <div className="mt-8 bg-bg-tertiary rounded-xl p-6 border border-border-color">
                <h3 className="font-semibold text-lg mb-4 text-text-primary">How It Works</h3>
                <ol className="space-y-3 text-text-primary">
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-theme-primary text-white rounded-full flex items-center justify-center text-sm font-semibold">1</span>
                        <span>Share your unique referral code with friends</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-theme-primary text-white rounded-full flex items-center justify-center text-sm font-semibold">2</span>
                        <span>Your friend signs up using your code and gets ₹{referralCode.referee_reward} off</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-theme-primary text-white rounded-full flex items-center justify-center text-sm font-semibold">3</span>
                        <span>When they complete their first purchase, you earn ₹{referralCode.referrer_reward}!</span>
                    </li>
                </ol>
            </div>
        </div>
    )
}
