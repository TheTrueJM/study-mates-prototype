import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import { PublicRoute, ProtectedStudentRoute, ProtectedStaffRoute } from "./components/ProtectedRoute";

// Student pages
import JoinTutorial from "./pages/student/JoinTutorial";
import EnterDetails from "./pages/student/EnterDetails";
import StudentTutorial from './pages/student/Tutorial';

// Staff pages
import Login from './pages/staff/Login';
import TutorialSetup from './pages/staff/TutorialSetup';
import StaffTutorial from './pages/staff/Tutorial';

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Home Route */}
        <Route 
          path="/" 
          element={<PublicRoute> <EnterDetails /> </PublicRoute> } 
        />

        {/* Student Routes */}
        <Route 
          path="/details" 
          element={<PublicRoute> <EnterDetails /> </PublicRoute>} 
        />
        <Route 
          path="/join" 
          element={<ProtectedStudentRoute> <JoinTutorial /> </ProtectedStudentRoute>} 
        />
        <Route 
          path="/tutorial/:code" 
          element={<ProtectedStudentRoute requiresJoin={true}> <StudentTutorial /> </ProtectedStudentRoute>} 
        />

        {/* Staff Routes */}
        <Route 
          path="/staff/login" 
          element={<PublicRoute> <Login /> </PublicRoute>} 
        />
        <Route 
          path="/staff/" 
          element={<ProtectedStaffRoute> <TutorialSetup /> </ProtectedStaffRoute>} 
        />
        <Route 
          path="/staff/tutorial/:code" 
          element={ <ProtectedStaffRoute> <StaffTutorial /> </ProtectedStaffRoute>} 
        />
      </Routes>
    </>
  );
}

export default App;
