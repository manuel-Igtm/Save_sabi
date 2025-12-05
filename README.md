# Save Sabi — Micro-Savings Finance App

A modern, mobile-first micro-savings finance app built with **React + Vite + TailwindCSS**. Automatically divides income using the **20/80 rule** — 20% saved, 80% spendable.

## Features

✅ **Login Screen** — Simple, centered authentication with demo mode  
✅ **Dashboard** — Balance summary, savings goal progress, alerts, and recent transactions  
✅ **Add Transactions** — Income and expense modals with savings/spend preview  
✅ **Savings Goals** — Set and track custom savings targets  
✅ **Transaction History** — Filter, search, and export transaction CSV  
✅ **Responsive Mobile-First Design** — Works seamlessly on all devices  
✅ **Clean Fintech UI** — Modern, minimal, professional styling  

## Tech Stack

- **React 18** — UI framework
- **Vite** — Fast build tool and dev server
- **React Router v6** — Page navigation
- **TailwindCSS** — Utility-first CSS framework
- **PostCSS** — CSS processing with Tailwind adapter

## Project Structure

```
src/
├── components/
│   ├── BalanceCard.jsx
│   ├── GoalProgressBar.jsx
│   ├── AlertBanner.jsx
│   ├── TransactionItem.jsx
│   ├── QuickAddModal.jsx
│   └── GoalModal.jsx
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   └── History.jsx
├── context/
│   └── WalletContext.jsx
├── App.jsx
├── index.css
└── main.jsx
```

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Dev Server

```bash
npm run dev
```

The dev server will start at `http://localhost:5173/` (or another port if 5173 is in use).

### 3. Build for Production

```bash
npm run build
```

### 4. Preview Production Build

```bash
npm run preview
```

## Pages & Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `Login.jsx` | Authentication entry point |
| `/dashboard` | `Dashboard.jsx` | Main app screen with balance, goals, transactions |
| `/history` | `History.jsx` | Full transaction history with filters and export |

## Core Concepts

### 20/80 Rule

When you add income:
- **20%** automatically goes to **Savings** (locked)
- **80%** goes to **Spendable** (available to spend)

### Mock Data

The app uses local React context and `localStorage` for state management. No backend required.

Sample wallet structure:
```javascript
{
  total: 10000,
  savings: 2000,      // 20% locked
  spendable: 8000,    // 80% available
  goal: 20000,        // Savings target
  alerts: [],
  transactions: [...]
}
```

## Tailwind CSS Configuration

### Content Paths (tailwind.config.js)

```javascript
content: [
  './index.html',
  './src/**/*.{js,jsx,ts,tsx}',
],
```

### Custom Theme Colors

```javascript
colors: {
  'sabi-green': '#48BB78',   // Primary color
  'sabi-dark': '#1A202C',    // Text color
  'sabi-light': '#F7FAFC',   // Background
  'sabi-gray': '#718096',    // Secondary text
},
```

## Troubleshooting

### Tailwind Classes Not Applying

**Check:**
1. `index.css` is imported in `main.jsx`
2. `tailwind.config.js` content paths are correct
3. `postcss.config.js` uses `@tailwindcss/postcss`
4. Restart dev server: `npm run dev`

### Dev Server Port in Use

Vite will automatically try the next port (5174, 5175, etc.)

Or specify manually:
```bash
npm run dev -- --port 3000
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 12+
- Mobile browsers (iOS Safari, Chrome Mobile)

---

**Built with ❤️ using React, Vite, and TailwindCSS**
