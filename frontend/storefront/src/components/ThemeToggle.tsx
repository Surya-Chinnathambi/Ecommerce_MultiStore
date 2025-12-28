import { Moon, Sun, Palette } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useState, useRef, useEffect } from 'react'

const colorSchemes = [
    { name: 'Purple', value: 'purple' as const, color: 'bg-purple-600' },
    { name: 'Blue', value: 'blue' as const, color: 'bg-blue-600' },
    { name: 'Green', value: 'green' as const, color: 'bg-green-600' },
    { name: 'Orange', value: 'orange' as const, color: 'bg-orange-600' },
    { name: 'Pink', value: 'pink' as const, color: 'bg-pink-600' },
]

export default function ThemeToggle() {
    const { theme, colorScheme, toggleTheme, setColorScheme } = useTheme()
    const [showColorPicker, setShowColorPicker] = useState(false)
    const pickerRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
                setShowColorPicker(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    return (
        <div className="flex items-center space-x-2">
            {/* Theme Toggle */}
            <button
                onClick={toggleTheme}
                className="p-2 rounded-lg bg-bg-tertiary hover:bg-border-color transition-colors"
                aria-label="Toggle theme"
                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
                {theme === 'light' ? (
                    <Moon className="h-5 w-5 text-text-secondary" />
                ) : (
                    <Sun className="h-5 w-5 text-text-secondary" />
                )}
            </button>

            {/* Color Scheme Picker */}
            <div className="relative" ref={pickerRef}>
                <button
                    onClick={() => setShowColorPicker(!showColorPicker)}
                    className="p-2 rounded-lg bg-bg-tertiary hover:bg-border-color transition-colors"
                    aria-label="Choose color scheme"
                    title="Choose color scheme"
                >
                    <Palette className="h-5 w-5 text-text-secondary" />
                </button>

                {showColorPicker && (
                    <div className="absolute right-0 mt-2 w-48 bg-bg-primary border border-border-color rounded-lg shadow-lg z-50 p-3">
                        <p className="text-sm font-medium text-text-primary mb-2">Color Scheme</p>
                        <div className="space-y-2">
                            {colorSchemes.map((scheme) => (
                                <button
                                    key={scheme.value}
                                    onClick={() => {
                                        setColorScheme(scheme.value)
                                        setShowColorPicker(false)
                                    }}
                                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${colorScheme === scheme.value
                                            ? 'bg-theme-primary text-white'
                                            : 'hover:bg-bg-tertiary text-text-primary'
                                        }`}
                                >
                                    <span className={`w-4 h-4 rounded-full ${scheme.color}`}></span>
                                    <span className="text-sm font-medium">{scheme.name}</span>
                                    {colorScheme === scheme.value && (
                                        <span className="ml-auto text-xs">✓</span>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
