export default function LobbyLayout({ username }) {
  return (
    <>
        <div className="text-center">
          {/* Username display */}
          <div className="stat-box mb-md">
            <div className="stat-label">Your Username</div>
            <div className="stat-value" style={{ fontSize: '1.25rem' }}>
              {username}
            </div>
          </div>

          {/* Waiting messages and loading animation */}
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
              Please wait until the Tutor forms the Discussion Groups
            </p>
          </div>
        </div>
    </>
  );
}
