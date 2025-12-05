import { ListGroup } from 'react-bootstrap';

export default function TransactionItem({ transaction }) {
  const isIncome = transaction.type === 'income';
  const icon = isIncome ? '✓' : '✗';
  const accentColor = isIncome ? '#22c55e' : '#ef4444';
  const accentBg = isIncome ? '#f0fdf4' : '#fef2f2';
  const sign = isIncome ? '+' : '−';

  return (
    <ListGroup.Item
      className="d-flex gap-3 align-items-center p-3"
      style={{ borderRadius: '12px', border: '1px solid #e5e7eb', marginBottom: '8px' }}
    >
      <div
        className="d-flex align-items-center justify-content-center flex-shrink-0 fw-bold"
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '12px',
          backgroundColor: accentBg,
          color: accentColor,
          fontSize: '18px',
        }}
      >
        {icon}
      </div>

      <div className="flex-grow-1">
        <p className="mb-1 fw-semibold" style={{ fontSize: '14px', color: '#1a202c' }}>
          {transaction.note || 'Transaction'}
        </p>
        <p className="text-muted small mb-0">{transaction.date}</p>
      </div>

      <p className="mb-0 fw-bold" style={{ fontSize: '14px', color: accentColor }}>
        {sign} KES {Number(transaction.amount || 0).toLocaleString()}
      </p>
    </ListGroup.Item>
  );
}
