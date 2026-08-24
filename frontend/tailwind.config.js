/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f7f1eb',
          100: '#ede3d8',
          200: '#dbc7b1',
          300: '#c4a68a',
          400: '#a98469',
          500: '#7a675a',
          600: '#6b5a4e',
          700: '#574a40',
          800: '#463c34',
          900: '#383838',
          950: '#1e1e1e',
        },
        dark: {
          50:  '#f7f1eb',
          100: '#e8ddd4',
          200: '#c9b8ac',
          300: '#a89080',
          400: '#8a6e5f',
          500: '#7a675a',
          600: '#574a40',
          700: '#3d342c',
          800: '#2a2420',
          900: '#1a1714',
          950: '#100e0c',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
