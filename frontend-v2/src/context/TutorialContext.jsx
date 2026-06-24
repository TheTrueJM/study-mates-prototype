import { createContext, useContext, useState, useEffect, useRef } from "react";
import { getSocket } from "../socket";

const TutorialContext = createContext(null);

export function TutorialProvider({ children }) {
    const [tutorialCode, setTutorialCode] = useState(null);
    const [state, setState] = useState(null);
    const [students, setStudents] = useState([]);
    const [groups, setGroups] = useState(null);
    const [timer, setTimer] = useState(null);
    const [round, setRound] = useState(0);
    const [authenticated, setAuthenticated] = useState(false);
    const [studentUuid, setStudentUuid] = useState(null);
    const [studentName, setStudentName] = useState(null);
    const [currentDetails, setCurrentDetails] = useState({});
    const socketRef = useRef(null);

    useEffect(() => {
        socketRef.current = getSocket();
        const socket = socketRef.current;

        // Student events
        socket.on("authenticated", (data) => {
            setAuthenticated(true);
            setStudentUuid(data.uuid);
            setStudentName(data.name);
            setTutorialCode(data.tutorial_code);
        });

        socket.on("join_failed", (data) => {
            alert(data.reason);
        });

        socket.on("tutorial_state", (data) => {
            setState(data.state);
            setStudents(data.students);
            setGroups(data.groups);
            setTimer(data.timer);
            setRound(data.round);
        });

        socket.on("students_updated", (data) => {
            setStudents(data.students);
        });

        socket.on("groups_formed", (data) => {
            setGroups(data.groups);
            setRound(data.round);
        });

        socket.on("discussion_started", (data) => {
            setTimer({
                duration: data.intro_duration + data.discussion_duration,
                remaining: data.intro_duration,
                phase: "intro"
            });
        });

        socket.on("timer_update", (data) => {
            setTimer(data);
        });

        socket.on("timer_expired", (data) => {
            if (data.phase === "intro") {
                // Discussion timer starts
                setTimer({
                    ...timer,
                    remaining: timer.duration - timer.intro_duration,
                    phase: "discussion"
                });
            } else {
                // Discussion ended
                setTimer(null);
            }
        });

        socket.on("tutorial_ended", () => {
            setAuthenticated(false);
            setStudentUuid(null);
            setStudentName(null);
            setTutorialCode(null);
            setState(null);
            setStudents([]);
            setGroups(null);
            setTimer(null);
            setRound(0);
            setCurrentDetails({});
            // Redirect to home page
        });

        socket.on("error", (data) => {
            alert(data.message);
        });

        return () => {
            socket.off();
        };
    }, []);

    const joinTutorial = (code) => {
        socketRef.current.emit("join_tutorial", { code });
    };

    const updateDetails = (details) => {
        socketRef.current.emit("update_details", details);
        setCurrentDetails(details);
    };

    const enterTutorial = () => {
        socketRef.current.emit("enter_tutorial");
    };

    const startRound = () => {
        socketRef.current.emit("start_round");
    };

    const startDiscussion = () => {
        socketRef.current.emit("start_discussion");
    };

    const nextRound = () => {
        socketRef.current.emit("next_round");
    };

    const backToLobby = () => {
        socketRef.current.emit("back_to_lobby");
    };

    const endTutorial = () => {
        socketRef.current.emit("end_tutorial");
    };

    return (
        <TutorialContext.Provider value={{
            tutorialCode, state, students, groups, timer, round,
            authenticated, studentUuid, studentName, currentDetails,
            joinTutorial, updateDetails, enterTutorial,
            startRound, startDiscussion, nextRound, backToLobby, endTutorial
        }}>
            {children}
        </TutorialContext.Provider>
    );
}

export function useTutorial() {
    return useContext(TutorialContext);
}