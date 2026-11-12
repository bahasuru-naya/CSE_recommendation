import React, { createContext, useContext, useState, useEffect } from 'react';

const BeginnerModeContext = createContext();

export function BeginnerModeProvider({ children }) {
  const [isBeginnerMode, setIsBeginnerMode] = useState(() => {
    try {
      const saved = localStorage.getItem('cse_beginner_mode');
      return saved !== null ? JSON.parse(saved) : true; // Default to Beginner-Friendly
    } catch (e) {
      return true;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('cse_beginner_mode', JSON.stringify(isBeginnerMode));
    } catch (e) {
      // Ignore localStorage errors
    }
  }, [isBeginnerMode]);

  const toggleBeginnerMode = () => setIsBeginnerMode((prev) => !prev);

  return (
    <BeginnerModeContext.Provider value={{ isBeginnerMode, setIsBeginnerMode, toggleBeginnerMode }}>
      {children}
    </BeginnerModeContext.Provider>
  );
}

export function useBeginnerMode() {
  const context = useContext(BeginnerModeContext);
  if (!context) {
    return { isBeginnerMode: true, toggleBeginnerMode: () => {} };
  }
  return context;
}
