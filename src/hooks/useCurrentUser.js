import { useCallback, useEffect, useState } from 'react';
import { getCurrentUser } from '../api/auth/authApi';

export default function useCurrentUser() {
  const [currentUser, setCurrentUser] = useState(null);

  const loadCurrentUser = useCallback(async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
      return user;
    } catch (err) {
      console.error('Failed to load current user:', err);
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;

    getCurrentUser()
      .then((user) => {
        if (active) {
          setCurrentUser(user);
        }
      })
      .catch((err) => {
        console.error('Failed to load current user:', err);
      });

    return () => {
      active = false;
    };
  }, []);

  return {
    currentUser,
    isAdmin: currentUser?.role === 'admin',
    loadCurrentUser,
  };
}
