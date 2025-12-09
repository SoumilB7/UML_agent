import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        claude: {
          bg: '#f0ebe5',       // Darker warm stone for main background
          card: '#f9f7f5',     // Lighter cream for cards
          border: '#e1dcd7',   // Warm border
          text: {
            primary: '#3e3a35', // Warm charcoal
            secondary: '#6b6661', // Warm gray
          },
          accent: '#da7756',   // Terracotta
        },
        primary: {
          50: '#fbf7f4',
          100: '#f5ebe3',
          200: '#edd9c8',
          300: '#e0bf9f',
          400: '#d29668',
          500: '#da7756', // Claude-ish orange
          600: '#c25e40',
          700: '#a24632',
          800: '#873d2f',
          900: '#6d352b',
        },
      },
    },
  },
  plugins: [],
}
export default config

