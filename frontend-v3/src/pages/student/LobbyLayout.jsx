import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../../components/Button";
import NumberInput from "../../components/NumberInput";
import DropdownInput from "../../components/DropdownInput";
import CheckboxInput from "../../components/CheckboxInput";


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
  const [shareCurrentGPA, setShareCurrentGPA] = useState(false);
  const [shareGoalGrade, setShareGoalGrade] = useState(false);
  const [shareAvailability, setShareAvailability] = useState(false);
  const [shareCommunication, setShareCommunication] = useState(false);
  const [shareMeetingMode, setShareMeetingMode] = useState(false);

  const [displayAttributes, setDisplayAttributes] = useState(false);

  const gradeOptions = [
    {value: 4, label: "Pass (4)"},
    {value: 5, label: "Credit (5)"},
    {value: 6, label: "Distinction (6)"},
    {value: 7, label: "Hogh Distinction (7)"},
  ];

  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const TIMES = ["Morning", "Afternoon", "Evening"];
  const [availableDays, setAvailableDays] = useState(
    DAYS.map((day) => ({ day, times: [] }))
  );

  const communicationOptions = [
    {value: "email", label: "Email"},
    {value: "teams", label: "Teams"},
    {value: "slack", label: "Slack"},
    {value: "discord", label: "Discord"},
    {value: "instagram", label: "Instagram"},
    {value: "snapchat", label: "Snapchat"},
    {value: "messenger", label: "Messenger"},
    {value: "signal", label: "Signal"},
    {value: "telegram", label: "Telegram"},
    {value: "linkedin", label: "LinkedIn"},
    {value: "others", label: "Other Methods"},
  ];

  const meetingModeOptions = [
    {value: "physical", label: "Physical (In-Person)"},
    {value: "virtual", label: "Virtual (Online)"},
    {value: "either", label: "Either"},
  ];

  const semesterOptions = [
    {value: 1, label: "First Semester"},
    {value: 2, label: "Second Semester"},
  ];


  useEffect(() => {
    setCurrentGPA(attributes.current_gpa);
    setGoalGrade(attributes.goal_grade);
    setAvailability(attributes.availability || []);
    setCommunication(attributes.communication || []);
    setMeetingMode(attributes.meeting_mode);
    setYear(attributes.year);
    setSemester(attributes.semester);
    setAccessibility(attributes.accessibility || false);
    
    // TODO: Handle Attribute Sharing Updating
    setSharingAttributes(sharedAttributes || []);

    setDisplayAttributes(attributesComplete || false);
  }, [code, navigate]);


  const getAvailabilityList = (availableDays) => {
    const availability = [];
    availableDays.forEach((slot, dayIndex) => {
      slot.times.forEach((time) => {
        const code = `${DAYS[dayIndex].slice(0,3)}${time[0]}`;
        availability.push(code);
      });
    });
    return availability;
  }

  // Toggle a Time Slot on/off for a Given Day
  const toggleTime = (dayIndex, time) => {
    const newDays = [...availableDays];
    const current = newDays[dayIndex].times;

    newDays[dayIndex] = {
      ...newDays[dayIndex],
      times: current.includes(time)
        ? current.filter((t) => t !== time)
        : [...current, time],
    };
    setAvailableDays(newDays);

    const newAvailability = getAvailabilityList(newDays);
    setAvailability(newAvailability);
    updateDetails({availability: newAvailability});
  };


  const handleCurrentGPA = (event) => {
    event.preventDefault();
    // TODO: Prevalidate
    const newCurrentGPA = event.target.value;

    setCurrentGPA(newCurrentGPA);
    updateDetails({current_gpa: newCurrentGPA}); // TODO: Might just need to use event.target.value for these
  }

  const handleGoalGrade = (event) => {
    event.preventDefault();
    const newGoalGrade = event.target.value;
    
    setGoalGrade(newGoalGrade);
    updateDetails({goal_grade: newGoalGrade});
  }

  const handleAvailability = (event) => {
    event.preventDefault();
    const newGoalGrade = event.target.value;
    
    setGoalGrade(newGoalGrade);
    updateDetails({goal_grade: newGoalGrade});
  }

  const handleConfirm = (event) => {
    event.preventDefault();

    // if (availability.length === 0) {
    //   const proceed = window.confirm("You did not select any available times. Submit anyway?");
    //   if (!proceed) return;
    // }

    const availability = getAvailabilityList(availableDays);

    updateDetails({
      current_gpa: currentGPA,
      goal_grade: goalGrade,
      availability: availability,
      availability: availability,
      communication: communication,
      meetingMode: meetingMode,
      year: year,
      semester: semester
    });
    confirmDetails();
  }


  return (
    <>
      {/* TODO: Fix Styling */}
      <div className="text-center">
        {/* Username display */}
        <div className="stat-box mb-md">
          <div className="stat-label">Your Username</div>
          <div className="stat-value" style={{ fontSize: "1.25rem" }}>{username}</div>
        </div>

        {(!attributesComplete || displayAttributes) ? (
          <>
            {/* Student Details Input */}
            <div className="mb-md" style={{ padding: "2rem 0" }}>
              <h2 style={{ color: "var(--color-primary)", marginBottom: "1rem" }}>
                Enter Details for Group Formation
              </h2>

              {/* Current GPA Selection */}
              {availableAttributes.includes("current_gpa") && (
                <>
                  {/* TODO: Improve Selection Menu and Input*/}
                  <DropdownInput
                    name="current-gpa"
                    label="Current GPA"
                    value={currentGPA}
                    options={gradeOptions}
                    placeholder="Select Current GPA"
                    onChange={handleCurrentGPA}
                  />
                  <CheckboxInput
                    name="share-current-gpa-checkbox"
                    label="Share Current GPA with Group Members?"
                    value={shareCurrentGPA}
                    onChange={setShareCurrentGPA}
                  />
                </>
              )}

              {/* Goal Grade Selection */}
              {availableAttributes.includes("goal_grade") && (
                <>
                  {/* TODO: Improve Selection Menu and Input*/}
                  <DropdownInput
                    name="goal-grade"
                    label="Goal Grade for Unit"
                    value={goalGrade}
                    options={gradeOptions}
                    placeholder="Select Goal Grade"
                    onChange={handleGoalGrade}
                  />
                  <CheckboxInput
                    name="share-current-gpa-checkbox"
                    label="Share Goal Grade with Group Members?"
                    value={shareGoalGrade}
                    onChange={setShareGoalGrade}
                  />
                </>
              )}


              {/* Availability Time Selection Grid */}
              {/* TODO: Clean Up this Code/Logic */}
              {availableAttributes.includes("availability") && (
                <div className="mt-md">
                  <label className="input-label">Availability Times</label>

                  <div className="flex-col gap-xs" style={{ display: "flex" }}>
                    {availableDays.map((slot, dayIndex) => (
                      <div key={dayIndex} className="availability-row">
                        <span className="day-label">{slot.day}</span>

                        {TIMES.map((time) => (
                          <button
                            key={time}
                            className={`btn-toggle ${
                              slot.times.includes(time) ? "active" : ""
                            }`}
                            onClick={() => toggleTime(dayIndex, time)}
                          >
                            {time}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                  <CheckboxInput
                    name="share-availability-checkbox"
                    label="Share Availability with Group Members?"
                    value={shareAvailability}
                    onChange={setShareAvailability}
                  />
                </div>
              )}

              {/* Student Communication Methods Selection */}
              {availableAttributes.includes("communication") && (
                <>
                  {/* TODO: Improve Selection Menu and Input Type */}
                  <DropdownInput
                    name="communication"
                    label="Prefered Communication Methods"
                    value={communication}
                    options={communicationOptions}
                    placeholder="Select Multiple Communication Methods"
                    onChange={setCommunication}
                    multiple={true}
                  />
                  <CheckboxInput
                    name="share-communication-checkbox"
                    label="Share Communication Methods with Group Members?"
                    value={shareCommunication}
                    onChange={setShareCommunication}
                  />
                </>
              )}

              {/* Meeting Mode Selection */}
              {availableAttributes.includes("meeting_mode") && (
                <>
                  {/* TODO: Improve Selection Menu and Input*/}
                  <DropdownInput
                    name="meeting-mode"
                    label="Prefered Meeting Mode"
                    value={meetingMode}
                    options={meetingModeOptions}
                    placeholder="Select Meeting Mode"
                    onChange={setMeetingMode}
                  />
                  <CheckboxInput
                    name="share-meeting-mode-checkbox"
                    label="Share Meeting Mode with Group Members?"
                    value={shareMeetingMode}
                    onChange={setShareMeetingMode}
                  />
                </>
              )}

              {/* Study Year Selection */}
              {availableAttributes.includes("year") && (
                <>
                  {/* TODO: Improve Selection Menu and Input*/}
                  <NumberInput
                    name="year"
                    label="Current Study Year"
                    value={semester}
                    min={1}
                    max={10}
                    placeholder="2..."
                    onChange={setSemester}
                  />
                  {/* TODO: Add Note that this is Always Shared to Other Students/Group Members */}
                </>
              )}

              {/* Study Semester Selection */}
              {availableAttributes.includes("semester") && (
                <>
                  {/* TODO: Improve Selection Menu and Input*/}
                  <DropdownInput
                    name="semester"
                    label="Current Study Semester"
                    value={semester}
                    options={semesterOptions}
                    placeholder="Select Study Semester"
                    onChange={setSemester}
                  />
                  {/* TODO: Add Note that this is Always Shared to Other Students/Group Members */}
                </>
              )}
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
              {/* TODO: Add Button to Edit Attributes again Somewhere */}
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
