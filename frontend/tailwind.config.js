/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#FFFFFF',
        card: '#FFFFFF',
        elevated: '#F8F9FA',
        accent: '#1A73E8',
        'accent-light': '#E8F0FE',
        border: '#E8EAED',
        'text-primary': '#1F1F1F',
        'text-secondary': '#5F6368',
        'text-tertiary': '#9AA0A6',
        'risk-low': '#34A853',
        'risk-moderate': '#FBBC04',
        'risk-elevated': '#F97316',
        'risk-high': '#EA4335',
        'gpay-blue': '#1A73E8',
        'gpay-surface': '#F8F9FA',
      },
      fontFamily: {
        sans: ['Google Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '14px',
      },
      boxShadow: {
        'gpay': '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)',
        'gpay-lg': '0 4px 12px rgba(0,0,0,0.1)',
      },
    },
  },
  plugins: [],
}
