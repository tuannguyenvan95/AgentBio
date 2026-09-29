/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cleanroom: {
          bg: '#F1F5F9',        // Sterile laboratory slate
          card: '#FFFFFF',      // Pure white card
          surface: '#F8FAFC',   // Sub-panel white
          border: '#CBD5E1',    // Precision steel border
          borderHover: '#94A3B8',
          textMuted: '#64748B', // Cool grey text
          textDark: '#0F172A',  // Deep slate headings
        },
        biogreen: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          500: '#10B981',
          600: '#059669',       // Bio-Green for verified sequences
          700: '#047857',
        },
        nucleic: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          500: '#8B5CF6',
          600: '#7C3AED',       // Nucleic Purple for active synthesis
          700: '#6D28D9',
        },
        biohazard: {
          50: '#FFF7ED',
          100: '#FFEDD5',
          500: '#F97316',
          600: '#EA580C',       // Biohazard Orange for flagged pathogen alerts
          700: '#C2410C',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', '"Plus Jakarta Sans"', 'sans-serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'clean-card': '0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05)',
        'clean-elevated': '0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.05)',
        'biogreen-glow': '0 0 15px -3px rgba(5, 150, 105, 0.3)',
        'biohazard-glow': '0 0 15px -3px rgba(234, 88, 12, 0.3)',
        'nucleic-glow': '0 0 15px -3px rgba(124, 58, 237, 0.25)',
      },
    },
  },
  plugins: [],
}
