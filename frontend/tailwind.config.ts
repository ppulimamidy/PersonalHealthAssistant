import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary — bioluminescent teal
        primary: {
          50:  '#e6fdf8',
          100: '#b3f5e8',
          200: '#80edd8',
          300: '#4de5c8',
          400: '#26dcbb',
          500: '#00D4AA', // core brand
          600: '#00b894',
          700: '#009e80',
          800: '#00836b',
          900: '#006b57',
        },
        // Obsidian — dark backgrounds
        obsidian: {
          950: '#050709',
          900: '#080B10',
          850: '#0a0e15',
          800: '#0C0F14',
          750: '#0f1318',
          700: '#12161D',
          650: '#161B24',
          600: '#1A1F29',
          550: '#1E2530',
          500: '#232C3A',
          400: '#2D3748',
          300: '#3D4F66',
          200: '#526380',
          100: '#6B7A8D',
          50:  '#8B97A8',
        },
        // Amber — secondary accent / highlights
        amber: {
          50:  '#fff9ec',
          100: '#fef0ca',
          200: '#fde099',
          300: '#fbc857',
          400: '#f9b13a',
          500: '#F5A623', // core accent
          600: '#d48d0f',
          700: '#b07209',
          800: '#8f5b07',
          900: '#754b06',
        },
        // Health semantic (preserved)
        health: {
          excellent: '#00D4AA',
          good:      '#6EE7B7',
          moderate:  '#F5A623',
          poor:      '#FB923C',
          critical:  '#F87171',
        },
        // Surfaces
        surface: {
          DEFAULT: '#12161D',
          raised:  '#161B24',
          overlay: '#1A1F29',
          border:  '#1E2530',
          divider: '#232C3A',
        },
      },
      fontFamily: {
        display: ['Syne', 'system-ui', 'sans-serif'],
        sans:    ['DM Sans', 'system-ui', 'sans-serif'],
        mono:    ['DM Mono', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },
      backgroundImage: {
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.05'/%3E%3C/svg%3E\")",
      },
      boxShadow: {
        'glow-teal':   '0 0 20px rgba(0, 212, 170, 0.15)',
        'glow-amber':  '0 0 20px rgba(245, 166, 35, 0.15)',
        'card':        '0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)',
        'card-hover':  '0 4px 12px rgba(0,0,0,0.5), 0 2px 4px rgba(0,0,0,0.3)',
        'inset-border': 'inset 0 0 0 1px rgba(255,255,255,0.06)',
      },
      animation: {
        'pulse-slow':  'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':     'fadeIn 0.3s ease-out',
        'slide-in':    'slideIn 0.25s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateX(-8px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
      borderRadius: {
        'xl':  '0.875rem',
        '2xl': '1.125rem',
      },
    },
  },
  plugins: [],
};

export default config;
