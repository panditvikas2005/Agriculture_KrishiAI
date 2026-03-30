import { useState, useEffect, useRef } from 'react'
import { Send, Trash2, Volume2, VolumeX } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { Spinner } from '../components/UI.jsx'
import { LANGS, STT_LANG } from '../hooks/useLang.js'
import { speakWithVoice } from '../hooks/useSpeakTTS.js'
import api from '../api.js'

export default function Chat({ lang }) {
  const { user } = useAuth()
  const [messages,  setMessages]  = useState([])
  const [input,     setInput]     = useState('')
  const [loading,   setLoading]   = useState(false)
  const [voiceOn,   setVoiceOn]   = useState(false)
  const [listening, setListening] = useState(false)
  const [micErr,    setMicErr]    = useState('')
  const recogRef = useRef(null)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:'smooth' }) }, [messages])

  const toggleMic = () => {
    setMicErr('')
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) { setMicErr('❌ Chrome browser use karo mic ke liye'); return }

    if (listening) { recogRef.current?.stop(); setListening(false); return }

    const r = new SR()
    r.lang           = STT_LANG[lang] || 'hi-IN'
    r.continuous     = false
    r.interimResults = true

    r.onstart  = () => setListening(true)
    r.onend    = () => setListening(false)
    r.onerror  = (e) => {
      const msg = {
        'network':     '⚠️ Mic ke liye Chrome ko internet chahiye. Ya HTTPS pe host karo.',
        'not-allowed': '🔒 Mic ki permission do — address bar mein lock icon click karo.',
        'no-speech':   '🔇 Kuch suna nahi — thoda aur zor se bolo.',
      }[e.error] || ('⚠️ Mic error: ' + e.error)
      setMicErr(msg); setListening(false)
    }
    r.onresult = (e) => {
      const txt = Array.from(e.results).map(r => r[0].transcript).join(' ').trim()
      setInput(txt)
      if (e.results[e.results.length - 1].isFinal && txt) {
        setListening(false)
        setTimeout(() => sendMsg(txt), 350)
      }
    }
    recogRef.current = r
    r.start()
  }

  const sendMsg = async (text) => {
    const t = typeof text === 'string' ? text : input
    if (!t.trim() || loading) return
    setMessages(p => [...p, { role:'user', text: t.trim() }])
    setInput(''); setLoading(true)
    try {
      const d = await api.chat({
        model_name: 'llama-3.3-70b-versatile',
        messages: [t.trim()],
        allow_search: true,
        language: lang,
        farmer_name: user?.name || 'Farmer',
        location: user?.location || 'Pune, Maharashtra'
      })
      setMessages(p => [...p, { role:'bot', text: d.response }])
      if (voiceOn) speakWithVoice(d.response, lang)
    } catch(err) {
      setMessages(p => [...p, { role:'bot', text:'⚠️ '+err.message, error:true }])
    }
    setLoading(false)
  }

  const suggestions = [
    '🌾 Maharashtra mein summer ke liye best crop?',
    '🦠 Gehu ke patte peele ho rahe hain — kya bimari?',
    '💊 Tamatar ke liye flowering stage mein fertilizer?'
  ]

  return (
    <div className="page" style={{display:'flex',flexDirection:'column',height:'calc(100vh - 120px)'}}>
      {/* Header */}
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:12}}>
        <div>
          <h1 className="page-head">💬 AI Advisor</h1>
          <p className="page-sub">Type karo ya 🎤 mic dabao — kisi bhi language mein</p>
        </div>
        <div style={{display:'flex',gap:8,alignItems:'center'}}>
          <button
            onClick={() => { setVoiceOn(v => !v); if (voiceOn) window.speechSynthesis?.cancel() }}
            className={`btn btn-sm ${voiceOn ? 'btn-primary' : 'btn-ghost'}`}
          >
            {voiceOn ? <Volume2 size={14}/> : <VolumeX size={14}/>}
            {voiceOn ? 'Awaaz On' : 'Awaaz Off'}
          </button>
          {messages.length > 0 && (
            <button onClick={() => setMessages([])} className="btn btn-ghost btn-sm">
              <Trash2 size={14}/> Clear
            </button>
          )}
        </div>
      </div>

      {voiceOn && (
        <div style={{background:'rgba(170,255,68,.05)',border:'1px solid rgba(170,255,68,.15)',borderRadius:10,padding:'8px 14px',marginBottom:10,fontSize:12,color:'var(--lime)',display:'flex',alignItems:'center',gap:8}}>
          <Volume2 size={13}/>
          <span>AI ka jawab bol ke aayega • Windows → Settings → Language mein Hindi voice install karo</span>
        </div>
      )}

      {/* Messages */}
      <div style={{flex:1,overflowY:'auto',display:'flex',flexDirection:'column',gap:8,paddingRight:4,marginBottom:12}}>
        {messages.length === 0 && (
          <div style={{margin:'auto',textAlign:'center',padding:40}}>
            <div style={{fontSize:48,marginBottom:16}}>🌿</div>
            <div style={{fontSize:16,fontWeight:600,marginBottom:8}}>KrishiAI se kuch bhi pucho</div>
            <div style={{fontSize:13,color:'var(--text2)',marginBottom:24}}>Type karo ya neeche 🎤 mic button dabao</div>
            <div style={{display:'flex',flexDirection:'column',gap:8,maxWidth:420,margin:'0 auto'}}>
              {suggestions.map(s => (
                <button key={s} onClick={() => sendMsg(s)} className="btn btn-secondary btn-sm" style={{textAlign:'left',justifyContent:'flex-start'}}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{display:'flex',justifyContent:m.role==='user'?'flex-end':'flex-start',animation:'fadeUp .25s ease both'}}>
            <div style={{maxWidth:'72%',padding:'13px 18px',fontSize:14,lineHeight:1.75,borderRadius:m.role==='user'?'18px 18px 4px 18px':'18px 18px 18px 4px',background:m.role==='user'?'linear-gradient(135deg,rgba(170,255,68,.12),rgba(0,212,170,.07))':m.error?'rgba(255,107,107,.07)':'rgba(255,255,255,.05)',border:m.role==='user'?'1px solid rgba(170,255,68,.2)':m.error?'1px solid rgba(255,107,107,.2)':'1px solid rgba(255,255,255,.08)',color:m.error?'var(--rose)':'var(--text)'}}>
              {m.role === 'bot' && <span style={{marginRight:8}}>🌿</span>}
              <span style={{whiteSpace:'pre-wrap'}}>{m.text}</span>
              {m.role === 'user' && <span style={{marginLeft:8}}>👨‍🌾</span>}
              {m.role === 'bot' && voiceOn && (
                <button onClick={() => speakWithVoice(m.text, lang)} style={{display:'block',marginTop:6,background:'none',border:'none',cursor:'pointer',color:'var(--lime)',fontSize:11,padding:0}}>▶ Dobara suno</button>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{display:'flex',gap:8,padding:'13px 18px',background:'rgba(255,255,255,.04)',borderRadius:'18px 18px 18px 4px',border:'1px solid rgba(255,255,255,.07)',width:'fit-content'}}>
            <span>🌿</span>
            {[0,1,2].map(i => <div key={i} style={{width:7,height:7,borderRadius:'50%',background:'var(--lime)',animation:'pulse .8s ease infinite',animationDelay:`${i*.2}s`}}/>)}
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Input Bar */}
      <div>
        {micErr && (
          <div style={{fontSize:12,color:'var(--rose)',marginBottom:6,padding:'6px 10px',background:'rgba(255,107,107,.07)',borderRadius:8,display:'flex',justifyContent:'space-between'}}>
            <span>{micErr}</span>
            <button onClick={() => setMicErr('')} style={{background:'none',border:'none',cursor:'pointer',color:'var(--rose)'}}>✕</button>
          </div>
        )}
        <div style={{display:'flex',gap:8,alignItems:'center'}}>
          <button onClick={toggleMic}
            style={{width:48,height:48,borderRadius:'50%',border:'none',flexShrink:0,cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',fontSize:22,transition:'all .25s',background:listening?'linear-gradient(135deg,#ff6b6b,#cc2222)':'linear-gradient(135deg,#aaff44,#55cc00)',boxShadow:listening?'0 0 24px rgba(255,107,107,.6), 0 0 0 4px rgba(255,107,107,.15)':'0 4px 16px rgba(170,255,68,.4)',animation:listening?'pulse .8s ease infinite':'none'}}
          >
            {listening ? '⏹' : '🎤'}
          </button>
          <input className="input"
            style={{flex:1,fontSize:15,height:48,transition:'all .2s',borderColor:listening?'rgba(255,107,107,.5)':undefined,boxShadow:listening?'0 0 0 3px rgba(255,107,107,.08)':undefined}}
            placeholder={listening ? '🎤 Sun raha hoon... bolo' : `Type ya 🎤 dabao (${LANGS[lang]})`}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMsg(input)}
          />
          <button onClick={() => sendMsg(input)} disabled={loading || !input.trim()} className="btn btn-primary" style={{height:48,padding:'0 22px',flexShrink:0}}>
            <Send size={16}/>
          </button>
        </div>
        {listening && (
          <div style={{textAlign:'center',marginTop:8,fontSize:12,color:'var(--rose)',fontWeight:600,animation:'blink 1s step-end infinite'}}>
            🎤 Bol rahe ho... rukoge to automatically send ho jayega
          </div>
        )}
      </div>
    </div>
  )
}
