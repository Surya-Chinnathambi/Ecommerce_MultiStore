import React, { createContext, useContext, useState, useEffect } from 'react'

type Theme = 'light' | 'dark'
type ColorScheme = 'purple' | 'blue' | 'green' | 'orange' | 'pink'

interface ThemeContextType {
    theme: Theme
    colorScheme: ColorScheme
    toggleTheme: () => void
    setColorScheme: (scheme: ColorScheme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const useTheme = () => {
    const context = useContext(ThemeContext)
    if (!context) {
        throw new Error('useTheme must be used within ThemeProvider')
    }
    return context
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [theme, setTheme] = useState<Theme>(() => {
        const savedTheme = localStorage.getItem('theme') as Theme
        return savedTheme || 'light'
    })

    const [colorScheme, setColorSchemeState] = useState<ColorScheme>(() => {
        const savedScheme = localStorage.getItem('colorScheme') as ColorScheme
        return savedScheme || 'purple'
    })

    useEffect(() => {
        const root = document.documentElement

        // Remove old theme classes
        root.classList.remove('light', 'dark')
        // Add current theme
        root.classList.add(theme)

        // Save to localStorage
        localStorage.setItem('theme', theme)
    }, [theme])

    useEffect(() => {
        const root = document.documentElement

        // Remove old color scheme classes
        root.classList.remove('scheme-purple', 'scheme-blue', 'scheme-green', 'scheme-orange', 'scheme-pink')
        // Add current color scheme
        root.classList.add(`scheme-${colorScheme}`)

        // Save to localStorage
        localStorage.setItem('colorScheme', colorScheme)
    }, [colorScheme])

    const toggleTheme = () => {
        setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
    }

    const setColorScheme = (scheme: ColorScheme) => {
        setColorSchemeState(scheme)
    }

    return (
        <ThemeContext.Provider value={{ theme, colorScheme, toggleTheme, setColorScheme }}>
            {children}
        </ThemeContext.Provider>
    )
}
