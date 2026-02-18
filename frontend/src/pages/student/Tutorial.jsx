import { useEffect, useState } from 'react';
import Card from '../../components/Card';
import { getSocket } from '../../socket';
import LobbyLayout from './LobbyLayout';
import GroupLayout from './GroupLayout';

function Tutorial() {
  // const { code } = useParams();

  const [username, setUsername] = useState('Unknown');

  const [tutorialCode, setTutorialCode] = useState('');
  const [tutorialState, setTutorialState] = useState('lobby');
  const [tutorialName, setTutorialName] = useState('QUT Tutorial');

  const [groupNumber, setGroupNumber] = useState(null);
  const [groupMembers, setGroupMembers] = useState([]);
  const [questions, setQuestions] = useState([]);

  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const socket = getSocket();

    socket.emit('fetch_tutorial');

    const onStudentUpdate = (tutorial) => {
      if (!tutorial) return;

      setUsername(tutorial.username || 'Unknown');

      setTutorialCode(tutorial.tutorial_code || '');
      setTutorialState(tutorial.state || 'lobby');
      setTutorialName(`${tutorial.name || 'QUT Tutorial'}${tutorialCode ? ` - ${tutorialCode}` : ''}`);

      setGroupNumber(tutorial.group_number || null);
      setGroupMembers(tutorial.group_members || []);

      setQuestions(tutorial.questions || []);

      if (tutorial.timer) {
        setTimeRemaining(tutorial.timer.remaining || 0);
        setIsRunning(!!tutorial.timer.running);
      }
    };

    const onTimerSync = (data) => {
      setTimeRemaining(data.remaining || 0);
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
  }, []);

  return (
    <div className="container container-sm mt-lg">
      <Card title={tutorialName}>
        {/* tutorial components split across separate files */}
        {tutorialState === 'lobby' && <LobbyLayout username={username} />}
        {(tutorialState === 'groups' ||tutorialState === 'discussion') && (
          <GroupLayout
            state={tutorialState}
            username={username}
            groupNumber={groupNumber}
            groupMembers={groupMembers}
            questions={questions}
            timeRemaining={timeRemaining}
            isRunning={isRunning}
          />
        )}
      </Card>
    </div>
  );
}

export default Tutorial;
