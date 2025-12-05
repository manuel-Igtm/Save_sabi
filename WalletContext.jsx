import { createContext, useState, useEffect } from 'react';

export const WalletContext = createContext();

const MOCK_DATA = {
  total: 10000,
  savings: 2000,
  spendable: 8000,
  goal: 20000,
  alerts: [],
  transactions: [
    {
      id: 1,
      type: 'income',
      amount: 2000,
      date: 'Today 10:30 AM',
      note: 'Freelance',
    },
    {
      id: 2,
      type: 'spend',
      amount: 500,
      date: 'Yesterday',
      note: 'Lunch',
    },
    {
      id: 3,
      type: 'income',
      amount: 5000,
      date: 'Dec 3, 3:15 PM',
      note: 'Monthly Salary',
    },
    {
      id: 4,
      type: 'spend',
      amount: 1200,
      date: 'Dec 2',
      note: 'Groceries',
    },
    {
      id: 5,
      type: 'spend',
      amount: 300,
      date: 'Dec 1',
      note: 'Transport',
    },
  ],
};

export function WalletProvider({ children }) {
  const [wallet, setWallet] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Load from localStorage or use mock data
    const saved = localStorage.getItem('saveSabiWallet');
    if (saved) {
      setWallet(JSON.parse(saved));
    } else {
      setWallet(MOCK_DATA);
    }

    const savedUser = localStorage.getItem('saveSabiUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const saveWallet = (newWallet) => {
    setWallet(newWallet);
    localStorage.setItem('saveSabiWallet', JSON.stringify(newWallet));
  };

  const addTransaction = (transaction) => {
    const newWallet = { ...wallet };

    if (transaction.type === 'income') {
      const savingsAmount = transaction.amount * 0.2;
      const spendableAmount = transaction.amount * 0.8;

      newWallet.savings += savingsAmount;
      newWallet.spendable += spendableAmount;
      newWallet.total += transaction.amount;
    } else {
      // Spend transaction
      if (transaction.amount > newWallet.spendable) {
        newWallet.alerts = [
          ...newWallet.alerts,
          '⚠️ You attempted to spend more than available balance',
        ];
      } else {
        newWallet.spendable -= transaction.amount;
        newWallet.total -= transaction.amount;
      }
    }

    newWallet.transactions = [
      {
        id: newWallet.transactions.length + 1,
        ...transaction,
      },
      ...newWallet.transactions,
    ];

    saveWallet(newWallet);
  };

  const updateGoal = (newGoal) => {
    const newWallet = { ...wallet, goal: newGoal };
    saveWallet(newWallet);
  };

  const login = (email) => {
    const newUser = { email, loginTime: new Date().toISOString() };
    setUser(newUser);
    localStorage.setItem('saveSabiUser', JSON.stringify(newUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('saveSabiUser');
  };

  const clearAlert = (index) => {
    const newWallet = { ...wallet };
    newWallet.alerts.splice(index, 1);
    saveWallet(newWallet);
  };

  return (
    <WalletContext.Provider
      value={{
        wallet,
        user,
        addTransaction,
        updateGoal,
        login,
        logout,
        clearAlert,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}
