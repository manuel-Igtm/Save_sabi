import { Card } from 'react-bootstrap';

export default function BalanceCard({ title, amount = 0, type = 'neutral', icon = null }) {
  const getTextColor = () => {
    if (type === 'savings') return '#22c55e';
    if (type === 'spendable') return '#3b82f6';
    return '#1a202c';
  };

  return (
    <Card className="h-100 shadow-sm" style={{ borderRadius: '12px', border: '1px solid #e5e7eb' }}>
      <Card.Body className="p-4">
        <div className="d-flex align-items-start justify-content-between gap-3">
          <div className="flex-grow-1">
            <p className="text-muted small fw-semibold text-uppercase mb-2" style={{ fontSize: '11px' }}>
              {title}
            </p>
            <p className="mb-0" style={{ fontSize: '24px', fontWeight: 'bold', color: getTextColor() }}>
              KES {Number(amount).toLocaleString()}
            </p>
          </div>
          {icon && (
            <div
              className="d-flex align-items-center justify-content-center flex-shrink-0"
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '8px',
                backgroundColor: '#f3f4f6',
                fontSize: '24px',
              }}
            >
              {icon}
            </div>
          )}
        </div>
      </Card.Body>
    </Card>
  );
}
