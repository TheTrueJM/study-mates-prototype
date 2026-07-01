import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../../components/Button";
import NumberInput from "../../components/NumberInput";


export default function LobbyLayout({ code, username, attributes, sharedAttributes, attributesComplete, availableAttributes, updateDetails, confirmDetails }) {
  const navigate = useNavigate();
  
  const [currentGPA, setCurrentGPA] = useState("");
  const [goalGrade, setGoalGrade] = useState("");
  const [availability, setAvailability] = useState([]);
  const [communication, setCommunication] = useState([]);
  const [meetingMode, setMeetingMode] = useState("");
  const [year, setYear] = useState("");
  const [semester, setSemester] = useState("");
  const [accessibility, setAccessibility] = useState(false);

  const [sharingAttributes, setSharingAttributes] = useState([]);

  const [displayAttributes, setDisplayAttributes] = useState(false);

  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const TIMES = ["Morning", "Afternoon", "Evening"];


  useEffect(() => {
    setCurrentGPA(attributes.current_gpa);
    setGoalGrade(attributes.goal_grade);
    setAvailability(attributes.availability || []);
    setCommunication(attributes.communication || []);
    setMeetingMode(attributes.meeting_mode);
    setYear(attributes.year);
    setSemester(attributes.semester);
    setAccessibility(attributes.accessibility || false);
    
    setSharingAttributes(sharedAttributes || []);

    setDisplayAttributes(attributesComplete || false);
  }, [code, navigate]);


  const handleCurrentGPA = (event) => {
    event.preventDefault();
    // TODO: Prevalidate
    setCurrentGPA(event.target.value);
    updateDetails({current_gpa: currentGPA}); // TODO: Might just need to use event.target.value for these
  }

  const handleGoalGrade = (event) => {
    event.preventDefault();
    setGoalGrade(event.target.value);
    updateDetails({goal_grade: goalGrade});
  }

  const handleConfirm = (event) => {
    event.preventDefault();
    updateDetails({
      current_gpa: currentGPA,
      goal_grade: goalGrade
    });
  }


  return (
    <>
      <div className="text-center">
        {/* Username display */}
        <div className="stat-box mb-md">
          <div className="stat-label">Your Username</div>
          <div className="stat-value" style={{ fontSize: "1.25rem" }}>
            {username}
          </div>
        </div>

        {(!attributesComplete || displayAttributes) ? (
          <>
            {/* Student Details Input */}
            <div className="mb-md" style={{ padding: "2rem 0" }}>
              <h2 style={{ color: "var(--color-primary)", marginBottom: "1rem" }}>
                Enter Details for Group Formation
              </h2>

              {/* TODO: Update to Dropdown Selection (P, C, D, HD) */}
              <NumberInput
                label="Current GPA"
                type="number"
                value={currentGPA}
                min={0}
                max={7}
                step={0.1}
                onChange={handleCurrentGPA}
                placeholder="e.g. 4.0"
              />

              {/* TODO: Update to Dropdown Selection (P, C, D, HD) */}
              <NumberInput
                label="Goal Unit Grade"
                type="number"
                value={goalGrade}
                min={0}
                max={7}
                step={0.1}
                onChange={handleGoalGrade}
                placeholder="e.g. 4.0"
              />
            </div>

            <div className="divider">
              <Button variant="primary" fullWidth onClick={handleConfirm}>
                Confirm Details
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* Waiting Messages and Loading Animation */}
            <div className="mb-md" style={{ padding: "2rem 0" }}>
              <h2 style={{ color: "var(--color-primary)", marginBottom: "1rem" }}>
                Waiting for group formation...
              </h2>

              <div className="loading-dots mb-md">
                <div className="dot" />
                <div className="dot" />
                <div className="dot" />
              </div>
            </div>

            <div className="divider">
              <p style={{ fontSize: "0.875rem", color: "#888" }}>
                Please wait until the Tutor forms the Discussion Groups
              </p>
            </div>
          </>
        )}
      </div>
    </>
  );
}
