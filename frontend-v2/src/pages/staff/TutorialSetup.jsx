import { useState } from "react";
import { createTutorial } from "../../api/staff";

export default function TutorialSetup() {
    const [name, setName] = useState("");
    const [groupSize, setGroupSize] = useState(4);
    const [discussionDuration, setDiscussionDuration] = useState(600);
    const [availableAttributes, setAvailableAttributes] = useState([
        "currentGPA", "goalGPA", "availability"
    ]);
    const [createdCode, setCreatedCode] = useState(null);
    
    const handleAttributeToggle = (attribute) => {
        if (availableAttributes.includes(attribute)) {
            setAvailableAttributes(availableAttributes.filter(a => a !== attribute));
        } else {
            setAvailableAttributes([...availableAttributes, attribute]);
        }
    };
    
    const handleSubmit = async () => {
        const result = await createTutorial({
            name,
            groupSize,
            discussionDuration,
            availableAttributes
        });
        setCreatedCode(result.code);
    };
    
    return (
        <div className="tutorial-setup">
            <h2>Create Tutorial</h2>
            
            <div className="field">
                <label>Tutorial Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            
            <div className="field">
                <label>Group Size</label>
                <input type="number" min="2" max="10" value={groupSize} onChange={(e) => setGroupSize(e.target.value)} />
            </div>
            
            <div className="field">
                <label>Discussion Duration (seconds)</label>
                <input type="number" min="60" max="3600" value={discussionDuration} onChange={(e) => setDiscussionDuration(e.target.value)} />
            </div>
            
            <div className="field">
                <label>Available Attributes</label>
                {["currentGPA", "goalGPA", "availability"].map(attr => (
                    <label key={attr}>
                        <input
                            type="checkbox"
                            checked={availableAttributes.includes(attr)}
                            onChange={() => handleAttributeToggle(attr)}
                        />
                        {attr === "currentGPA" ? "Current GPA" : 
                         attr === "goalGPA" ? "Goal Grade" : "Availability"}
                    </label>
                ))}
            </div>
            
            <button onClick={handleSubmit}>Create Tutorial</button>
            
            {createdCode && (
                <div className="result">
                    <h3>Tutorial Created!</h3>
                    <p>Code: {createdCode}</p>
                    <p>Share this code with students</p>
                </div>
            )}
        </div>
    );
}