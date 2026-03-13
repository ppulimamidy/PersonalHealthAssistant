/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './src/**/*.{ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: {
          400: '#26dcbb',
          500: '#00D4AA',
          600: '#00b894',
        },
        obsidian: {
          950: '#050709',
          900: '#080B10',
          800: '#0C0F14',
          700: '#12161D',
          650: '#161B24',
          600: '#1A1F29',
          500: '#232C3A',
          400: '#2D3748',
        },
        amber: {
          400: '#f9b13a',
          500: '#F5A623',
        },
        surface: {
          DEFAULT: '#12161D',
          raised: '#161B24',
          overlay: '#1A1F29',
          border: '#1E2530',
          divider: '#232C3A',
        },
        health: {
          excellent: '#00D4AA',
          good: '#6EE7B7',
          moderate: '#F5A623',
          poor: '#FB923C',
          critical: '#F87171',
        },
      },
      fontFamily: {
        display: ['Syne_700Bold'],
        sans: ['DMSans_400Regular'],
        sansMedium: ['DMSans_500Medium'],
      },
    },
  },
  plugins: [],
};
