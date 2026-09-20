import { createContext, useContext, useState } from 'react';

// Optional stub — swap with real token auth against Django backend later.
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('buildtrack_user')) || null;
    } catch {
      return null;
    }
  });

  const login = (userData, token = 'demo-token') => {
    localStorage.setItem('buildtrack_token', token);
    localStorage.setItem('buildtrack_user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('buildtrack_token');
    localStorage.removeItem('buildtrack_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
