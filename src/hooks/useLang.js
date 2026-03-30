import { useState } from 'react'

export const LANGS = {
  en:'English', hi:'हिन्दी', mr:'मराठी', pa:'ਪੰਜਾਬੀ',
  gu:'ગુજરાતી', ta:'தமிழ்', te:'తెలుగు', kn:'ಕನ್ನಡ', bn:'বাংলা', bh:'भोजपुरी'
}

export const STT_LANG = {
  en:'en-US', hi:'hi-IN', mr:'mr-IN', pa:'pa-IN', gu:'gu-IN',
  ta:'ta-IN', te:'te-IN', kn:'kn-IN', bn:'bn-IN', bh:'hi-IN'
}

export const TTS_LANG = {
  en:'en-IN', hi:'hi-IN', mr:'mr-IN', pa:'pa-IN', gu:'gu-IN',
  ta:'ta-IN', te:'te-IN', kn:'kn-IN', bn:'bn-IN', bh:'hi-IN'
}

export function useLang() {
  const [lang, setLang] = useState(() => localStorage.getItem('krishi_lang') || 'hi')
  const changeLang = l => { setLang(l); localStorage.setItem('krishi_lang', l) }
  return [lang, changeLang]
}
