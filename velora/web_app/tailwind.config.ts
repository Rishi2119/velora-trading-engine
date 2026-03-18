import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0A0F1C',
        card: '#121826',
        profit: '#00FF9F',
        loss: '#FF4D4D',
        premium: '#FFD700',
        electric: '#3A86FF',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(58, 134, 255, 0.3)',
      },
    },
  },
  plugins: [],
};

export default config;
