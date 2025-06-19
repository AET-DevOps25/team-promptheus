import { useState } from "react";




export function getLocalStorageItem(key: string) {  // TODO: maybe wrap in custom hook (see ds. answ.)
  //const [storedValue, setStoredValue] = useState<T>(() => {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;

}

export function setLocalStorageItem<T>(key: string, value: T) {
  //const [storedValue, setStoredValue] = useState<T>(() => {
    localStorage.setItem(key, JSON.stringify(value));
}


// TODO: ask about efficiency / potential problems with 
// Here we handle all the hooks
...
  // Load selected user from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("selectedGitHubUser")
    if (saved) {
      setSelectedUser(JSON.parse(saved))
    }
  }, [])

  // Listen for storage changes to update across tabs
  useEffect(() => {
    const handleStorageChange = () => {
      const saved = localStorage.getItem("selectedGitHubUser")
      setSelectedUser(saved ? JSON.parse(saved) : null)
    }

    window.addEventListener("storage", handleStorageChange)
    window.addEventListener("selectedUserChanged", handleStorageChange)

    return () => {
      window.removeEventListener("storage", handleStorageChange)
      window.removeEventListener("selectedUserChanged", handleStorageChange)
    }
  }, [])