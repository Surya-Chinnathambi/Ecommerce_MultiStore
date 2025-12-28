import { MessageCircle } from 'lucide-react'

interface WhatsAppButtonProps {
    productName: string
    productUrl: string
    price?: number
}

export default function WhatsAppButton({ productName, productUrl, price }: WhatsAppButtonProps) {
    const handleWhatsAppShare = () => {
        const message = `Check out this product: ${productName}${price ? ` - ₹${price}` : ''
            }\n${window.location.origin}${productUrl}`

        const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`
        window.open(whatsappUrl, '_blank')
    }

    return (
        <button
            onClick={handleWhatsAppShare}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all duration-300 transform hover:scale-105 shadow-md hover:shadow-lg"
        >
            <MessageCircle className="w-5 h-5" />
            <span className="font-medium">Share on WhatsApp</span>
        </button>
    )
}

// Floating WhatsApp button for contact
interface WhatsAppFloatButtonProps {
    phoneNumber: string
    message?: string
}

export function WhatsAppFloatButton({ phoneNumber, message = 'Hello! I need help.' }: WhatsAppFloatButtonProps) {
    const handleClick = () => {
        const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`
        window.open(whatsappUrl, '_blank')
    }

    return (
        <button
            onClick={handleClick}
            className="fixed bottom-6 right-6 z-50 bg-green-500 hover:bg-green-600 text-white p-4 rounded-full shadow-2xl transition-all duration-300 transform hover:scale-110 animate-bounce"
            aria-label="Contact us on WhatsApp"
        >
            <MessageCircle className="w-6 h-6" />
        </button>
    )
}
