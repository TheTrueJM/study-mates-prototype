import { createContext, startTransition, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getSocket, emitWithAck, setStudentId, STUDENT_NAMESPACE, STAFF_NAMESPACE } from "../socket";
import { useAuth } from "./AuthContext";

const TutorialContext = createContext(null);

const SESSION_LOST = "Your Session is no longer Running, as the Server was Restarted or it was Closed while you were away.";

const INITIAL_TUTORIAL = {
  tutorialCode: "",
  tutorialName: "",
  tutorialState: "",
  availableAttributes: [],
  questions: [],
  timeDuration: 0,
  timeRemaining: 0,
  timeRunning: false,
  timeEndsAt: null,
  round: 0,

  // Student
  studentName: "",
  attributes: {},
  sharedAttributes: [],
  attributesComplete: false,
  studentCount: 0,
  groupNumber: null,
  groupMembers: [],
  formation: 0,

  // Staff
  locked: false,
  students: {},
  groups: {},
  groupSize: null,
  maxGroups: null,
};

// The Remaining Time is from when the update is received, so is kept as an End Time while the Timer is running
const mapTimer = (timer = {}) => ({
  timeDuration: timer.duration ?? 0,
  timeRemaining: timer.remaining ?? 0,
  timeRunning: !!timer.running,
  timeEndsAt: timer.running ? Date.now() + (timer.remaining ?? 0) * 1000 : null,
});

const mapStudentUpdate = (data) => ({
  tutorialCode: data.tutorial_code || "",
  tutorialName: data.tutorial_name || "",
  tutorialState: data.state || "",
  availableAttributes: data.available_attributes || [],
  questions: data.questions || [],
  ...mapTimer(data.timer),
  round: data.round ?? 0,
  studentName: data.username || "",
  attributes: data.attributes || {},
  sharedAttributes: data.shared_attributes || [],
  attributesComplete: !!data.attributes_complete,
  studentCount: data.student_count || 0,
  groupNumber: data.group_number ?? null,
  groupMembers: data.group_members || [],
  formation: data.formation ?? 0,
});

const mapStaffUpdate = (data) => ({
  tutorialCode: data.tutorial_code || "",
  tutorialName: data.tutorial_name || "",
  tutorialState: data.state || "",
  availableAttributes: data.available_attributes || [],
  questions: data.questions || [],
  ...mapTimer(data.timer),
  round: data.round ?? 0,
  locked: !!data.locked,
  students: data.students || {},
  groups: data.groups || {},
  groupSize: data.group_size ?? null,
  maxGroups: data.max_groups ?? null,
});


