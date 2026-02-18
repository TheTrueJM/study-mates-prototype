// SessionLobby - Staff sees join code and students joining in real-time
// TODO: Replace dummy data with real-time socket.io updates

import Card from '../../components/Card';
import Button from '../../components/Button';

function SessionLobby() {
  // Placeholder data (will come from backend via socket.io)
  const joinCode = 'ABCD-1234';
  // Stress-test: 30 students
  const students = Array.from({ length: 30 }, (_, i) =>
    `Unknown-Student-${String(i + 1).padStart(2, '0')}`
  );

  const handleBeginGrouping = () => {
    console.log('Begin group forming round');
    // TODO: Call API -> navigate to /staff/groups
  };

  return (
    <div className="page">
      <div className="container container-lg">
      <Card title="Session Lobby">

        {/* Join code + QR code area */}
        <div className="mb-sm">
          <label className="input-label">Join Code</label>
          <div className="flex gap-md">
            <div className="join-code">
              <div className="code-value">{joinCode}</div>
            </div>
            <div className="qr-placeholder">[QR CODE]</div>
          </div>
        </div>

        {/* Joined students grid */}
        <div className="mb-sm">
          <div className="input-label">Students Joined: {students.length}</div>
          <div className="grid grid-responsive">
            {students.map((student) => (
              <div key={student} className="student-chip">
                {student}
              </div>
            ))}
          </div>
        </div>

        <Button variant="secondary" fullWidth onClick={handleBeginGrouping}>
          Begin Group Forming Round
        </Button>

      </Card>
      </div>
    </div>
  );
}

export default SessionLobby;
