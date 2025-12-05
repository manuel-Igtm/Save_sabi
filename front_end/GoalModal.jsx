import { useState } from 'react';
import { Modal, Form, Button } from 'react-bootstrap';

export default function GoalModal({ isOpen, onClose, onSave, currentGoal }) {
  const [goal, setGoal] = useState(currentGoal || '');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!goal) return;
    onSave(parseFloat(goal));
    setGoal('');
    onClose();
  };

  return (
    <Modal show={isOpen} onHide={onClose} centered size="sm">
      <Modal.Header closeButton className="border-0">
        <Modal.Title className="fw-bold">Set Savings Goal</Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <p className="text-muted small mb-3">
          Define your target savings amount. The progress bar will show how close you are.
        </p>

        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold small">Target Goal Amount (KES)</Form.Label>
            <Form.Control
              type="number"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g., 50000"
              autoFocus
              style={{ borderRadius: '8px', padding: '10px 12px' }}
            />
          </Form.Group>

          <div className="p-3 mb-3 rounded" style={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb' }}>
            <p className="text-muted small fw-semibold mb-2">Goal Preview:</p>
            <p className="fw-bold mb-0" style={{ fontSize: '18px', color: '#22c55e' }}>
              {goal ? `KES ${parseFloat(goal).toLocaleString()}` : '—'}
            </p>
          </div>

          <div className="d-flex gap-2">
            <Button
              variant="light"
              onClick={onClose}
              className="flex-grow-1"
              style={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!goal}
              className="flex-grow-1 fw-semibold"
              style={{
                backgroundColor: '#22c55e',
                borderColor: '#22c55e',
                borderRadius: '8px',
                border: 'none',
              }}
            >
              Save Goal
            </Button>
          </div>
        </Form>
      </Modal.Body>
    </Modal>
  );
}
