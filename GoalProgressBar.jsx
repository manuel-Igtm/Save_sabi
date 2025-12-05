import { Card, ProgressBar, Badge } from 'react-bootstrap';

export default function GoalProgressBar({ saved = 0, goal = 1 }) {
  const percentage = Math.min(Math.round((saved / goal) * 100), 100);

  return (
    <Card className="shadow-sm" style={{ borderRadius: '12px', border: '1px solid #e5e7eb' }}>
      <Card.Body className="p-4">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <div>
            <p className="mb-1 fw-semibold" style={{ fontSize: '16px', color: '#374151' }}>
              Savings Goal
            </p>
            <p className="text-muted small mb-0">{percentage}% complete</p>
          </div>
          <Badge bg="success" style={{ borderRadius: '9999px', padding: '6px 12px', fontSize: '12px' }}>
            {percentage}%
          </Badge>
        </div>

        <ProgressBar
          now={percentage}
          style={{
            height: '12px',
            borderRadius: '9999px',
            backgroundColor: '#e5e7eb',
          }}
          className="mb-3"
        />

        <div className="d-flex align-items-center justify-content-between">
          <p className="text-muted small mb-0">
            KES {Number(saved).toLocaleString()}
          </p>
          <p className="text-muted small mb-0">
            Target: KES {Number(goal).toLocaleString()}
          </p>
        </div>
      </Card.Body>
    </Card>
  );
}
