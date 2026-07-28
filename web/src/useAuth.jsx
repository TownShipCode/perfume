import { createContext, useContext, useState, useEffect } from 'react';
import { getToken, getRole, getName, getAgentCode, clearToken } from './api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = getToken();
    if (t) {
      setUser({
        role: getRole(),
        name: getName(),
        agent_code: getAgentCode(),
      });
    }
    setLoading(false);
  }, []);

  const logout = () => { clearToken(); setUser(null); };

  return (
    <AuthCtx.Provider value={{ user, setUser, logout, loading }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  return useContext(AuthCtx);
}
