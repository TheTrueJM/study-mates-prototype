import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../../components/Button";
import Modal from "../../components/Modal";


export default function GroupLayout({ code, state, username, groupNumber, groupMembers, questions, timeRemaining, timeRunning }) {
  const navigate = useNavigate();

  const [expandedMember, setExpandedMember] = useState("");
  const [showQuestionsModal, setShowQuestionsModal] = useState(false);


  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const toggleMember = (name) => {
    setExpandedMember(expandedMember === name ? "" : name);
  };


  return (
    <>
      {groupNumber === null ? (
        <div className="text-center">
          <p>Waiting for Group Allocation...</p>
        </div>
      ) : (
        <>
          <div className="card-subtitle">Group {groupNumber}</div>

          {state === "discussion" && (
            <div className="timer-display mb-md">
              <div className="timer-value">{formatTime(timeRemaining)}</div>
              <div className="timer-status">Remaining Discussion Time</div>
            </div>
          )}

          <div className="flex-col gap-xs" style={{ display: "flex" }}>
            {groupMembers
              .filter((member, index, self) => index === self.findIndex(m => m.name === member.name))
              .map((member) => (
                <div
                  key={member.name}
                  className={`member-card ${member.name === username ? "current-user" : ""}`}
                  style={{ cursor: "pointer" }}
                  onClick={() => toggleMember(member.name)}
                >
                  <div className="member-name">{member.name}</div>
                  {/* TODO: Improve Styling */}
                  {expandedMember === member.name && member.sharedAttributes && (
                    <>
                      {member.sharedAttributes.includes("current_gpa") && member.current_gpa && (
                        <div className="member-current-gpa" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          {/* TODO: Translate to Category (i.e. P, C, H, HD) */}
                          <strong>Current GPA:</strong> {member.current_gpa || "None Specified"}
                        </div>
                      )}

                      {member.sharedAttributes.includes("goal_grade") && member.goal_grade && (
                        <div className="member-goal-grade" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          {/* TODO: Translate to Category (i.e. P, C, H, HD) */}
                          <strong>Goal Grade:</strong> {member.goal_grade || "None Specified"}
                        </div>
                      )}

                      {member.sharedAttributes.includes("availability") && member.availability && (
                        <div className="member-availability" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          <strong>Availability:</strong> {member.availability.join(", ") || "None Specified"}
                        </div>
                      )}

                      {member.sharedAttributes.includes("communication") && member.communication && (
                        <div className="member-availability" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          <strong>Communication Methods:</strong> {member.communication.join(", ") || "None Specified"}
                        </div>
                      )}

                      {member.sharedAttributes.includes("meeting_mode") && member.meeting_mode && (
                        <div className="member-meeting-mode" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          <strong>Meeting Mode:</strong> {member.meeting_mode || "None Specified"}
                        </div>
                      )}

                      {member.sharedAttributes.includes("year") && member.year && (
                        <div className="member-year" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          <strong>Study Year:</strong> {member.year || "None Specified"}
                        </div>
                      )}

                      {member.sharedAttributes.includes("semester") && member.semester && (
                        <div className="member-semester" style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#666" }}>
                          <strong>Study Semester:</strong> {member.semester || "None Specified"}
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))}
          </div>
        </>
      )}


      {state === "discussion" && (
        <div className="divider mt-md">
          <Button variant="secondary" onClick={() => setShowQuestionsModal(true)} fullWidth>
            View Discussion Topics
          </Button>

          <p className="mt-sm" style={{ fontSize: "0.875rem", color: "#888" }}>
            Discuss the Topics and Questions to get to know your Group Members!
          </p>
        </div>
      )}


      <Modal title="Tutorial Session Settings" isOpen={showQuestionsModal} onClose={() => setShowQuestionsModal(false)}>
        {questions.length === 0 ? (
          <p style={{ color: "#888" }}>No Topics Available Yet.</p>
        ) : (
          <div className="flex-col gap-xs" style={{ display: "flex" }}>
            {questions.map((question, index) => (
              <div key={index} className="question-item">
                <div className="question-number">{index + 1}</div>
                <div>{question}</div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </>
  );
}
