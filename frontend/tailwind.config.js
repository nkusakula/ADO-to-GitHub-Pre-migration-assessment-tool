/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ado-blue': '#0078d4',
        'github-green': '#238636',
        'github-dark': '#0d1117',
        'github-darker': '#010409',
      },
    },
  },
  plugins: [],
}
