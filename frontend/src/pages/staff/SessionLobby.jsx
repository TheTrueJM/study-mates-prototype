// SessionLobby - Staff sees join code and students joining in real-time
// TODO: Replace dummy data with real-time socket.io updates

import Card from '../../components/Card';
import Button from '../../components/Button';

function SessionLobby() {
  // Placeholder data (will come from backend via socket.io)
  const joinCode = 'ABCD-1234';
  const students = [
    'Anonymous-Wombat-42',
    'Random-Koala-17',
    'Mystery-Dolphin-89',
    'Unknown-Eagle-23',
    'Silent-Tiger-56',
    'Hidden-Panda-91',
    'Secret-Fox-34',
    'Quiet-Bear-78',
    'Private-Owl-12',
    'Masked-Wolf-45',
    'Veiled-Deer-67',
    'Unseen-Hawk-29',
  ];

  const handleBeginGrouping = () => {
    console.log('Begin group forming round');
    // TODO: Call API -> navigate to /staff/groups
  };

  return (
    <div className="page">
      <div className="container container-lg">
      <Card title="Session Lobby">

        {/* Join code + QR code area */}
        <div className="mb-lg">
          <label className="input-label">Join Code</label>
          <div className="flex gap-md">
            <div className="join-code">
              <div className="code-value">{joinCode}</div>
            </div>
            <div className="qr-placeholder">[QR CODE]</div>
          </div>
        </div>

        {/* Joined students grid */}
        <div className="mb-md">
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
