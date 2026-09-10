/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0B0E14',
        card: '#141922',
        elevated: '#1C2230',
        accent: '#4F8CFF',
        'text-primary': '#E6EAF2',
        'text-secondary': '#8A93A6',
        'text-tertiary': '#5A6376',
        'risk-low': '#22C55E',
        'risk-moderate': '#EAB308',
        'risk-elevated': '#F97316',
        'risk-high': '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '14px',
      },
    },
  },
  plugins: [],
}
