// SessionLobby - Staff sees join code and students joining in real-time
// TODO: Replace dummy data with real-time socket.io updates

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { getStaffSocket } from '../../socket';

function SessionLobby() {
  const { code } = useParams();
  const navigate = useNavigate();

  const [joinCode, setJoinCode] = useState(code || '');
  const [students, setStudents] = useState([]);
  const [tutorialName, setTutorialName] = useState('');

  useEffect(() => {
    const socket = getStaffSocket();

    socket.emit('fetch_tutorial');

    const onUpdate = (tutorial) => {
      if (!tutorial) {
        return;
      }
      setJoinCode(tutorial.tutorial_code || code);
      setTutorialName(`${tutorial.name || 'Tutorial'} - Lobby`);
      setStudents(Object.values(tutorial.students || {}).map(s => s.name));

      if (tutorial.state === 'groups') {
        navigate('/staff/groups');
      }
      if (tutorial.state === 'discussion') {
        navigate('/staff/discussion');
      }
    };

    socket.on('tutorial_update', onUpdate);

    return () => {
      socket.off('tutorial_update', onUpdate);
    };
  }, [code, navigate]);

  const handleBeginGrouping = () => {
    const socket = getStaffSocket();
    socket.emit('start_grouping');
  };

  return (
    <div className="container container-lg mt-lg">
      <Card title={tutorialName}>

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
          Begin Group Formation
        </Button>

      </Card>
    </div>
  );
}

export default SessionLobby;
