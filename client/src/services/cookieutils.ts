type CookieDictionary = Record<string, any>;

export function setCookie(key: string, value: any, days = 30) {
  const encodedValue = encodeURIComponent(JSON.stringify(value));
  const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
  document.cookie = `${key}=${encodedValue}; expires=${expires}; path=/`;
}

export function getCookie(key: string): CookieDictionary | null {
  const cookies = document.cookie.split('; ').reduce((acc, cookie) => {
    const [name, value] = cookie.split('=');
    try {
      acc[name] = JSON.parse(decodeURIComponent(value));
    } catch {
      acc[name] = value;
    }
    return acc;
  }, {} as CookieDictionary);

  return cookies[key] ?? null;
}

export function removeCookie(key: string) {
  document.cookie = `${key}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

export function updateCookie(key: string, value: any) {
    const current = getCookie('appData') || {};
    const updated = { ...current, [key]: value };
    setCookie('appData', updated);
}

export function getFromCookie(key: string) {
    const data = getCookie('appData');
    return data?.[key];
  }
  