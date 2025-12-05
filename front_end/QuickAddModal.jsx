import { useState } from 'react';
import { Modal, Form, Button, Container } from 'react-bootstrap';

export default function QuickAddModal({ isOpen, type, onClose, onAdd }) {
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');

  if (!isOpen) return null;

  const isIncome = type === 'income';
  const parsed = parseFloat(amount) || 0;
  const savings = isIncome ? parsed * 0.2 : 0;
  const spendable = isIncome ? parsed * 0.8 : parsed;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!parsed) return;

    const transaction = {
      type,
      amount: parsed,
      note,
      date: new Date().toLocaleString(),
    };

    onAdd(transaction);
    setAmount('');
    setNote('');
    onClose();
  };

  return (
    <Modal show={isOpen} onHide={onClose} centered size="sm">
      <Modal.Header closeButton className="border-0">
        <Modal.Title className="fw-bold">
          {isIncome ? '➕ Add Income' : '➖ Add Expense'}
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold small">Amount (KES)</Form.Label>
            <Form.Control
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0"
              style={{ borderRadius: '8px', padding: '10px 12px' }}
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold small">Note (Optional)</Form.Label>
            <Form.Control
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g., Lunch, Freelance project"
              style={{ borderRadius: '8px', padding: '10px 12px' }}
            />
          </Form.Group>

          {parsed > 0 && (
            <div className="p-3 mb-3 rounded" style={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb' }}>
              <p className="text-muted small fw-semibold mb-2">Preview</p>
              <div className="d-flex align-items-center justify-content-between gap-3">
                <div>
                  <p className="fw-semibold small mb-1" style={{ color: '#22c55e' }}>
                    💰 Savings (20%)
                  </p>
                  <p className="small mb-0">KES {savings.toLocaleString()}</p>
                </div>
                <div>
                  <p className="fw-semibold small mb-1" style={{ color: '#3b82f6' }}>
                    💳 Spendable (80%)
                  </p>
                  <p className="small mb-0">KES {spendable.toLocaleString()}</p>
                </div>
              </div>
            </div>
          )}

          <div className="d-flex gap-2 pt-2">
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
              disabled={!parsed}
              className="flex-grow-1 fw-semibold"
              style={{
                backgroundColor: '#22c55e',
                borderColor: '#22c55e',
                borderRadius: '8px',
                border: 'none',
              }}
            >
              Confirm
            </Button>
          </div>
        </Form>
      </Modal.Body>
    </Modal>
  );
}
