import { useTutorial } from "../../context/TutorialContext";

export default function LobbyLayout() {
    const { tutorialCode, state, students } = useTutorial();
    
    return (
        <div className="lobby-layout">
            <h2>Tutorial Lobby</h2>
            <p>Tutorial Code: {tutorialCode}</p>
            
            <div className="students-list">
                <h3>Students ({students.length})</h3>
                {students.map(student => (
                    <div key={student.uuid} className="student-card">
                        <span>{student.name}</span>
                        {student.details_complete && <span>✓</span>}
                    </div>
                ))}
            </div>
        </div>
    );
}