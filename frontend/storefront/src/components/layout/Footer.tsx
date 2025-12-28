import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import { MapPin, Phone } from 'lucide-react'

export default function Footer() {
    const { data: storeData } = useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    return (
        <footer className="bg-bg-tertiary text-text-secondary border-t border-border-color mt-12">
            <div className="container mx-auto px-4 py-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Store Info */}
                    <div>
                        <h3 className="text-text-primary text-lg font-bold mb-4">{storeData?.name}</h3>
                        {storeData?.address && (
                            <div className="flex items-start space-x-2 mb-2">
                                <MapPin className="h-5 w-5 mt-0.5 flex-shrink-0" />
                                <p className="text-sm">
                                    {storeData.address}
                                    {storeData.city && `, ${storeData.city}`}
                                    {storeData.state && `, ${storeData.state}`}
                                    {storeData.pincode && ` - ${storeData.pincode}`}
                                </p>
                            </div>
                        )}
                        {storeData?.owner_phone && (
                            <div className="flex items-center space-x-2 mb-2">
                                <Phone className="h-5 w-5" />
                                <a href={`tel:${storeData.owner_phone}`} className="text-sm hover:text-theme-primary">
                                    {storeData.owner_phone}
                                </a>
                            </div>
                        )}
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="text-text-primary text-lg font-bold mb-4">Quick Links</h3>
                        <ul className="space-y-2">
                            <li>
                                <a href="/" className="text-sm hover:text-theme-primary">Home</a>
                            </li>
                            <li>
                                <a href="/products" className="text-sm hover:text-theme-primary">Products</a>
                            </li>
                            <li>
                                <a href="/track-order" className="text-sm hover:text-theme-primary">Track Order</a>
                            </li>
                        </ul>
                    </div>

                    {/* Customer Support */}
                    <div>
                        <h3 className="text-text-primary text-lg font-bold mb-4">Customer Support</h3>
                        <p className="text-sm mb-4">
                            Have questions? We're here to help!
                        </p>
                        {storeData?.owner_phone && (
                            <p className="text-sm">
                                Call us: <a href={`tel:${storeData.owner_phone}`} className="text-theme-primary hover:text-theme-primary-hover">
                                    {storeData.owner_phone}
                                </a>
                            </p>
                        )}
                    </div>
                </div>

                <div className="border-t border-border-color mt-8 pt-6 text-center">
                    <p className="text-sm text-text-tertiary">
                        © {new Date().getFullYear()} {storeData?.name || 'Store'}. All rights reserved.
                    </p>
                </div>
            </div>
        </footer>
    )
}
