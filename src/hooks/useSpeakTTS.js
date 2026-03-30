import { TTS_LANG } from './useLang.js'

export async function speakWithVoice(text, lang) {
  const clean = text
    .replace(/\*\*/g, '').replace(/\*/g, '').replace(/_/g, '')
    .replace(/#+\s/g, '').replace(/`/g, '').replace(/>/g, '')
    .replace(/\n+/g, '. ').trim().slice(0, 500)

  console.log('🔊 TTS Request:', { text: clean.slice(0, 50) + '...', language: lang })

  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: clean, language: lang }),
    })

    console.log('🔊 TTS Response status:', res.status)

    if (res.ok) {
      const data = await res.json()
      const b64  = data.audio_base64
      if (b64) {
        const binary = atob(b64)
        const bytes  = new Uint8Array(binary.length)
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
        const blob  = new Blob([bytes], { type: 'audio/wav' })
        const url   = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audio.play()
        audio.onended = () => URL.revokeObjectURL(url)
        console.log('🔊 Playing Sarvam audio successfully')
        return
      }
    } else {
      const errorText = await res.text()
      console.error('🔊 Sarvam TTS error:', res.status, errorText)
    }
  } catch (e) {
    console.warn('🔊 Sarvam TTS failed, using browser fallback:', e.message)
  }

  // Fallback: Browser Web Speech API
  console.log('🔊 Using browser fallback TTS for language:', lang)
  if (!window.speechSynthesis) {
    console.error('🔊 Browser speech synthesis not available')
    return
  }
  const langCode = TTS_LANG[lang] || 'hi-IN'
  const doSpeak = (voices) => {
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(clean)
    u.lang = langCode; u.rate = 0.85; u.pitch = 1.05
    const best = voices.find(v => v.lang === langCode)
               || voices.find(v => v.lang.startsWith(langCode.slice(0,5)))
               || voices.find(v => v.lang.startsWith(langCode.slice(0,2)))
    if (best) {
      u.voice = best
      console.log('🔊 Using voice:', best.name)
    } else {
      console.warn('🔊 No matching voice found for:', langCode)
    }
    window.speechSynthesis.speak(u)
  }
  const voices = window.speechSynthesis.getVoices()
  if (voices.length > 0) doSpeak(voices)
  else window.speechSynthesis.addEventListener('voiceschanged', function h() {
    doSpeak(window.speechSynthesis.getVoices())
    window.speechSynthesis.removeEventListener('voiceschanged', h)
  })
}
