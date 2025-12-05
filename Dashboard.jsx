import { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Button, ListGroup } from 'react-bootstrap';
import BalanceCard from '../components/BalanceCard';
import GoalProgressBar from '../components/GoalProgressBar';
import AlertBanner from '../components/AlertBanner';
import TransactionItem from '../components/TransactionItem';
import QuickAddModal from '../components/QuickAddModal';
import GoalModal from '../components/GoalModal';
import { WalletContext } from '../context/WalletContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { wallet, user, addTransaction, updateGoal, logout } = useContext(WalletContext);
  const [showIncomeModal, setShowIncomeModal] = useState(false);
  const [showSpendModal, setShowSpendModal] = useState(false);
  const [showGoalModal, setShowGoalModal] = useState(false);

  if (!wallet || !user) {
    return (
      <Container fluid className="d-flex align-items-center justify-content-center vh-100">
        <p className="text-muted">Loading...</p>
      </Container>
    );
  }

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const recentTransactions = wallet.transactions.slice(0, 5);

  return (
    <Container fluid style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', paddingBottom: '100px' }}>
      {/* Header */}
      <div
        className="sticky-top"
        style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          zIndex: 1020,
        }}
      >
        <Container className="max-w-md mx-auto px-4 py-3" style={{ maxWidth: '500px', margin: '0 auto' }}>
          <div className="d-flex align-items-center justify-content-between">
            <div className="d-flex align-items-center gap-3">
              <div
                className="d-flex align-items-center justify-content-center fw-bold text-white"
                style={{
                  width: '40px',
                  height: '40px',
                  backgroundColor: '#22c55e',
                  borderRadius: '8px',
                  fontSize: '18px',
                }}
              >
                SS
              </div>
              <div>
                <h1 className="mb-0 fw-bold" style={{ fontSize: '18px' }}>
                  Save Sabi
                </h1>
                <p className="mb-0 text-muted small">{user.email}</p>
              </div>
            </div>
            <div className="d-flex gap-2">
              <Button variant="link" className="text-decoration-none text-dark">
                ⚙️
              </Button>
              <Button variant="link" className="text-decoration-none text-dark" onClick={handleLogout}>
                🚪
              </Button>
            </div>
          </div>
        </Container>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: '500px', margin: '0 auto', padding: '24px 16px' }}>
        {/* Section A: Balance Summary */}
        <div className="mb-4">
          <h5 className="fw-bold text-dark mb-3" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Balance Summary
          </h5>
          <Card className="shadow-sm" style={{ borderRadius: '12px', border: '1px solid #e5e7eb' }}>
            <Card.Body className="p-0">
              <Row className="g-0">
                <Col xs={4} className="border-end p-3" style={{ borderColor: '#e5e7eb' }}>
                  <p className="text-muted small fw-semibold mb-2" style={{ fontSize: '11px' }}>
                    Total
                  </p>
                  <p className="mb-0 fw-bold" style={{ fontSize: '16px', color: '#1a202c' }}>
                    KES {Number(wallet.total).toLocaleString()}
                  </p>
                </Col>
                <Col xs={4} className="border-end p-3" style={{ borderColor: '#e5e7eb' }}>
                  <p className="text-muted small fw-semibold mb-2" style={{ fontSize: '11px' }}>
                    Savings
                  </p>
                  <p className="mb-0 fw-bold" style={{ fontSize: '16px', color: '#22c55e' }}>
                    KES {Number(wallet.savings).toLocaleString()}
                  </p>
                </Col>
                <Col xs={4} className="p-3">
                  <p className="text-muted small fw-semibold mb-2" style={{ fontSize: '11px' }}>
                    Spendable
                  </p>
                  <p className="mb-0 fw-bold" style={{ fontSize: '16px', color: '#3b82f6' }}>
                    KES {Number(wallet.spendable).toLocaleString()}
                  </p>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </div>

        {/* Section B: Goal Progress */}
        <div className="mb-4">
          <div className="d-flex align-items-center justify-content-between mb-3">
            <h5 className="fw-bold text-dark mb-0" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Savings Goal
            </h5>
            <Button
              variant="link"
              className="text-decoration-none p-0"
              style={{ fontSize: '12px', fontWeight: '600', color: '#22c55e' }}
              onClick={() => setShowGoalModal(true)}
            >
              ✎ Edit
            </Button>
          </div>
          <GoalProgressBar saved={wallet.savings} goal={wallet.goal} />
        </div>

        {/* Section C: Alerts */}
        {wallet.alerts.length > 0 && (
          <div className="mb-4">
            <h5 className="fw-bold text-dark mb-3" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Alerts
            </h5>
            <AlertBanner alerts={wallet.alerts} />
          </div>
        )}

        {/* Section D: Quick Actions */}
        <div className="d-flex gap-2 mb-4">
          <Button
            className="flex-grow-1 fw-bold"
            style={{
              backgroundColor: '#22c55e',
              borderColor: '#22c55e',
              borderRadius: '12px',
              padding: '12px',
              fontSize: '14px',
              border: 'none',
            }}
            onClick={() => setShowIncomeModal(true)}
          >
            ➕ Add Income
          </Button>
          <Button
            className="flex-grow-1 fw-bold"
            style={{
              backgroundColor: '#ef4444',
              borderColor: '#ef4444',
              borderRadius: '12px',
              padding: '12px',
              fontSize: '14px',
              border: 'none',
              color: 'white',
            }}
            onClick={() => setShowSpendModal(true)}
          >
            ➖ Add Expense
          </Button>
        </div>

        {/* Section E: Recent Transactions */}
        <div>
          <div className="d-flex align-items-center justify-content-between mb-3">
            <h5 className="fw-bold text-dark mb-0" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Recent Transactions
            </h5>
            <a
              href="/history"
              style={{ fontSize: '12px', fontWeight: '600', color: '#22c55e', textDecoration: 'none' }}
            >
              View All →
            </a>
          </div>
          {recentTransactions.length > 0 ? (
            <ListGroup variant="flush">
              {recentTransactions.map((transaction) => (
                <div key={transaction.id}>
                  <TransactionItem transaction={transaction} />
                </div>
              ))}
            </ListGroup>
          ) : (
            <Card className="text-center shadow-sm" style={{ borderRadius: '12px', border: '1px solid #e5e7eb', padding: '32px' }}>
              <p className="text-muted small mb-0">📭 No transactions yet. Start by adding income!</p>
            </Card>
          )}
        </div>
      </div>

      {/* Floating Action Buttons */}
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '16px',
          zIndex: 1010,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <Button
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: '#22c55e',
            border: 'none',
            fontSize: '24px',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          }}
          onClick={() => setShowIncomeModal(true)}
        >
          +
        </Button>
        <Button
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: '#ef4444',
            border: 'none',
            fontSize: '24px',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            color: 'white',
          }}
          onClick={() => setShowSpendModal(true)}
        >
          −
        </Button>
      </div>

      {/* Modals */}
      <QuickAddModal
        isOpen={showIncomeModal}
        type="income"
        onClose={() => setShowIncomeModal(false)}
        onAdd={(transaction) => addTransaction(transaction)}
      />

      <QuickAddModal
        isOpen={showSpendModal}
        type="spend"
        onClose={() => setShowSpendModal(false)}
        onAdd={(transaction) => addTransaction(transaction)}
      />

      <GoalModal
        isOpen={showGoalModal}
        onClose={() => setShowGoalModal(false)}
        onSave={updateGoal}
        currentGoal={wallet.goal}
      />
    </Container>
  );
}
