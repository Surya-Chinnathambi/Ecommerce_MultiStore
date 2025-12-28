/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                // Theme-aware colors using CSS variables
                'bg-primary': 'rgb(var(--bg-primary) / <alpha-value>)',
                'bg-secondary': 'rgb(var(--bg-secondary) / <alpha-value>)',
                'bg-tertiary': 'rgb(var(--bg-tertiary) / <alpha-value>)',
                'text-primary': 'rgb(var(--text-primary) / <alpha-value>)',
                'text-secondary': 'rgb(var(--text-secondary) / <alpha-value>)',
                'text-tertiary': 'rgb(var(--text-tertiary) / <alpha-value>)',
                'border-color': 'rgb(var(--border-color) / <alpha-value>)',
                'theme-primary': 'rgb(var(--primary) / <alpha-value>)',
                'theme-primary-hover': 'rgb(var(--primary-hover) / <alpha-value>)',
                'theme-accent': 'rgb(var(--accent) / <alpha-value>)',

                // Legacy color schemes for compatibility
                primary: {
                    50: '#faf5ff',
                    100: '#f3e8ff',
                    200: '#e9d5ff',
                    300: '#d8b4fe',
                    400: '#c084fc',
                    500: '#a855f7',
                    600: '#9333ea',
                    700: '#7e22ce',
                    800: '#6b21a8',
                    900: '#581c87',
                },
                secondary: {
                    50: '#fdf4ff',
                    100: '#fae8ff',
                    200: '#f5d0fe',
                    300: '#f0abfc',
                    400: '#e879f9',
                    500: '#d946ef',
                    600: '#c026d3',
                    700: '#a21caf',
                    800: '#86198f',
                    900: '#701a75',
                },
                accent: {
                    50: '#fef2f2',
                    100: '#fee2e2',
                    200: '#fecaca',
                    300: '#fca5a5',
                    400: '#f87171',
                    500: '#ef4444',
                    600: '#dc2626',
                    700: '#b91c1c',
                    800: '#991b1b',
                    900: '#7f1d1d',
                },
            },
            backgroundImage: {
                'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'gradient-secondary': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                'gradient-accent': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            },
            animation: {
                'slide-in-left': 'slideInLeft 0.3s ease-out',
                'fade-in': 'fadeIn 0.5s ease-out',
            },
            keyframes: {
                slideInLeft: {
                    '0%': { transform: 'translateX(-100%)', opacity: '0' },
                    '100%': { transform: 'translateX(0)', opacity: '1' },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
            },
        },
    },
    plugins: [],
}
