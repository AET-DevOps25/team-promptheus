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
