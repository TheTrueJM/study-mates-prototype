import { useTutorial } from "../../context/TutorialContext";

export default function GroupsLayout() {
    const { groups, startDiscussion } = useTutorial();
    
    return (
        <div className="groups-layout">
            <h2>Groups Formation</h2>
            
            {groups && Object.keys(groups).length > 0 ? (
                <div className="groups-list">
                    {Object.entries(groups).map(([groupId, members]) => (
                        <div key={groupId} className="group-card">
                            <h3>{groupId}</h3>
                            <ul>
                                {members.map(uuid => (
                                    <li key={uuid}>Member UUID: {uuid}</li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            ) : (
                <p>No groups formed yet</p>
            )}
            
            <button onClick={startDiscussion}>Start Discussion</button>
        </div>
    );
}