// Tutorial - Staff can handle tutorial actions, across lobby, grouping and discussion states
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Button from '../../components/Button';
import Card from '../../components/Card';
import Input from '../../components/Input';
import Modal from '../../components/Modal';
import { getStaffSocket } from '../../socket';
import LobbyLayout from './LobbyLayout';
import GroupsLayout from './GroupsLayout';
import DiscussionLayout from './DiscussionLayout';

function Tutorial() {
  const { code } = useParams();
  const navigate = useNavigate();

  const [socketInstance, setSocketInstance] = useState(null);

  const [tutorialCode, setTutorialCode] = useState(code || '');
  const [tutorialState, setTutorialState] = useState('lobby');
  const [tutorialName, setTutorialName] = useState('QUT Tutorial');

  const [groupSize, setGroupSize] = useState(6);

  const [students, setStudents] = useState({});
  const [groups, setGroups] = useState([]);
  const [questions, setQuestions] = useState([]);

  const [timeDuration, setTimeDuration] = useState(5);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const [showSettingsModal, setShowSettingsModal] = useState(false);

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

    const onError = (err) => {
      if (err && err.message) {
        navigate("/staff/");
      }
    };

    const onLeftTutorial = () => {
    };
    const onTutorialDeleted = () => {
      navigate("/staff/");
    };

    socket.on('tutorial_update', onUpdate);
    socket.on('timer_sync', onTimerSync);
    socket.on('timer_notification', onTimerNotification);
    socket.on('error', onError);
    socket.on('left_tutorial', onLeftTutorial);
    socket.on('tutorial_deleted', onTutorialDeleted);

    return () => {
      socket.off('tutorial_update', onUpdate);
      socket.off('timer_sync', onTimerSync);
      socket.off('timer_notification', onTimerNotification);
      socket.off('error', onError);
      socket.off('left_tutorial', onLeftTutorial);
      socket.off('tutorial_deleted', onTutorialDeleted);
    };
  }, [code, navigate]);

  /* socket handlers shared across tutorial states */
  const handleLobby = () => socketInstance.emit('reset_lobby');
  const handleGrouping = () => socketInstance.emit('start_grouping');
  const handleDiscussion = () => socketInstance.emit('start_discussion');
  const handleClose = () => {
    if (confirm("Are you sure you want to close this tutorial?")) {
      socketInstance.emit("leave_tutorial");
      navigate("/staff/");
      socketInstance.emit("delete_tutorial");
    }
  };
  const handleTimerStart = () => socketInstance.emit('start_timer');
  const handleTimerStop = () => socketInstance.emit('stop_timer');

  const handleUpdateSettings = (e) => {
    e.preventDefault();
    if (!socketInstance) return;

    if (!Number.isInteger(parseFloat(groupSize)) || parseFloat(groupSize) < 2 || parseFloat(groupSize) > 10) {
      alert("Please enter a valid group size (between 2 and 10 students).");
      return;
    }

    if (isNaN(parseFloat(timeDuration)) || parseFloat(timeDuration) < 1 || parseFloat(timeDuration) > 60) {
      alert("Please enter a valid discussion time (between 1 and 60 minutes).");
      return;
    }

    socketInstance.emit("update_settings", {
      group_size: groupSize,
      time: timeDuration,
    });

    setShowSettingsModal(false);
  };


  return (
    <div className="container container-lg mt-lg">
      <Card
        title={tutorialName}
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button variant="outline" onClick={() => setShowSettingsModal(true)}>Tutorial Settings</Button>
            {(tutorialState === "groups" || tutorialState === "discussion") && (
              <Button onClick={handleLobby}>
                Back to Lobby
              </Button>
            )}
          </div>
        }
      >
        {/* tutorial components split across separate files */}
        {tutorialState === 'lobby' && <LobbyLayout tutorialCode={tutorialCode} students={students} onGrouping={handleGrouping} />}
        {tutorialState === 'groups' && <GroupsLayout groups={groups} students={students} onGrouping={handleGrouping} onDiscussion={handleDiscussion} />}
        {tutorialState === 'discussion' && (
          <DiscussionLayout
            questions={questions}
            timeRemaining={timeRemaining}
            isRunning={isRunning}
            onStartTimer={handleTimerStart}
            onStopTimer={handleTimerStop}
            onGrouping={handleGrouping}
          />
        )}
      </Card>

      {showSettingsModal && (
        <Modal title="Tutorial Session Settings" onClose={() => setShowSettingsModal(false)}>
          {/* Student group size slider (2-10) */}
          <div className="form-group">
            <label className="input-label">Students per Group</label>
            <div className="range-group">
              <input
                type="range"
                min="2"
                max="10"
                value={groupSize}
                onChange={(e) => setGroupSize(Number(e.target.value))}
              />
              <div className="range-value">{groupSize}</div>
            </div>
            <div className="range-labels">
              <span>2</span>
              <span>10</span>
            </div>
          </div>

          {/* Discussion time input */}
          <Input
            label="Discussion Time (minutes)"
            type="number"
            min="1"
            max="60"
            value={timeDuration}
            onChange={setTimeDuration}
            placeholder="5..."
          />

          {/* Action buttons */}
          <div className="btn-group">
            <Button variant="outline" onClick={handleClose}>Close Tutorial</Button>
            <Button variant="primary" onClick={handleUpdateSettings}>Update Settings</Button>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default Tutorial;
