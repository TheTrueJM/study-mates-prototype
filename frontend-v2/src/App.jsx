import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { TutorialProvider } from "./context/TutorialContext";
import { getStaffToken } from "./api/staff";
import Login from "./pages/staff/Login";
import TutorialSetup from "./pages/staff/TutorialSetup";
import LobbyLayout from "./pages/staff/LobbyLayout";
import GroupsLayout from "./pages/staff/GroupsLayout";
import DiscussionLayout from "./pages/staff/DiscussionLayout";
import JoinTutorial from "./pages/student/JoinTutorial";
import EnterDetails from "./pages/student/EnterDetails";
import StudentLobbyLayout from "./pages/student/LobbyLayout";
import StudentGroupsLayout from "./pages/student/GroupsLayout";
import StudentDiscussionLayout from "./pages/student/DiscussionLayout";
import NotFound from "./pages/NotFound";

function StaffProtectedRoute({ children }) {
    return getStaffToken() ? children : <Navigate to="/staff/login" />;
}

function StudentRoute({ children }) {
    // Student auth is via Socket.IO, not route-based
    // The TutorialContext handles this
    return children;
}

export default function App() {
    return (
        <BrowserRouter>
            <TutorialProvider>
                <Routes>
                    {/* Staff Routes */}
                    <Route path="/staff/login" element={<Login />} />
                    <Route path="/staff/setup" element={
                        <StaffProtectedRoute><TutorialSetup /></StaffProtectedRoute>
                    } />
                    <Route path="/staff/tutorial" element={
                        <StaffProtectedRoute><LobbyLayout /></StaffProtectedRoute>
                    } />
                    
                    {/* Student Routes */}
                    <Route path="/" element={<JoinTutorial />} />
                    <Route path="/enter-details" element={<EnterDetails />} />
                    <Route path="/lobby" element={<StudentLobbyLayout />} />
                    <Route path="/groups" element={<StudentGroupsLayout />} />
                    <Route path="/discussion" element={<StudentDiscussionLayout />} />
                    
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </TutorialProvider>
        </BrowserRouter>
    );
}