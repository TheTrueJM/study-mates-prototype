import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";

import Card from "../../components/Card";
import Button from "../../components/Button";
import NumberInput from "../../components/NumberInput";
import SliderInput from "../../components/SliderInput";
// import DropdownInput from "../../components/DropdownInput";
import CheckboxInput from "../../components/CheckboxInput";
import Modal from "../../components/Modal";

import LobbyLayout from "./LobbyLayout";
import GroupsLayout from "./GroupsLayout";
import DiscussionLayout from "./DiscussionLayout";


function Tutorial() {
  const navigate = useNavigate();
  const { code } = useParams();

  const [groupSizeSetting, setGroupSizeSetting] = useState(5);
  const [maxGroupsSetting, setMaxGroupsSetting] = useState("");
  const [discussionTimeSetting, setDiscussionTimeSetting] = useState(5);
  const [availableAttributesSetting, setAvailableAttributesSetting] = useState([]);

  const [enableMaxGroups, setEnableMaxGroups] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  const {
    tutorialCode, tutorialName, tutorialState, groupSize, maxGroups, availableAttributes,
    students, groups, questions, timeDuration, timeRemaining, timeRunning,
    updateTutorial, backToLobby, startGrouping, startDiscussion, endTutorial,
    startTimer, stopTimer, resetTimer
  } = useTutorial();


  useEffect(() => {
    // TODO: Handle Errors and Navigation
    if (!tutorialCode) {
      navigate("/staff/");
    } else if (tutorialCode != code) {
      navigate(`/staff/tutorial/${tutorialCode}`);
    }

    setGroupSizeSetting(groupSize);
    setMaxGroupsSetting(maxGroups);
    setEnableMaxGroups(!!maxGroups)
    setDiscussionTimeSetting(timeDuration / 60);
    setAvailableAttributesSetting(availableAttributes)
  }, [code, navigate]);


  // Tutorial State Handling
  const handleLobby = () => backToLobby();
  const handleGrouping = () => startGrouping();
  const handleDiscussion = () => startDiscussion();
  const handleClose = () => {
    if (confirm("Are you sure you want to close this Tutorial?")) {
      endTutorial();
    }
  };
  const handleTimerStart = () => startTimer();
  const handleTimerStop = () => stopTimer();


  const handleUpdateSettings = (event) => {
    event.preventDefault();

    const iGroupSize = parseFloat(groupSizeSetting);
    const iMaxGroups = parseFloat(maxGroupsSetting);
    const fDiscussionTime = parseFloat(discussionTimeSetting);

    // TODO: Improve Feedback Approach (take from SetupTutorial)
    if (!Number.isInteger(iGroupSize) || iGroupSize < 2 || iGroupSize > 10) {
      alert("Please enter a valid group size (between 2 and 10 students).");
      return;
    }

    if (enableMaxGroups && !Number.isInteger(iMaxGroups) || iMaxGroups < 2) {
      alert("Please enter a valid maximum groups (at least 2 groups).");
      return;
    }

    if (isNaN(fDiscussionTime) || fDiscussionTime < 1 || fDiscussionTime > 60) {
      alert("Please enter a valid discussion time (between 1 and 60 minutes).");
      return;
    }

    updateTutorial({
      group_size: iGroupSize,
      max_groups: enableMaxGroups ? iMaxGroups : null,
      discussion_time: fDiscussionTime,
      available_attributes: availableAttributes
    });

    setShowSettingsModal(false);
  };


  return (
    <div className="container container-lg mt-lg">
      <Card
        title={`${tutorialName} (${tutorialState})`}
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button variant="outline" onClick={() => setShowSettingsModal(true)}>Tutorial Settings</Button>
            {(tutorialState !== "lobby") && (
              <Button onClick={handleLobby}>Back to Lobby</Button>
            )}
          </div>
        }
      >
        {/* tutorial components split across separate files */}
        {tutorialState === "lobby" && (
          <LobbyLayout
            code={code}
            students={students}
            onGrouping={handleGrouping}
          />
        )}
        {tutorialState === "grouping" && (
          <GroupsLayout
            code={code}
            students={students}
            groups={groups}
            onGrouping={handleGrouping}
            onDiscussion={handleDiscussion}
          />
        )}
        {tutorialState === "discussion" && (
          <DiscussionLayout
            code={code}
            questions={questions}
            timeRemaining={timeRemaining}
            timeRunning={timeRunning}
            onGrouping={handleGrouping}
            onStartTimer={handleTimerStart}
            onStopTimer={handleTimerStop}
          />
        )}
      </Card>


      <Modal title="Tutorial Session Settings" isOpen={showSettingsModal} onClose={() => setShowSettingsModal(false)}>
        {/* Student Group Size Slider (2-10) */}
        <SliderInput
          name="group-size"
          label="Students per Group"
          value={groupSizeSetting}
          min={2}
          max={10}
          onChange={setGroupSizeSetting}
        />

        {/* Maximum Student Groups Input */}
        <NumberInput
          name="max-groups"
          label="Maximum Groups of Students"
          value={maxGroups}
          min={2}
          placeholder="8..."
          onChange={setMaxGroupsSetting}
          disabled={!enableMaxGroups}
        />
        <CheckboxInput
          name="max-groups-checkbox"
          label="Enable Maximum Groups"
          value={enableMaxGroups}
          onChange={setEnableMaxGroups}
        />

        {/* Discussion Time Input */}
        <NumberInput
          name="discussion-time"
          label="Discussion Time (minutes)"
          value={discussionTimeSetting}
          min={1}
          max={60}
          placeholder="5..."
          onChange={setDiscussionTimeSetting}
        />

        {/* Student Attributes Selection */}
        {/* TODO: Include and Improve Selection Menu and Input Type */}
        {/* <DropdownInput
          name="student-attributes"
          label="Available Student Attributes"
          value={availableAttributes}
          options={studentAttributeOptions}
          placeholder="Select Multiple Attributes"
          onChange={setAvailableAttributes}
          multiple={true}
        /> */}

        {/* Action buttons */}
        <div className="btn-group">
          <Button variant="outline" onClick={handleClose}>Close Tutorial</Button>
          <Button variant="primary" onClick={handleUpdateSettings}>Update Settings</Button>
        </div>
      </Modal>
    </div>
  );
}

export default Tutorial;
