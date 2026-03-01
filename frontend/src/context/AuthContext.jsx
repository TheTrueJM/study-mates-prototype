import React, { createContext, useState, useCallback, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [studentDetails, setStudentDetails] = useState(() => {
    const saved = localStorage.getItem("studentDetails");
    return saved ? JSON.parse(saved) : null;
  });
  const [staffStatus, setStaffStatus] = useState(false);
  const [isValidating, setIsValidating] = useState(true);

  // Validate staff authentication on app load
  useEffect(() => {
    validateStaffStatus();
  }, []);

  const validateStaffStatus = useCallback(async () => {
    setIsValidating(true);
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

    try {
      const res = await fetch(`${BACKEND_URL}/staff/status`, {
        credentials: 'include',
      });

      if (res.ok) {
        const data = await res.json();
        
        if (data.authenticated) {
          setStaffStatus(true)
          setStudentDetails(null)
        } else {
          setStaffStatus(false)
        }
      }
    } catch (error) {
      console.error('Session validation error:', error);
    } finally {
      setIsValidating(false);
    }
  }, []);

  const setStudent = useCallback((details) => {
    setStudentDetails(details);
    if (details) {
      localStorage.setItem("studentDetails", JSON.stringify(details));
    }
    setStaffStatus(false);
  }, []);

  const setStaff = useCallback(() => {
    setStaffStatus(true);
    setStudentDetails(null);
  }, []);

  const logout = useCallback(async () => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
    
    try {
      await fetch(`${BACKEND_URL}/staff/logout`, {
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    }

    localStorage.removeItem("studentDetails");
    setStudentDetails(null);
    setStaffStatus(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        studentDetails,
        staffStatus,
        isValidating,
        setStudent,
        setStaff,
        logout,
        validateStaffStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
