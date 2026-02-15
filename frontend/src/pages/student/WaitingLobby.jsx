// WaitingLobby - Student waits here while tutor forms groups

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import { getSocket } from '../../socket';

function WaitingLobby() {
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const socket = getSocket();

    socket.emit('fetch_tutorial');

    const onStudentUpdate = (payload) => {
      if (!payload) {
        return;
      }
      setUsername(payload.username || '');

      if (payload.state === 'groups') {
        navigate('/group');
      }
    };

    socket.on('student_update', onStudentUpdate);

    return () => {
      socket.off('student_update', onStudentUpdate);
    };
  }, [navigate]);

  return (
    <div className="container container-sm mt-lg">
      <Card>
        <div className="text-center">

          {/* Username display */}
          <div className="stat-box mb-md">
            <div className="stat-label">Your Username</div>
            <div className="stat-value" style={{ fontSize: '1.25rem' }}>
              {username}
            </div>
          </div>

          {/* Waiting message + loading animation */}
          <div className="mb-md" style={{ padding: '2rem 0' }}>
            <h2 style={{ color: 'var(--color-primary)', marginBottom: '1rem' }}>
              Waiting for group formation...
            </h2>

            <div className="loading-dots mb-md">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>

          <div className="divider">
            <p style={{ fontSize: '0.875rem', color: '#888' }}>
              Please wait while the tutor forms discussion groups
            </p>
          </div>

        </div>
      </Card>
    </div>
  );
}

export default WaitingLobby;
