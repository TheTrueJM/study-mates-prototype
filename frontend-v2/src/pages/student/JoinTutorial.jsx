import { useState } from "react";
import { useTutorial } from "../../context/TutorialContext";

export default function JoinTutorial() {
    const [code, setCode] = useState("");
    const { joinTutorial } = useTutorial();
    
    const handleSubmit = (e) => {
        e.preventDefault();
        if (code.trim()) {
            joinTutorial(code.trim());
        }
    };
    
    return (
        <div className="join-tutorial">
            <h2>Join Tutorial</h2>
            <form onSubmit={handleSubmit}>
                <input 
                    type="text" 
                    placeholder="Enter tutorial code" 
                    value={code} 
                    onChange={(e) => setCode(e.target.value)} 
                />
                <button type="submit">Join</button>
            </form>
        </div>
    );
}