import { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Form, Button, Row, Col, Card, ListGroup, Badge } from 'react-bootstrap';
import TransactionItem from '../components/TransactionItem';
import { WalletContext } from '../context/WalletContext';

export default function History() {
  const navigate = useNavigate();
  const { wallet } = useContext(WalletContext);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  if (!wallet) {
    return (
      <Container fluid className="d-flex align-items-center justify-content-center vh-100">
        <p className="text-muted">Loading...</p>
      </Container>
    );
  }

  let filteredTransactions = wallet.transactions;

  // Filter by type
  if (filterType !== 'all') {
    filteredTransactions = filteredTransactions.filter(
      (t) => t.type === filterType
    );
  }

  // Filter by search term
  if (searchTerm) {
    filteredTransactions = filteredTransactions.filter((t) =>
      t.note.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }

  const handleExport = () => {
    const csv = [
      ['Date', 'Type', 'Amount', 'Note'],
      ...wallet.transactions.map((t) => [
        t.date,
        t.type,
        t.amount,
        t.note,
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `save-sabi-history-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <Container fluid style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px' }}>
      {/* Header */}
      <div
        className="sticky-top"
        style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          zIndex: 1020,
        }}
      >
        <Container style={{ maxWidth: '500px', margin: '0 auto' }}>
          <div className="d-flex align-items-center gap-3 py-3 px-4">
            <Button
              variant="link"
              className="text-decoration-none text-dark p-0"
              onClick={() => navigate('/dashboard')}
              style={{ fontSize: '24px' }}
            >
              ←
            </Button>
            <h1 className="mb-0 fw-bold" style={{ fontSize: '18px' }}>
              Transaction History
            </h1>
          </div>
        </Container>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: '500px', margin: '0 auto', padding: '24px 16px' }}>
        {/* Search */}
        <div className="mb-3">
          <Form.Control
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search transactions..."
            style={{ borderRadius: '8px', border: '2px solid #e5e7eb', padding: '10px 12px' }}
          />
        </div>

        {/* Filters */}
        <div className="d-flex gap-2 overflow-auto mb-4 pb-2">
          {['all', 'income', 'spend'].map((type) => (
            <Button
              key={type}
              onClick={() => setFilterType(type)}
              variant={filterType === type ? 'success' : 'outline-secondary'}
              size="sm"
              className="fw-semibold"
              style={{
                borderRadius: '20px',
                fontSize: '13px',
                whiteSpace: 'nowrap',
                flexShrink: 0,
              }}
            >
              {type === 'all' && 'All'}
              {type === 'income' && '➕ Income'}
              {type === 'spend' && '➖ Expense'}
            </Button>
          ))}
        </div>

        {/* Export Button */}
        <Button
          onClick={handleExport}
          className="w-100 mb-4"
          style={{
            borderRadius: '8px',
            border: '2px solid #22c55e',
            backgroundColor: 'transparent',
            color: '#22c55e',
            fontWeight: '600',
            padding: '10px',
            fontSize: '14px',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f0fdf4';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <span className="me-2">📥</span>Export as CSV
        </Button>

        {/* Transactions List */}
        <div className="mb-4">
          <p className="text-muted small fw-semibold mb-3" style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {filteredTransactions.length} Transaction{filteredTransactions.length !== 1 ? 's' : ''}
          </p>
          {filteredTransactions.length > 0 ? (
            <ListGroup variant="flush">
              {filteredTransactions.map((transaction) => (
                <div key={transaction.id}>
                  <TransactionItem transaction={transaction} />
                </div>
              ))}
            </ListGroup>
          ) : (
            <Card className="text-center shadow-sm" style={{ borderRadius: '12px', border: '1px solid #e5e7eb', padding: '48px 24px' }}>
              <p className="text-muted small mb-0">
                {searchTerm ? '🔍 No matching transactions' : '📭 No transactions'}
              </p>
            </Card>
          )}
        </div>

        {/* Stats */}
        {filteredTransactions.length > 0 && (
          <Row className="g-3">
            <Col xs={6}>
              <Card className="shadow-sm h-100" style={{ borderRadius: '12px', border: '1px solid #dcfce7', backgroundColor: '#f0fdf4' }}>
                <Card.Body className="p-3">
                  <p className="text-muted small fw-semibold mb-2" style={{ fontSize: '11px' }}>
                    Total Income
                  </p>
                  <p className="mb-0 fw-bold" style={{ fontSize: '16px', color: '#22c55e' }}>
                    KES{' '}
                    {filteredTransactions
                      .filter((t) => t.type === 'income')
                      .reduce((sum, t) => sum + t.amount, 0)
                      .toLocaleString()}
                  </p>
                </Card.Body>
              </Card>
            </Col>
            <Col xs={6}>
              <Card className="shadow-sm h-100" style={{ borderRadius: '12px', border: '1px solid #fee2e2', backgroundColor: '#fef2f2' }}>
                <Card.Body className="p-3">
                  <p className="text-muted small fw-semibold mb-2" style={{ fontSize: '11px' }}>
                    Total Expenses
                  </p>
                  <p className="mb-0 fw-bold" style={{ fontSize: '16px', color: '#ef4444' }}>
                    KES{' '}
                    {filteredTransactions
                      .filter((t) => t.type === 'spend')
                      .reduce((sum, t) => sum + t.amount, 0)
                      .toLocaleString()}
                  </p>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}
      </div>
    </Container>
  );
}
