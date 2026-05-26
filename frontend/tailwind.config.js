export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'PingFang SC', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Bricolage Grotesque', 'Plus Jakarta Sans', 'PingFang SC', 'system-ui', 'sans-serif'],
      },
      colors: {
        bg: {
          deep: '#EDE8E1',
          base: '#F9F6F2',
          elevated: '#FFFFFF',
        },
        surface: {
          DEFAULT: 'rgba(44, 32, 20, 0.03)',
          hover: 'rgba(44, 32, 20, 0.05)',
          active: 'rgba(44, 32, 20, 0.07)',
        },
        border: {
          subtle: 'rgba(44, 32, 20, 0.07)',
          DEFAULT: 'rgba(44, 32, 20, 0.12)',
        },
        accent: {
          DEFAULT: '#C75832',
          light: '#E89270',
          dim: '#A3421F',
        },
        fg: {
          DEFAULT: '#2A2017',
          secondary: '#736860',
          dim: '#AEA59C',
        },
      },
    },
  },
}
