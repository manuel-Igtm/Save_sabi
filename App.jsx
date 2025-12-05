import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { WalletProvider, WalletContext } from './context/WalletContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import './index.css';
import { useContext } from 'react';

function ProtectedRoute({ children }) {
  const { user } = useContext(WalletContext);
  if (!user) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <WalletProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </WalletProvider>
  );
}
