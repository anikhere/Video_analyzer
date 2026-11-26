/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        royal: {
          950: '#050C1E',
          900: '#081430',
          850: '#0B1A3D',
          800: '#0F224F',
          750: '#132A60',
          700: '#193678',
          600: '#1D4ED8',
          500: '#2563EB',
          400: '#3B82F6',
          300: '#60A5FA',
          200: '#93C5FD',
          100: '#DBEAFE',
        },
      },
      boxShadow: {
        royal: '0 18px 45px -15px rgba(4, 10, 28, 0.78), 0 0 0 1px rgba(147, 197, 253, 0.14)',
        'royal-glow': '0 0 28px -4px rgba(59, 130, 246, 0.38)',
      },
    },
  },
  plugins: [],
};
