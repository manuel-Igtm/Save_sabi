import { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Card, Form, Button, Spinner } from 'react-bootstrap';
import { WalletContext } from '../context/WalletContext';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useContext(WalletContext);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    setTimeout(() => {
      login(email);
      setLoading(false);
      navigate('/dashboard');
    }, 800);
  };

  const handleDemoLogin = () => {
    setLoading(true);
    setTimeout(() => {
      login('demo@savesabi.com');
      setLoading(false);
      navigate('/dashboard');
    }, 800);
  };

  return (
    <Container
      fluid
      className="d-flex align-items-center justify-content-center vh-100"
      style={{ backgroundColor: '#f8f9fa' }}
    >
      <Card
        className="shadow p-5"
        style={{ maxWidth: '420px', width: '100%', borderRadius: '16px', border: '1px solid #e5e7eb' }}
      >
        {/* Header */}
        <div className="text-center mb-4">
          <div
            className="d-flex align-items-center justify-content-center mx-auto mb-3"
            style={{
              width: '56px',
              height: '56px',
              backgroundColor: '#22c55e',
              borderRadius: '12px',
              color: 'white',
              fontSize: '28px',
              fontWeight: 'bold',
            }}
          >
            💰
          </div>
          <h1 className="h2 fw-bold text-dark mb-1">Save Sabi</h1>
          <p className="text-muted small mb-0">Save smart. Spend wise.</p>
        </div>

        {/* Form */}
        <Form onSubmit={handleLogin}>
          <Form.Group className="mb-3">
            <Form.Label className="text-dark fw-semibold small mb-2">Email Address</Form.Label>
            <Form.Control
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              style={{ borderRadius: '8px', padding: '10px 12px', fontSize: '14px' }}
            />
          </Form.Group>

          <Button
            type="submit"
            disabled={!email || loading}
            className="w-100 fw-semibold mb-3"
            style={{
              backgroundColor: '#22c55e',
              borderColor: '#22c55e',
              borderRadius: '8px',
              padding: '10px',
              fontSize: '14px',
              border: 'none',
            }}
          >
            {loading ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
        </Form>

        {/* Divider */}
        <div className="d-flex align-items-center gap-2 mb-3">
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e5e7eb' }} />
          <span className="text-muted small">or</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e5e7eb' }} />
        </div>

        {/* Demo Button */}
        <Button
          variant="outline-secondary"
          onClick={handleDemoLogin}
          disabled={loading}
          className="w-100 fw-semibold mb-4"
          style={{
            borderRadius: '8px',
            padding: '10px',
            fontSize: '14px',
            borderColor: '#22c55e',
            color: '#22c55e',
            backgroundColor: 'transparent',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f0fdf4';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          Continue as Demo
        </Button>

        {/* Footer notice */}
        <p className="text-center text-muted small mb-0">
          💡 No account needed! Sign in with any email to get started.
        </p>
      </Card>
    </Container>
  );
}
