export function getLocalStorageItem(key: string) {  // TODO: maybe wrap in custom hook (see ds. answ.)
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
}

export function setLocalStorageItem<T>(key: string, value: T) {
    localStorage.setItem(key, JSON.stringify(value));
}
