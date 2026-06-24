import { useState } from "react";
import { useTutorial } from "../../context/TutorialContext";

export default function EnterDetails() {
    const { updateDetails, enterTutorial, state, tutorialCode } = useTutorial();
    const [currentGPA, setCurrentGPA] = useState("");
    const [goalGPA, setGoalGPA] = useState("");
    const [availability, setAvailability] = useState({});
    const [sharedAttributes, setSharedAttributes] = useState([]);
    
    // Determine which attributes are available from tutorial state
    const availableAttributes = state?.available_attributes || [];
    
    const handleShareToggle = (attribute) => {
        if (sharedAttributes.includes(attribute)) {
            setSharedAttributes(sharedAttributes.filter(a => a !== attribute));
        } else {
            setSharedAttributes([...sharedAttributes, attribute]);
        }
    };
    
    const handleSubmit = () => {
        const details = {};
        if (currentGPA && availableAttributes.includes("currentGPA")) {
            details.currentGPA = parseFloat(currentGPA);
        }
        if (goalGPA && availableAttributes.includes("goalGPA")) {
            details.goalGPA = parseFloat(goalGPA);
        }
        if (Object.keys(availability).length > 0 && availableAttributes.includes("availability")) {
            details.availability = availability;
        }
        details.sharedAttributes = sharedAttributes;
        
        updateDetails(details);
        enterTutorial();
    };
    
    return (
        <div className="enter-details">
            <h2>Enter Your Details</h2>
            <p>Tutorial: {tutorialCode}</p>
            
            {availableAttributes.includes("currentGPA") && (
                <div className="field">
                    <label>Current GPA</label>
                    <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="7"
                        value={currentGPA}
                        onChange={(e) => setCurrentGPA(e.target.value)}
                    />
                    <label>
                        <input
                            type="checkbox"
                            checked={sharedAttributes.includes("currentGPA")}
                            onChange={() => handleShareToggle("currentGPA")}
                        />
                        Share with others
                    </label>
                </div>
            )}
            
            {availableAttributes.includes("goalGPA") && (
                <div className="field">
                    <label>Goal Grade</label>
                    <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="7"
                        value={goalGPA}
                        onChange={(e) => setGoalGPA(e.target.value)}
                    />
                    <label>
                        <input
                            type="checkbox"
                            checked={sharedAttributes.includes("goalGPA")}
                            onChange={() => handleShareToggle("goalGPA")}
                        />
                        Share with others
                    </label>
                </div>
            )}
            
            {availableAttributes.includes("availability") && (
                <div className="field">
                    <label>Availability</label>
                    {/* Availability picker component */}
                    <label>
                        <input
                            type="checkbox"
                            checked={sharedAttributes.includes("availability")}
                            onChange={() => handleShareToggle("availability")}
                        />
                        Share with others
                    </label>
                </div>
            )}
            
            <button onClick={handleSubmit}>Enter Tutorial</button>
        </div>
    );
}