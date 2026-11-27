import { Routes, Route, Navigate } from "react-router-dom";

import { useAuth } from "./contexts/AuthContext";

import Navbar from "./components/Navbar";
import Toaster from "./components/Toaster";
import ConnectionBanner from "./components/ConnectionBanner";

// Student Pages
import JoinTutorial from "./pages/student/JoinTutorial";
import StudentTutorial from "./pages/student/Tutorial";

// Staff Pages
import Login from "./pages/staff/Login";
import Register from "./pages/staff/Register";
import SetupTutorial from "./pages/staff/SetupTutorial";
import StaffTutorial from "./pages/staff/Tutorial";

// Error Pages
import NotFound from "./pages/NotFound";


// ProtectedStudentRoute - Requires Student ...
export function ProtectedStudentRoute({ children }) {
  return children;
}

// ProtectedStaffRoute - Requires Staff Authentication
export function ProtectedStaffRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/staff/login" replace />;
  }

  return children;
}


function App() {
  return (
    <>
      <Navbar />
      <ConnectionBanner />
      <main className="main">
        <Routes>
          {/* Home Route */}
          <Route path="/" element={<JoinTutorial />} />

          {/* Student Routes */}
          <Route path="/join" element={<JoinTutorial />} />
          <Route path="/tutorial/:code"
            element={<ProtectedStudentRoute><StudentTutorial /></ProtectedStudentRoute>}
          />

          {/* Staff Routes */}
          <Route path="/staff/login" element={<Login />} />
          <Route path="/staff/register" element={<Register />} />
          <Route path="/staff/"
            element={<ProtectedStaffRoute><SetupTutorial /></ProtectedStaffRoute>}
          />
          <Route path="/staff/tutorial/:code"
            element={<ProtectedStaffRoute><StaffTutorial /></ProtectedStaffRoute>}
          />

          {/* 404 - Catch All Unspecified Routes */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Toaster />
    </>
  )
}

export default App
