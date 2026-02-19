import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';

function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="container container-md mt-lg">
      <div className="card">
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: '4rem', margin: '0.5rem 0' }}>404</h1>
          <h2 style={{ margin: '1rem 0' }}>Page Not Found</h2>
          <p style={{ color: '#666', marginBottom: '2rem' }}>
            Sorry, the page you're looking for doesn't exist.
          </p>
          <Button variant="primary" onClick={() => navigate('/')}>
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
