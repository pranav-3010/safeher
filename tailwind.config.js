/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand
        navy: {
          DEFAULT: '#172033',
          50: '#EEF2F8',
          100: '#D7DEEA',
          200: '#AEBBD2',
          300: '#7E8FB3',
          400: '#52658E',
          500: '#34466B',
          600: '#283755',
          700: '#1E2A45',
          800: '#172033',
          900: '#101828',
        },
        accent: {
          DEFAULT: '#2563EB',
          50: '#EFF4FF',
          100: '#DBE6FE',
          200: '#BFCEFE',
          300: '#93AEFD',
          400: '#608AFA',
          500: '#3B6BF6',
          600: '#2563EB',
          700: '#1D4FD8',
          800: '#1E42AE',
          900: '#1E3A89',
        },
        // Safety status
        safe: {
          DEFAULT: '#16803A',
          light: '#E8F5EC',
          dark: '#0F5E2A',
        },
        moderate: {
          DEFAULT: '#B77900',
          light: '#FBF3DD',
          dark: '#855A00',
        },
        highrisk: {
          DEFAULT: '#C2410C',
          light: '#FCEFE6',
          dark: '#8F2E07',
        },
        danger: {
          DEFAULT: '#B91C1C',
          light: '#FCEAEA',
          dark: '#8A1414',
        },
        // Neutrals
        ink: {
          DEFAULT: '#111827',
          soft: '#6B7280',
        },
        canvas: {
          DEFAULT: '#FFFFFF',
          subtle: '#F7F8FA',
        },
        border: {
          DEFAULT: '#E5E7EB',
          strong: '#D1D5DB',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px 0 rgba(17, 24, 39, 0.04), 0 1px 3px 0 rgba(17, 24, 39, 0.06)',
        cardHover: '0 4px 12px -2px rgba(17, 24, 39, 0.08), 0 2px 6px -1px rgba(17, 24, 39, 0.06)',
        popover: '0 12px 28px -6px rgba(17, 24, 39, 0.14), 0 4px 10px -2px rgba(17, 24, 39, 0.08)',
      },
      borderRadius: {
        DEFAULT: '10px',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          from: { transform: 'translateX(100%)' },
          to: { transform: 'translateX(0)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.9)', opacity: '0.7' },
          '70%': { transform: 'scale(1.6)', opacity: '0' },
          '100%': { transform: 'scale(1.6)', opacity: '0' },
        },
        'sos-pulse': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(185, 28, 28, 0.5)' },
          '50%': { boxShadow: '0 0 0 16px rgba(185, 28, 28, 0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-in-right': 'slide-in-right 0.25s ease-out',
        'pulse-ring': 'pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite',
        'sos-pulse': 'sos-pulse 2s infinite',
      },
    },
  },
  plugins: [],
};
