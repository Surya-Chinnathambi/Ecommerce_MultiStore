/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                sans: [
                    'Inter', 'Geist', '-apple-system', 'BlinkMacSystemFont',
                    'Segoe UI', 'Roboto', 'system-ui', 'sans-serif',
                ],
                mono: [
                    'Geist Mono', 'JetBrains Mono', 'Fira Code',
                    'ui-monospace', 'SFMono-Regular', 'monospace',
                ],
            },
            colors: {
                // ─── Semantic design-token colors (CSS variable backed) ───────
                'bg-primary': 'rgb(var(--bg-primary) / <alpha-value>)',
                'bg-secondary': 'rgb(var(--bg-secondary) / <alpha-value>)',
                'bg-tertiary': 'rgb(var(--bg-tertiary) / <alpha-value>)',
                'bg-elevated': 'rgb(var(--bg-elevated) / <alpha-value>)',
                'text-primary': 'rgb(var(--text-primary) / <alpha-value>)',
                'text-secondary': 'rgb(var(--text-secondary) / <alpha-value>)',
                'text-tertiary': 'rgb(var(--text-tertiary) / <alpha-value>)',
                'text-quaternary': 'rgb(var(--text-quaternary) / <alpha-value>)',
                'border-color': 'rgb(var(--border-color) / <alpha-value>)',
                'border-strong': 'rgb(var(--border-strong) / <alpha-value>)',
                'theme-primary': 'rgb(var(--primary) / <alpha-value>)',
                'theme-primary-hover': 'rgb(var(--primary-hover) / <alpha-value>)',
                'theme-accent': 'rgb(var(--accent) / <alpha-value>)',
            },

            boxShadow: {
                'xs': 'var(--shadow-xs)',
                'sm': 'var(--shadow-sm)',
                'md': 'var(--shadow-md)',
                'lg': 'var(--shadow-lg)',
                'xl': 'var(--shadow-xl)',
                '2xl': 'var(--shadow-2xl)',
                'card': 'var(--shadow-sm)',
                'dropdown': 'var(--shadow-lg)',
                'modal': 'var(--shadow-xl)',
                'glow': '0 0 30px rgb(var(--primary) / 0.25)',
                'glow-sm': '0 0 15px rgb(var(--primary) / 0.2)',
            },

            borderRadius: {
                'sm': 'var(--radius-sm)',
                'md': 'var(--radius-md)',
                'lg': 'var(--radius-lg)',
                'xl': 'var(--radius-xl)',
                '2xl': 'var(--radius-2xl)',
            },

            backgroundImage: {
                'gradient-primary': 'linear-gradient(135deg, rgb(var(--primary)), rgb(var(--accent)))',
                'gradient-warm': 'linear-gradient(135deg, #f59e0b, #ef4444)',
                'gradient-cool': 'linear-gradient(135deg, #06b6d4, #6366f1)',
                'gradient-surface': 'linear-gradient(180deg, rgb(var(--bg-primary)), rgb(var(--bg-secondary)))',
            },

            spacing: {
                '4.5': '1.125rem',
                '13': '3.25rem',
                '18': '4.5rem',
                '76': '19rem',
                '88': '22rem',
                '100': '25rem',
                '112': '28rem',
                '128': '32rem',
            },

            animation: {
                'fade-in': 'fadeIn 0.25s ease-out',
                'slide-up': 'slideUp 0.3s cubic-bezier(0.16,1,0.3,1)',
                'slide-down': 'slideDown 0.3s cubic-bezier(0.16,1,0.3,1)',
                'scale-in': 'scaleIn 0.2s cubic-bezier(0.16,1,0.3,1)',
                'bounce-in': 'bounceIn 0.4s cubic-bezier(0.16,1,0.3,1)',
                'float': 'float 5s ease-in-out infinite',
                'slide-in-left': 'slideInLeft 0.3s cubic-bezier(0.16,1,0.3,1)',
                'slide-in-right': 'slideInRight 0.3s cubic-bezier(0.16,1,0.3,1)',
                'shimmer': 'shimmer 1.6s ease-in-out infinite',
                'pulse-ring': 'pulseRing 2s ease-out infinite',
                'spin-slow': 'spin 3s linear infinite',
            },

            keyframes: {
                fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
                slideUp: { from: { transform: 'translateY(12px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
                slideDown: { from: { transform: 'translateY(-12px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
                scaleIn: { from: { transform: 'scale(0.94)', opacity: '0' }, to: { transform: 'scale(1)', opacity: '1' } },
                bounceIn: { '0%': { transform: 'scale(0.88)', opacity: '0' }, '60%': { transform: 'scale(1.03)' }, '100%': { transform: 'scale(1)', opacity: '1' } },
                float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
                slideInLeft: { from: { transform: 'translateX(-20px)', opacity: '0' }, to: { transform: 'translateX(0)', opacity: '1' } },
                slideInRight: { from: { transform: 'translateX(20px)', opacity: '0' }, to: { transform: 'translateX(0)', opacity: '1' } },
                shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
                pulseRing: { '0%': { transform: 'scale(0.8)', opacity: '0.8' }, '100%': { transform: 'scale(2)', opacity: '0' } },
            },

            transitionTimingFunction: {
                'spring': 'cubic-bezier(0.16, 1, 0.3, 1)',
                'bounce': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
            },
        },
    },
    plugins: [],
}
