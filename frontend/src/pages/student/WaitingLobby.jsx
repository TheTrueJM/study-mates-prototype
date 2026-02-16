// WaitingLobby - Student waits here while tutor forms groups
// TODO: Replace dummy data with real-time socket.io updates

import Card from '../../components/Card';

function WaitingLobby() {
  // Placeholder data (will come from backend via socket.io)
  const username = 'Anonymous-Wombat-42';
  const studentCount = 12;

  return (
    <div className="page-center">
      <div className="container container-sm">
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

            {/* Student count */}
            <div className="stat-box">
              <div className="stat-label">Students Joined</div>
              <div className="stat-value">{studentCount}</div>
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
    </div>
  );
}

export default WaitingLobby;
