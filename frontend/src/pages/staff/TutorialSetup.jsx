// TutorialSetup - Staff configures group size and discussion time before starting

import { useState, useEffect } from 'react';
import { useNavigate } from "react-router-dom";
import Card from '../../components/Card';
import Input from '../../components/Input';
import Button from '../../components/Button';
import { getStaffSocket } from '../../socket';

function TutorialSetup() {
  const [socketInstance, setSocketInstance] = useState(null);
  const [name, setName] = useState("");
  const [groupSize, setGroupSize] = useState(6);
  const [discussionTime, setDiscussionTime] = useState(10);
  const navigate = useNavigate();

  useEffect(() => {
    const socket = getStaffSocket();
    setSocketInstance(socket);

    const onTutorialCreated = (data) => {
      console.log("Tutorial created with code:", data.code);
      navigate(`/staff/tutorial/${data.code}`);
    };

    const onSession = (data) => {
      if (data && data.tutorial) {
        navigate(`/staff/tutorial/${data.tutorial}`);
      }
    };

    socket.on("tutorial_created", onTutorialCreated);
    socket.on("session", onSession);

    return () => {
      socket.off("tutorial_created", onTutorialCreated);
      socket.off("session", onSession);
    };
  }, [navigate]);

  const handleBegin = (e) => {
    e.preventDefault();
    if (!socketInstance) return;

    socketInstance.emit("create_tutorial", {
      name: name,
      group_size: groupSize,
      discussion_time: discussionTime,
    });
  };

  return (
    <div className="container container-md mt-lg">
      <Card title="Tutorial Session Setup">

        {/* Tutorial Name input */}
        <Input
          label="Enter Tutorial Name"
          onChange={setName}
          placeholder="Tutorial Name..."
        />

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
          value={discussionTime}
          onChange={setDiscussionTime}
          placeholder="10..."
        />

        <div className="mt-md">
          <Button variant="secondary" fullWidth onClick={handleBegin}>
            Begin Tutorial Session
          </Button>
        </div>

      </Card>
    </div>
  );
}

export default TutorialSetup;
