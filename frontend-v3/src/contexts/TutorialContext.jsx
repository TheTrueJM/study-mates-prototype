import { createContext, useContext, useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { getSocket, getStaffSocket, disconnectSocket, disconnectStaffSocket } from "../socket";


const TutorialContext = createContext(null);

export function TutorialProvider({ children }) {
  const navigate = useNavigate();

  const [UUID, setUUID] = useState(null);
  const [tutorialCode, setTutorialCode] = useState(null);
  const [tutorialName, setTutorialName] = useState(null);
  const [state, setState] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [timer, setTimer] = useState({});

  const [studentName, setStudentName] = useState(null);
  const [attributes, setAttributes] = useState({});
  const [sharedAttributes, setSharedAttributes] = useState([]);
  const [attributesComplete, setAttributesComplete] = useState(null);
  const [groupNumber, setGroupNumber] = useState(null);
  const [groupMembers, setGroupMembers] = useState({});

  const [students, setStudents] = useState({});
  const [availableAttributes, setAvailableAttributes] = useState([]);
  const [groups, setGroups] = useState({});
  const [groupSize, setGroupSize] = useState(null);
  const [maxGroups, setMaxGroups] = useState(null);

  const socketRef = useRef(null);


  useEffect(() => {
    socketRef.current = getSocket();

    socketRef.current.on("session", (data) => {
      if (data) {
        const uuid = data.user_id;
        const tutorialCode = data.code;

        if (uuid) {
          localStorage.setItem("uuid", uuid);
          setUUID(uuid);
        }
        if (tutorialCode) {
          localStorage.setItem("tutorialCode", tutorialCode);
          setTutorialCode(tutorialCode);
        }
      }
    });

    socketRef.current.on("tutorial_ended", () => {
      setTutorialCode(null);
      setTutorialName(null);
      setState(null);
      setQuestions([]);
      setTimer({});

      setStudentName(null);
      setAttributes({});
      setSharedAttributes([]);
      setAttributesComplete(null);
      setGroupNumber(null);
      setGroupMembers({});

      setStudents({});
      setAvailableAttributes([]);
      setGroups({});
      setGroupSize(null);
      setMaxGroups(null);

      // TODO: Redirect to home page or create tutorial page (depending on auth)
      // navigate("/");
    });

    socketRef.current.on("error", (error) => {
      // TODO: Check if Alert causes Issues
      // alert(error.message);
      console.log(error.message);
    });

    // Student Events
    socketRef.current.on("details_updated", (data) => {
      setAttributes(data.attributes);
      setSharedAttributes(data.sharedAttributes);
    });

    socketRef.current.on("details_confirmed", (data) => {
      setAttributes(data.attributes);
      setSharedAttributes(data.sharedAttributes);
    });

    socketRef.current.on("student_update", (data) => {
      setStudentName(data.get("username"));
      setAttributes(data.get("attributes"));
      setSharedAttributes(data.get("shared_attributes"));
      setAttributesComplete(data.get("attributes_complete"));

      setTutorialCode(data.get("tutorial_code"));
      setTutorialName(data.get("tutorial_name"));
      setState(data.get("state"));
      setGroupNumber(data.get("group_number"));
      setGroupMembers(data.get("group_members"));
      setQuestions(data.get("questions"));
      setTimer(data.get("timer"));
    });

    // Staff Events
    socketRef.current.on("tutorial_created", (data) => {
      setTutorialCode(data.get("tutorial_code"));
    });

    // Timer Events
    socketRef.current.on("timer_notification", (data) => {
      // TODO: Improve Integration
      alert(data.message);
      // console.log(error.message);
    });

    return () => {
      socket.off();
    };
  }, []);


  const switchToStaff = () => {
    disconnectSocket();
    socketRef.current = getSocket("/staff");
  };

  const switchToStudent = () => {
    disconnectSocket();
    socketRef.current = getSocket("/");
  };


  // Student Actions
  const enterTutorial = (code) => {
    socketRef.current.emit("enter_tutorial", { code });
  };

  const updateDetails = (details) => {
    socketRef.current.emit("update_details", details);
  };

  const confirmDetails = () => {
    socketRef.current.emit("confirm_details");
  };

  const leaveTutorial = () => {
    socketRef.current.emit("leave_tutorial");
    localStorage.removeItem("tutorialCode");
  };

  // Staff Actions
  const createTutorial = (settings) => {
    socketRef.current.emit("create_tutorial", settings);
  };

  const updateTutorial = (settings) => {
    socketRef.current.emit("update_settings", settings);
  };

  const backToLobby = () => {
    socketRef.current.emit("return_lobby");
  };

  const startGrouping = () => {
    socketRef.current.emit("start_grouping");
  };

  const startDiscussion = () => {
    socketRef.current.emit("start_discussion");
  };

  const startTimer = () => {
    socketRef.current.emit("start_timer");
  };

  const stopTimer = () => {
    socketRef.current.emit("stop_timer");
  };

  const resetTimer = (time) => {
    socketRef.current.emit("reset_timer", { time });
  };

  const endTutorial = () => {
    socketRef.current.emit("end_tutorial");
    localStorage.removeItem("tutorialCode");
  };


  return (
    <TutorialContext.Provider value={{
      tutorialCode, tutorialName, state, questions, timer,
      studentName, attributes, sharedAttributes, attributesComplete, groupNumber, groupMembers,
      students, availableAttributes, groups, groupSize, maxGroups,
      switchToStaff, switchToStudent, enterTutorial, updateDetails, confirmDetails, leaveTutorial,
      createTutorial, updateTutorial, backToLobby, startGrouping, startDiscussion, endTutorial,
      startTimer, stopTimer, resetTimer
    }}>
      {children}
    </TutorialContext.Provider>
  );
}

export const useTutorial = () => useContext(TutorialContext);