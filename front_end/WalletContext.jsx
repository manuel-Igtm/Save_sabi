import { createContext, useState, useEffect } from 'react';
import { authAPI, walletAPI, transactionAPI, goalsAPI, nudgesAPI } from './src/api/endpoints';

export const WalletContext = createContext();

export function WalletProvider({ children }) {
  const [wallet, setWallet] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user and wallet data on mount
  useEffect(() => {
    const initializeData = async () => {
      try {
        const token = localStorage.getItem('authToken');
        if (token) {
          // User is logged in, fetch real data
          await fetchUserData();
        } else {
          // No token, user needs to login
          setLoading(false);
        }
      } catch (err) {
        console.error('Failed to initialize data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    initializeData();
  }, []);

  const fetchUserData = async () => {
    try {
      setLoading(true);

      // Fetch user info
      const userResponse = await authAPI.getUser();
      setUser(userResponse.data);

      // Fetch primary wallet
      const walletResponse = await walletAPI.getPrimaryWallet();
      const walletData = walletResponse.data;

      // Fetch recent transactions
      const transactionsResponse = await transactionAPI.getTransactions({
        wallet_id: walletData.id,
        limit: 10,
      });

      // Fetch goals
      const goalsResponse = await goalsAPI.getGoals();

      // Fetch nudges/alerts
      const nudgesResponse = await nudgesAPI.getNudges();

      // Combine data into wallet object
      setWallet({
        id: walletData.id,
        total: parseFloat(walletData.balance_savings) + parseFloat(walletData.balance_spend),
        savings: parseFloat(walletData.balance_savings),
        spendable: parseFloat(walletData.balance_spend),
        currency: walletData.currency,
        goal: goalsResponse.data[0]?.target_amount || 0,
        goalId: goalsResponse.data[0]?.id,
        alerts: nudgesResponse.data.map(n => n.message),
        transactions: transactionsResponse.data.map(t => ({
          id: t.id,
          type: t.direction === 'in' ? 'income' : 'spend',
          amount: parseFloat(t.amount),
          date: new Date(t.created_at).toLocaleString(),
          note: t.category || t.metadata?.note || 'No description',
          category: t.category,
        })),
      });

      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
      setError(err.message);
      setLoading(false);

      // If unauthorized, clear token
      if (err.response?.status === 401) {
        localStorage.removeItem('authToken');
        setUser(null);
      }
    }
  };

  const login = async (email, password) => {
    try {
      setLoading(true);
      setError(null);

      const response = await authAPI.login({ email, password });
      const { token, user: userData } = response.data;

      // Save token
      localStorage.setItem('authToken', token);
      setUser(userData);

      // Fetch wallet data
      await fetchUserData();

      return { success: true };
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.response?.data?.message || 'Login failed');
      setLoading(false);
      return { success: false, error: err.response?.data?.message || 'Login failed' };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('saveSabiUser');
      setUser(null);
      setWallet(null);
    }
  };

  const addTransaction = async (transaction) => {
    try {
      setError(null);

      // Create transaction via API
      const response = await transactionAPI.createTransaction({
        wallet: wallet.id,
        amount: transaction.amount,
        direction: transaction.type === 'income' ? 'in' : 'out',
        category: transaction.category || (transaction.type === 'income' ? 'income' : 'expense'),
        metadata: {
          note: transaction.note,
        },
      });

      // Refresh wallet data to get updated balances
      await fetchUserData();

      return { success: true, data: response.data };
    } catch (err) {
      console.error('Failed to add transaction:', err);
      setError(err.response?.data?.message || 'Failed to add transaction');
      return { success: false, error: err.response?.data?.message || 'Failed to add transaction' };
    }
  };

  const updateGoal = async (newGoal) => {
    try {
      setError(null);

      if (wallet.goalId) {
        // Update existing goal
        await goalsAPI.updateGoal(wallet.goalId, {
          target_amount: newGoal,
        });
      } else {
        // Create new goal
        const response = await goalsAPI.createGoal({
          wallet: wallet.id,
          name: 'Savings Goal',
          target_amount: newGoal,
        });
        setWallet(prev => ({ ...prev, goalId: response.data.id }));
      }

      setWallet(prev => ({ ...prev, goal: newGoal }));

      return { success: true };
    } catch (err) {
      console.error('Failed to update goal:', err);
      setError(err.response?.data?.message || 'Failed to update goal');
      return { success: false, error: err.response?.data?.message || 'Failed to update goal' };
    }
  };

  const clearAlert = async (index) => {
    try {
      // In a real implementation, you'd call the API to mark the nudge as read
      // For now, just remove from local state
      setWallet(prev => ({
        ...prev,
        alerts: prev.alerts.filter((_, i) => i !== index),
      }));
    } catch (err) {
      console.error('Failed to clear alert:', err);
    }
  };

  return (
    <WalletContext.Provider
      value={{
        wallet,
        user,
        loading,
        error,
        addTransaction,
        updateGoal,
        login,
        logout,
        clearAlert,
        refreshData: fetchUserData,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}