export function TutorialProvider({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  const { token, loading: authLoading, logout } = useAuth();

  // The Active Socket Namespace follows the Current Page (staff pages use the staff namespace),
  // and Staff Pages only Connect once Signed In (reconnecting if the sign in changes)
  const onStaffPage = location.pathname.startsWith("/staff");
  const namespace = onStaffPage ? STAFF_NAMESPACE : STUDENT_NAMESPACE;
  const connectionKey = !onStaffPage ? "student" : (!authLoading && token ? `staff:${token}` : null);

  const [tutorial, setTutorial] = useState(INITIAL_TUTORIAL);
  const [connected, setConnected] = useState(false);
  const [connectionLost, setConnectionLost] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);
  const [toasts, setToasts] = useState([]);

  const navigateRef = useRef(navigate);
  const logoutRef = useRef(logout);
  const tutorialCodeRef = useRef("");
  const activeKey = useRef(undefined);
  const activeNamespace = useRef(null);
  const attachedNamespaces = useRef(new Set());

  useEffect(() => {
    navigateRef.current = navigate;
    logoutRef.current = logout;
    tutorialCodeRef.current = tutorial.tutorialCode;
  }, [navigate, logout, tutorial.tutorialCode]);


  // Notifications
  const dismissToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  // A Duration of null stays until it is Dismissed
  const notify = useCallback((message, type = "info", duration = 4500) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((current) => [...current.slice(-2), { id, message, type }]);
    if (duration !== null) setTimeout(() => dismissToast(id), duration);
  }, [dismissToast]);


  // Socket Listeners are attached once per Namespace, and only update state while that Namespace is active
  const attachListeners = useCallback((ns) => {
    const socket = getSocket(ns);
    if (attachedNamespaces.current.has(ns)) return socket;
    attachedNamespaces.current.add(ns);

    const isActive = () => activeNamespace.current === ns;
    const homePath = ns === STAFF_NAMESPACE ? "/staff/" : "/";

    // Navigation is applied as a transition, so clearing the Tutorial is too, letting both happen together
    // (otherwise the student's tutorial page would see it isn't in the session and join it again)
    const exitTutorial = () => {
      navigateRef.current(homePath);
      startTransition(() => setTutorial(INITIAL_TUTORIAL));
    };

    socket.on("connect", () => {
      if (!isActive()) return;
      setConnected(true);
      setConnectionLost(false);
    });

    socket.on("disconnect", (reason) => {
      if (!isActive()) return;
      setConnected(false);
      if (reason !== "io client disconnect") setConnectionLost(true);
    });

    socket.on("connect_error", (error) => {
      if (!isActive()) return;

      // The Server refuses Staff whose Sign In has expired or is no longer valid
      if (ns === STAFF_NAMESPACE && error?.message === "unauthorized") {
        logoutRef.current();
        notify("Your Staff Sign In has Expired. Please Sign In again.", "error", 6000);
        return;
      }
      setConnectionLost(true);
    });

    socket.on("session", (data) => {
      if (ns === STUDENT_NAMESPACE) setStudentId(data?.uuid);
      if (!isActive()) return;

      if (data?.code) {
        setTutorial((current) => ({ ...current, tutorialCode: data.code }));
      } else {
        // Students are told by the Tutorial Page
        if (ns === STAFF_NAMESPACE && tutorialCodeRef.current) notify(SESSION_LOST, "error", null);
        setTutorial(INITIAL_TUTORIAL);
      }
      setSessionReady(true);
    });

    socket.on("error", (error) => {
      if (isActive() && error?.message) notify(error.message, "error");
    });

    socket.on("timer_notification", (data) => {
      if (!isActive()) return;
      notify(data?.message || "Time's up!", "info", 8000);
      try {
        navigator.vibrate?.([200, 100, 200]);
      } catch {
        // Vibration not supported
      }
    });

    socket.on("tutorial_ended", (data) => {
      if (!isActive()) return;
      if (data?.reason === "idle") {
        notify("The Session was Closed as it hadn't been used for a while.", "info", null);
      } else {
        notify(
          ns === STAFF_NAMESPACE
            ? "The Tutorial Session has Ended."
            : "Your Tutor has Ended the Session. Thanks for Taking Part!",
          "info"
        );
      }
      exitTutorial();
    });

    if (ns === STUDENT_NAMESPACE) {
      socket.on("tutorial_joined", (data) => {
        if (isActive()) setTutorial((current) => ({ ...current, tutorialCode: data?.tutorial_code || "" }));
      });

      socket.on("left_tutorial", (data) => {
        if (!isActive()) return;
        if (data?.removed) notify("Your Tutor Removed you from the Session.", "info", 8000);
        exitTutorial();
      });

      socket.on("student_update", (data) => {
        if (isActive()) setTutorial((current) => ({ ...current, ...mapStudentUpdate(data) }));
      });
    } else {
      socket.on("tutorial_created", (data) => {
        if (isActive()) setTutorial((current) => ({ ...current, tutorialCode: data?.tutorial_code || "" }));
      });

      socket.on("tutorial_update", (data) => {
        if (isActive()) setTutorial((current) => ({ ...current, ...mapStaffUpdate(data) }));
      });
    }

    return socket;
  }, [notify]);


  // Connect to the Namespace for the Current Page, Disconnecting from the Other
  useEffect(() => {
    if (activeKey.current === connectionKey) return;
    activeKey.current = connectionKey;

    const previous = activeNamespace.current;
    const next = connectionKey ? namespace : null;
    activeNamespace.current = next;
    if (previous) getSocket(previous).disconnect();

    setTutorial(INITIAL_TUTORIAL);
    setSessionReady(false);
    setConnected(false);
    setConnectionLost(false);

    if (next) attachListeners(next).connect();
  }, [connectionKey, namespace, attachListeners]);


  // Student Actions (each resolves with the server's acknowledgement)
  const enterTutorial = useCallback(async (code) => {
    const response = await emitWithAck(STUDENT_NAMESPACE, "enter_tutorial", { code });
    if (response.ok) setTutorial((current) => ({ ...current, tutorialCode: response.tutorial_code }));
    return response;
  }, []);

  const updateDetails = useCallback((details) => emitWithAck(STUDENT_NAMESPACE, "update_details", details), []);
  const confirmDetails = useCallback(() => emitWithAck(STUDENT_NAMESPACE, "confirm_details"), []);
  const leaveTutorial = useCallback(() => emitWithAck(STUDENT_NAMESPACE, "leave_tutorial"), []);

  // Staff Actions
  const createTutorial = useCallback(async (settings) => {
    const response = await emitWithAck(STAFF_NAMESPACE, "create_tutorial", settings);
    if (response.ok) setTutorial((current) => ({ ...current, tutorialCode: response.tutorial_code }));
    return response;
  }, []);

  const updateTutorial = useCallback((settings) => emitWithAck(STAFF_NAMESPACE, "update_settings", settings), []);
  const lockTutorial = useCallback((locked) => emitWithAck(STAFF_NAMESPACE, "lock_tutorial", { locked }), []);
  const removeStudent = useCallback(
    (studentId) => emitWithAck(STAFF_NAMESPACE, "remove_student", { student_id: studentId }),
    []
  );
  const backToLobby = useCallback(() => emitWithAck(STAFF_NAMESPACE, "return_lobby"), []);
  const startGrouping = useCallback(() => emitWithAck(STAFF_NAMESPACE, "start_grouping"), []);
  const startDiscussion = useCallback(() => emitWithAck(STAFF_NAMESPACE, "start_discussion"), []);
  const startTimer = useCallback(() => emitWithAck(STAFF_NAMESPACE, "start_timer"), []);
  const stopTimer = useCallback(() => emitWithAck(STAFF_NAMESPACE, "stop_timer"), []);
  const resetTimer = useCallback(
    (time) => emitWithAck(STAFF_NAMESPACE, "reset_timer", time === undefined ? {} : { time }),
    []
  );
  const adjustTimer = useCallback((seconds) => emitWithAck(STAFF_NAMESPACE, "adjust_timer", { seconds }), []);
  const endTutorial = useCallback(() => emitWithAck(STAFF_NAMESPACE, "end_tutorial"), []);


  const value = useMemo(() => ({
    ...tutorial,
    namespace, connected, connectionLost, sessionReady,
    toasts, notify, dismissToast,
    enterTutorial, updateDetails, confirmDetails, leaveTutorial,
    createTutorial, updateTutorial, lockTutorial, removeStudent, backToLobby, startGrouping, startDiscussion,
    startTimer, stopTimer, resetTimer, adjustTimer, endTutorial,
  }), [
    tutorial, namespace, connected, connectionLost, sessionReady, toasts, notify, dismissToast,
    enterTutorial, updateDetails, confirmDetails, leaveTutorial, createTutorial, updateTutorial,
    lockTutorial, removeStudent, backToLobby, startGrouping, startDiscussion,
    startTimer, stopTimer, resetTimer, adjustTimer, endTutorial,
  ]);

  return (
    <TutorialContext.Provider value={value}>
      {children}
    </TutorialContext.Provider>
  );
}

export const useTutorial = () => useContext(TutorialContext);
