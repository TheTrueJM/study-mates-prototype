import { useTutorial } from "../../context/TutorialContext";
import Timer from "../../components/Timer";

export default function DiscussionLayout() {
    const { timer, nextRound, backToLobby } = useTutorial();
    
    return (
        <div className="discussion-layout">
            <h2>Discussion Phase</h2>
            
            {timer && (
                <div className="timer-display">
                    <Timer timer={timer} />
                </div>
            )}
            
            <button onClick={nextRound}>Next Round</button>
            <button onClick={backToLobby}>Back to Lobby</button>
        </div>
    );
}