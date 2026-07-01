import { createContext, useContext, useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import { getStaffSocket, getStudentSocket, disconnectSocket } from "../socket";

const TutorialContext = createContext(null);

export function TutorialProvider({ children }) {
  const navigate = useNavigate();

  const [UUID, setUUID] = useState("");
  const [tutorialCode, setTutorialCode] = useState("");
  const [tutorialName, setTutorialName] = useState("");
  const [state, setState] = useState("");
  const [availableAttributes, setAvailableAttributes] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [timeDuration, setTimeDuration] = useState("");
  const [timeRemaining, setTimeRemaining] = useState("");
  const [timeRunning, setTimeRunning] = useState(false);

  const [studentName, setStudentName] = useState("");
  const [attributes, setAttributes] = useState({});
  const [sharedAttributes, setSharedAttributes] = useState([]);
  const [attributesComplete, setAttributesComplete] = useState(false);
  const [groupNumber, setGroupNumber] = useState("");
  const [groupMembers, setGroupMembers] = useState({});

  const [students, setStudents] = useState({});
  const [groups, setGroups] = useState({});
  const [groupSize, setGroupSize] = useState("");
  const [maxGroups, setMaxGroups] = useState("");

  const [currentNamespace, setCurrentNamespace] = useState("/");


  // Helper function to attach all event listeners to a socket instance
  const attachListeners = (nsSocket) => {
    nsSocket.on("session", (data) => {
      console.log("Session Socket: ", nsSocket);

      if (data) {
        const uuid = data.uuid;
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

    nsSocket.on("tutorial_ended", () => {
      setTutorialCode("");
      setTutorialName("");
      setState("");
      setQuestions([]);
      setTimeDuration("");
      setTimeRemaining("");
      setTimeRunning(false);

      setStudentName("");
      setAttributes({});
      setSharedAttributes([]);
      setAttributesComplete(false);
      setGroupNumber("");
      setGroupMembers({});

      setStudents({});
      setAvailableAttributes([]);
      setGroups({});
      setGroupSize("");
      setMaxGroups("");

      disconnectSocket(currentNamespace);

      // TODO: Redirect to home page or create tutorial page (depending on auth)
      navigate(currentNamespace == "/staff" ? "/staff/login" : "/");
    });

    nsSocket.on("error", (error) => {
      // TODO: Check if Alert causes Issues
      // alert(error.message);
      console.log("Socket Error: ", error.message);
    });

    // Student Events
    nsSocket.on("tutorial_joined", (data) => {
      const tutorialCode = data.tutorial_code;
      localStorage.setItem("tutorialCode", tutorialCode);
      setTutorialCode(tutorialCode);
      navigate(`/tutorial/${tutorialCode}`);
    });

    nsSocket.on("details_updated", (data) => {
      setAttributes(data.attributes || {});
      setSharedAttributes(data.sharedAttributes || []);
      setAttributesComplete(data.attributes_complete);
    });

    nsSocket.on("details_confirmed", (data) => {
      setAttributes(data.attributes || {});
      setSharedAttributes(data.sharedAttributes || []);
      setAttributesComplete(data.attributes_complete);
    });

    nsSocket.on("student_update", (data) => {
      setStudentName(data.username);
      setAttributes(data.attributes || {});
      setSharedAttributes(data.shared_attributes || []);
      setAttributesComplete(data.attributes_complete);

      setTutorialCode(data.tutorial_code);
      setTutorialName(data.tutorial_name);
      setState(data.state);
      setGroupNumber(data.group_number);
      setGroupMembers(data.group_members || []);
      setQuestions(data.questions || []);

      const timer = data.timer || {};
      setTimeDuration(timer.duration);
      setTimeRemaining(timer.remaining);
      setTimeRunning(timer.running);
    });

    // Staff Events
    nsSocket.on("tutorial_created", (data) => {
      const tutorialCode = data.tutorial_code;
      localStorage.setItem("tutorialCode", tutorialCode);
      setTutorialCode(tutorialCode);
      navigate(`/staff/tutorial/${tutorialCode}`);
    });

    nsSocket.on("tutorial_update", (data) => {
      setTutorialCode(data.tutorial_code);
      setTutorialName(data.tutorial_name);
      setState(data.state);
      setGroupSize(data.group_size);
      setMaxGroups(data.max_groups);
      setAvailableAttributes(data.available_attributes || []);

      setStudents(data.students || {});
      setGroups(data.groups || {});
      setQuestions(data.questions || []);

      const timer = data.timer || {};
      setTimeDuration(timer.duration);
      setTimeRemaining(timer.remaining);
      setTimeRunning(timer.running);
    });

    // Timer Events
    nsSocket.on("timer_notification", (data) => {
      alert(data.message);
    });
  };

  // Initialize student socket on mount
  useEffect(() => {
    const studentSocket = getStudentSocket();
    attachListeners(studentSocket);
    setCurrentNamespace("/");
  }, []);

  const switchToStaff = () => {
    disconnectSocket("/");
    const staffSocket = getStaffSocket();
    attachListeners(staffSocket);
    setCurrentNamespace("/staff");
  };

  const switchToStudent = () => {
    disconnectSocket("/staff");
    const studentSocket = getStudentSocket();
    attachListeners(studentSocket);
    setCurrentNamespace("/");
  };

  const getActiveSocket = () => {
    if (currentNamespace === "/staff") {
      return getStaffSocket();
    }
    return getStudentSocket();
  };

  // Student Actions
  const enterTutorial = (code) => {
    getStudentSocket().emit("enter_tutorial", { code });
  };

  const updateDetails = (details) => {
    getStudentSocket().emit("update_details", details);
  };

  const confirmDetails = () => {
    getStudentSocket().emit("confirm_details");
  };

  const leaveTutorial = () => {
    getStudentSocket().emit("leave_tutorial");
    localStorage.removeItem("tutorialCode");
  };

  // Staff Actions
  const createTutorial = (settings) => {
    console.log("Create Tutorial Socket: ", getStaffSocket());
    getStaffSocket().emit("create_tutorial", settings);
  };

  const updateTutorial = (settings) => {
    getStaffSocket().emit("update_settings", settings);
  };

  const backToLobby = () => {
    getStaffSocket().emit("return_lobby");
  };

  const startGrouping = () => {
    getStaffSocket().emit("start_grouping");
  };

  const startDiscussion = () => {
    getStaffSocket().emit("start_discussion");
  };

  const startTimer = () => {
    getStaffSocket().emit("start_timer");
  };

  const stopTimer = () => {
    getStaffSocket().emit("stop_timer");
  };

  const resetTimer = (time) => {
    getStaffSocket().emit("reset_timer", { time });
  };

  const endTutorial = () => {
    getStaffSocket().emit("end_tutorial");
    localStorage.removeItem("tutorialCode");
  };

  return (
    <TutorialContext.Provider value={{
      tutorialCode, tutorialName, state, questions, timeDuration, timeRemaining, timeRunning,
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