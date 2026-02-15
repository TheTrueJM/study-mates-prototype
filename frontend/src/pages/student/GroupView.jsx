// GroupView - Student sees their assigned group members

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import { getSocket } from '../../socket';

function GroupView() {
  const [username, setUsername] = useState('');
  const [groupNumber, setGroupNumber] = useState(null);
  const [groupMembers, setGroupMembers] = useState([]);
  const [tutorialName, setTutorialName] = useState('');
  const [state, setState] = useState('');
  const [timerRemaining, setTimerRemaining] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const socket = getSocket();

    const onStudentUpdate = (tutorial) => {
      if (!tutorial) return;
      setUsername(tutorial.username || '');
      setGroupNumber(tutorial.group_number);
      setGroupMembers(tutorial.group_members || []);
      setTutorialName(tutorial.name || '');
      setState(tutorial.state || '');

      if (tutorial.state === 'lobby') {
        navigate('/waiting');
      } else if (tutorial.state === 'discussion') {
        navigate('/group');
      }

      if (tutorial.timer) {
        setTimerRemaining(tutorial.timer.remaining || 0);
      }
    };

    const onTimerSync = (data) => {
      setTimerRemaining(data.remaining || 0);
    };

    const onTimerNotification = (data) => {
      if (data && data.message) alert(data.message);
    };

    socket.on('student_update', onStudentUpdate);
    socket.on('timer_sync', onTimerSync);
    socket.on('timer_notification', onTimerNotification);

    return () => {
      socket.off('student_update', onStudentUpdate);
      socket.off('timer_sync', onTimerSync);
      socket.off('timer_notification', onTimerNotification);
    };
  }, [navigate]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="container container-md mt-lg">
      <Card title={tutorialName || 'Tutorial Session'}>
        <div className="card-subtitle">Group {groupNumber}</div>

        {state === 'discussion' && (
          <div className="timer-display mb-md">
            <div className="timer-value">{formatTime(timerRemaining)}</div>
            <div className="timer-status">Discussion time remaining</div>
          </div>
        )}

        <div className="flex-col gap-xs" style={{ display: 'flex' }}>
          {groupMembers.map((member) => (
            <div key={member} className="member-card">
              <div className="member-name">{member}</div>
            </div>
          ))}
        </div>

        <div className="divider mt-md">
          <p style={{ fontSize: '0.875rem', color: '#888' }}>
            Discuss and exchange contact information with your group members
          </p>
        </div>
      </Card>
    </div>
  );
}

export default GroupView;
