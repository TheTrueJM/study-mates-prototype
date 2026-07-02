import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";

import Card from "../../components/Card";
import Button from "../../components/Button";
import Modal from "../../components/Modal";

import LobbyLayout from "./LobbyLayout";
import GroupLayout from "./GroupLayout";


function Tutorial() {
  const navigate = useNavigate();
  const { code } = useParams();

  const {
    studentName, attributes, sharedAttributes, attributesComplete,
    tutorialCode, tutorialName, tutorialState, availableAttributes,
    groupNumber, groupMembers, questions, timeRemaining, timeRunning,
    enterTutorial, updateDetails, confirmDetails, leaveTutorial
  } = useTutorial();


  useEffect(() => {
    // TODO: Handle Errors and Navigation
    if (!tutorialCode) {
      enterTutorial(code);
    } else if (tutorialCode != code) {
      enterTutorial(tutorialCode);
    }
  }, [code, navigate]);

  return (
    <div className="container container-md mt-lg">
      <Card
        title={tutorialName}
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {/* {(tutorialState === "groups" || tutorialState === "discussion") && (
              <Button variant="outline" onClick={() => setShowDetailsModal(true)}>
                Edit Details
              </Button>
            )} */}
            <Button variant="outline" onClick={leaveTutorial}>Leave Tutorial</Button>
          </div>
        }
      >
        {/* tutorial components split across separate files */}
        {tutorialState === "lobby" && (
          <LobbyLayout
            code={code}
            username={studentName}
            attributes={attributes}
            sharedAttributes={sharedAttributes}
            attributesComplete={attributesComplete}
            availableAttributes={availableAttributes}
            updateDetails={updateDetails}
            confirmDetails={confirmDetails}
          />
        )}
        {(tutorialState === "grouping" || tutorialState === "discussion") && (
          <GroupLayout
            code={code}
            state={tutorialState}
            username={studentName}
            groupNumber={groupNumber}
            groupMembers={groupMembers}
            questions={questions}
            timeRemaining={timeRemaining}
            timeRunning={timeRunning}
          />
        )}
      </Card>


      {/* <Modal title="Tutorial Session Settings" isOpen={showDetailsModal} onClose={() => setShowDetailsModal(false)}> */}
        {/* TODO: Add Student Attributes Inputs */}
      {/* </Modal> */}
    </div>
  );
}

export default Tutorial;
