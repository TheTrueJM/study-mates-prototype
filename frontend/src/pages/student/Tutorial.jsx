import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { getSocket } from '../../socket';
import { useAuth } from '../../hooks/useAuth';
import LobbyLayout from './LobbyLayout';
import GroupLayout from './GroupLayout';

function Tutorial() {
  const [socketInstance, setSocketInstance] = useState(null);
  const navigate = useNavigate();
  const { setStudent } = useAuth();

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
    console.log("[FRONTEND DEBUG] Tutorial component mounted");
    const socket = getSocket();
    setSocketInstance(socket);

    const tutorialCode = localStorage.getItem("tutorial_code");
    console.log("[FRONTEND DEBUG] tutorialCode from localStorage:", tutorialCode);
    if (tutorialCode) {
      console.log("[FRONTEND DEBUG] Emitting join_tutorial with code:", tutorialCode);
      socket.emit("join_tutorial", { code: tutorialCode });
    } else {
      console.log("[FRONTEND DEBUG] Emitting fetch_tutorial");
      socket.emit("fetch_tutorial");
    }

    const onStudentUpdate = (tutorial) => {
      if (!tutorial) return;

      console.log("[FRONTEND DEBUG] student_update received:", JSON.stringify(tutorial, null, 2));

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

    const onTutorialEnded = () => {
      localStorage.removeItem("tutorial_code");
      setStudent(null);
      navigate("/");
    };

    const onSessionCleared = () => {
      localStorage.removeItem("tutorial_code");
      setStudent(null);
      navigate("/");
    };

    const onError = (err) => {
      if (err && err.message) {
        localStorage.removeItem("tutorial_code");
        setStudent(null);
        navigate("/");
      }
    };

    socket.on('student_update', onStudentUpdate);
    socket.on('timer_sync', onTimerSync);
    socket.on('timer_notification', onTimerNotification);
    socket.on('tutorial_ended', onTutorialEnded);
    socket.on('session_cleared', onSessionCleared);
    socket.on('error', onError);

    return () => {
      socket.off('student_update', onStudentUpdate);
      socket.off('timer_sync', onTimerSync);
      socket.off('timer_notification', onTimerNotification);
      socket.off('tutorial_ended', onTutorialEnded);
      socket.off('session_cleared', onSessionCleared);
      socket.off('error', onError);
    };
  }, [navigate, tutorialCode]);

  const handleLeave = () => {
    socketInstance.emit("reset_session");
  };

  return (
    <div className="container container-sm mt-lg">
      <Card
        title={tutorialName}
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button variant="outline" onClick={handleLeave}>Leave Tutorial</Button>
          </div>
        }
      >
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
