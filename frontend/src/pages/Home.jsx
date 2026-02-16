// Home - Landing page where users choose Student or Staff entry

import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';

function Home() {
  const navigate = useNavigate();

  return (
    <div className="page-center">
      <div className="container container-sm">
      <Card title="Study Mates">
        <p className="mb-md" style={{ color: '#888' }}>
          Select how you want to join the tutorial session.
        </p>

        <div className="flex-col gap-sm" style={{ display: 'flex' }}>
          <Button variant="primary" fullWidth onClick={() => navigate('/student/join')}>
            Join as Student
          </Button>
          <Button variant="secondary" fullWidth onClick={() => navigate('/staff/setup')}>
            Staff Login
          </Button>
        </div>
      </Card>
      </div>
    </div>
  );
}

export default Home;
