/**
 * Design tokens — mirrors the web app's Tailwind theme.
 * Use these constants when Tailwind class names don't work
 * (e.g. in StyleSheet.create(), SVG fills, animation configs).
 */

export const colors = {
  primary: {
    400: '#26dcbb',
    500: '#00D4AA',
    600: '#00b894',
  },
  obsidian: {
    950: '#050709',
    900: '#080B10',  // Default background
    800: '#0C0F14',
    700: '#12161D',  // Card surface
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
  text: {
    primary: '#E8EDF5',
    secondary: '#526380',
    muted: '#2D3748',
  },
} as const;

export const typography = {
  fontFamily: {
    display: 'Syne_700Bold',
    sans: 'DMSans_400Regular',
    sansMedium: 'DMSans_500Medium',
  },
  size: {
    xs: 11,
    sm: 13,
    base: 15,
    lg: 17,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
  },
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  full: 9999,
} as const;
