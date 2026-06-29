import { useState, useEffect } from 'react';
import { useNavigate } from "react-router-dom";

import { useTutorial } from '../../contexts/TutorialContext';

import Card from '../../components/Card';
import Button from '../../components/Button';
import TextInput from '../../components/TextInput';
import NumberInput from '../../components/NumberInput';
import SliderInput from '../../components/SliderInput';
import DropdownInput from '../../components/DropdownInput';
import CheckboxInput from '../../components/CheckboxInput';


function TutorialSetup() {
  const { createTutorial } = useTutorial();

  const [name, setName] = useState("");
  const [groupSize, setGroupSize] = useState(5);
  const [maxGroups, setMaxGroups] = useState("");
  const [discussionTime, setDiscussionTime] = useState(5);
  const [availableAttributes, setAvailableAttributes] = useState([]);

  const [enableMaxGroups, setEnableMaxGroups] = useState(false);

  const studentAttributeOptions = [
    {value: "current_gpa", label: "Current GPA"},
    {value: "goal_grade", label: "Goal Grade"},
    {value: "availability", label: "Availability"},
    {value: "communication", label: "Communication Methods"},
    {value: "meeting_mode", label: "Prefered Meeting Modes"},
    {value: "year", label: "Study Year"},
    {value: "semester", label: "Study Semester"},
    // {value: "accessibility", label: "Accessibility"}
  ];


  useEffect(() => {
    setAvailableAttributes(["current_gpa", "goal_grade", "availability", "communication"]);
  }, [])


  const handleBegin = (event) => {
    event.preventDefault();

    const iGroupSize = parseFloat(groupSize);
    const iMaxGroups = parseFloat(maxGroups);
    const fDiscussionTime = parseFloat(groupSize);

    // TODO: Improve Feedback Approach
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

    createTutorial({
      tutorial_name: name,
      group_size: iGroupSize,
      max_groups: enableMaxGroups ? iMaxGroups : null,
      discussion_time: fDiscussionTime,
    });
  };


  return (
    <div className="container container-md mt-lg">
      <Card title="Tutorial Session Setup">

        {/* Tutorial Name Input */}
        <TextInput
          name="name"
          label="Enter Tutorial Name"
          value={name}
          placeholder="Name..."
          onChange={setName}
        />

        {/* Student Group Size Slider (2-10) */}
        <SliderInput
          name="group-size"
          label="Students per Group"
          value={groupSize}
          min={2}
          max={10}
          onChange={setGroupSize}
        />

        {/* Maximum Student Groups Input */}
        <NumberInput
          name="max-groups"
          label="Maximum Groups of Students"
          value={maxGroups}
          min={2}
          placeholder="8..."
          onChange={setMaxGroups}
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
          value={discussionTime}
          min={1}
          max={60}
          placeholder="5..."
          onChange={setDiscussionTime}
        />

        {/* Student Attributes Selection */}
        <DropdownInput
          name="student-attributes"
          label="Available Student Attributes"
          value={availableAttributes}
          options={studentAttributeOptions}
          placeholder="Select Multiple Attributes"
          onChange={setAvailableAttributes}
          multiple={true}
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
