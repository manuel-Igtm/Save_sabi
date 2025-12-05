import { Alert } from 'react-bootstrap';

export default function AlertBanner({ alerts }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="d-flex flex-column gap-3">
      {alerts.map((alert, index) => (
        <Alert
          key={index}
          variant="warning"
          className="d-flex gap-3 align-items-start mb-0"
          style={{ borderRadius: '12px', border: '1px solid #fcd34d' }}
        >
          <div style={{ fontSize: '24px', flexShrink: 0 }}>⚠️</div>
          <div className="flex-grow-1">
            <p className="mb-1 fw-semibold" style={{ fontSize: '14px', color: '#92400e' }}>
              {alert}
            </p>
            <p className="text-muted small mb-0">We recommend reviewing your recent transactions.</p>
          </div>
          <div className="text-muted small" style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>
            Just now
          </div>
        </Alert>
      ))}
    </div>
  );
}
