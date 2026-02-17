// Tutorial - Staff can handle tutorial actions, across lobby, grouping and discussion states
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { getStaffSocket } from '../../socket';
import LobbyLayout from './LobbyLayout';
import GroupsLayout from './GroupsLayout';
import DiscussionLayout from './DiscussionLayout';

function Tutorial() {
  const { code } = useParams();

  const [socketInstance, setSocketInstance] = useState(null);

  const [tutorialCode, setTutorialCode] = useState(code || '');
  const [tutorialState, setTutorialState] = useState('lobby');
  const [tutorialName, setTutorialName] = useState('QUT Tutorial');

  const [students, setStudents] = useState({});
  const [groups, setGroups] = useState([]);
  const [questions, setQuestions] = useState([]);

  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [resetTime, setResetTime] = useState(10);

  useEffect(() => {
    const socket = getStaffSocket();
    setSocketInstance(socket);

    socket.emit('fetch_tutorial');

    const onUpdate = (tutorial) => {
      if (!tutorial) return;

      setTutorialCode(tutorial.tutorial_code || code || '');
      setTutorialState(tutorial.state || 'lobby');
      setTutorialName(`${tutorial.name || 'QUT Tutorial'}${tutorialCode ? ` - ${tutorialCode}` : ''}`);

      setStudents(tutorial.students || {});

      const groupList = Object.entries(tutorial.groups || {}).map(([id, members]) => ({ id, members }));
      setGroups(groupList);

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

    socket.on('tutorial_update', onUpdate);
    socket.on('timer_sync', onTimerSync);
    socket.on('timer_notification', onTimerNotification);

    return () => {
      socket.off('tutorial_update', onUpdate);
      socket.off('timer_sync', onTimerSync);
      socket.off('timer_notification', onTimerNotification);
    };
  }, [code]);

  /* socket handlers shared across tutorial states */
  const handleLobby = () => socketInstance.emit('reset_lobby');
  const handleGrouping = () => socketInstance.emit('start_grouping');
  const handleDiscussion = () => socketInstance.emit('start_discussion');

  const handleTimerStart = () => socketInstance.emit('start_timer');
  const handleTimerStop = () => socketInstance.emit('stop_timer');
  const handleTimerReset = () => socketInstance.emit('reset_timer', { time: resetTime });

  return (
    <div className="container container-lg mt-lg">
      <Card title={tutorialName} actions={(
        (tutorialState === 'groups' || tutorialState === 'discussion') ? (
          <Button variant="outline" onClick={handleLobby}>Back to Lobby</Button>
        ) : null
      )}>
        {/* tutorial components split across separate files */}
        {tutorialState === 'lobby' && <LobbyLayout tutorialCode={tutorialCode} students={students} onGrouping={handleGrouping} />}
        {tutorialState === 'groups' && <GroupsLayout groups={groups} students={students} onGrouping={handleGrouping} onDiscussion={handleDiscussion} />}
        {tutorialState === 'discussion' && (
          <DiscussionLayout
            questions={questions}
            timeRemaining={timeRemaining}
            isRunning={isRunning}
            resetTime={resetTime}
            setResetTime={setResetTime}
            onStartTimer={handleTimerStart}
            onStopTimer={handleTimerStop}
            onResetTimer={handleTimerReset}
            onGrouping={handleGrouping}
          />
        )}
      </Card>
    </div>
  );
}

export default Tutorial;
