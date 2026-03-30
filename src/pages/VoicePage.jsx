import { useState, useRef } from 'react'
import { Play, Clock } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { Spinner, Alert } from '../components/UI.jsx'
import { LANGS, STT_LANG } from '../hooks/useLang.js'
import { speakWithVoice } from '../hooks/useSpeakTTS.js'
import api from '../api.js'

export default function VoicePage({ lang }) {
  const { user } = useAuth()
  const [recording,   setRecording]   = useState(false)
  const [processing,  setProcessing]  = useState(false)
  const [transcript,  setTranscript]  = useState('')
  const [aiReply,     setAiReply]     = useState('')
  const [history,     setHistory]     = useState([])
  const [activeLang,  setActiveLang]  = useState(lang)
  const [error,       setError]       = useState('')
  const recogRef = useRef(null)

  const startRec = () => {
    setError(''); setTranscript(''); setAiReply('')
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) { setError('Chrome use karo mic ke liye'); return }
    const r = new SR()
    r.lang           = STT_LANG[activeLang] || 'hi-IN'
    r.continuous     = false
    r.interimResults = false
    r.onresult = async e => {
      const t = Array.from(e.results).map(r => r[0].transcript).join(' ').trim()
      setTranscript(t); setRecording(false)
      if (t) await getReply(t)
    }
    r.onerror = e => {
      setError(e.error === 'network' ? 'Network error — Chrome ko internet chahiye' : '⚠️ ' + e.error)
      setRecording(false)
    }
    r.onend = () => setRecording(false)
    recogRef.current = r
    r.start()
    setRecording(true)
  }

  const stopRec = () => { recogRef.current?.stop(); setRecording(false) }

  const getReply = async (question) => {
    setProcessing(true)
    try {
      const d = await api.chat({
        model_name: 'llama-3.3-70b-versatile',
        messages: [question],
        allow_search: false,
        language: activeLang,
        farmer_name: user?.name || 'Farmer',
        location: user?.location || 'Pune, Maharashtra'
      })
      setAiReply(d.response)
      speakWithVoice(d.response, activeLang)
      setHistory(h => [
        { q: question, a: d.response, lang: activeLang, time: new Date().toLocaleTimeString('hi') },
        ...h.slice(0, 5)
      ])
    } catch(err) { setError(err.message) }
    setProcessing(false)
  }

  return (
    <div className="page">
      <div style={{textAlign:'center',padding:'20px 0 32px'}}>
        <div style={{fontSize:80,marginBottom:12,filter:recording?'drop-shadow(0 0 20px rgba(170,255,68,.6))':'none',animation:recording?'pulse .8s ease infinite':'none',transition:'filter .3s'}}>🎙️</div>
        <h1 style={{fontFamily:'Syne,sans-serif',fontSize:28,fontWeight:800,color:'var(--lime)',marginBottom:8}}>Voice AI Advisor</h1>
        <p style={{color:'var(--text2)',fontSize:15}}>बोलो — AI सुनेगा, समझेगा और जवाब देगा 🌾</p>
      </div>

      <div style={{maxWidth:360,margin:'0 auto 28px'}}>
        <label className="input-label" style={{textAlign:'center',display:'block',marginBottom:8}}>भाषा / Language</label>
        <select className="input" value={activeLang} onChange={e => setActiveLang(e.target.value)}>
          {Object.entries(LANGS).map(([c,n]) => <option key={c} value={c}>{n}</option>)}
        </select>
      </div>

      <div style={{display:'flex',justifyContent:'center',marginBottom:28}}>
        <div style={{position:'relative'}}>
          {recording && [1,2].map(i => (
            <div key={i} style={{position:'absolute',inset:0,borderRadius:'50%',border:'2px solid rgba(170,255,68,.4)',animation:`ripple ${1+i*.4}s ease-out infinite`,animationDelay:`${i*.3}s`}}/>
          ))}
          <button onClick={recording ? stopRec : startRec} disabled={processing}
            style={{width:100,height:100,borderRadius:'50%',border:'none',cursor:'pointer',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:6,fontSize:32,transition:'all .3s',background:recording?'linear-gradient(135deg,#ff6b6b,#cc2222)':'linear-gradient(135deg,#aaff44,#55cc00)',boxShadow:recording?'0 0 30px rgba(255,107,107,.5)':'0 8px 32px rgba(170,255,68,.4)',animation:recording?'glow 1.5s ease infinite':'none'}}
          >
            {processing ? <Spinner size={28}/> : recording ? '⏹' : '🎤'}
            <span style={{fontSize:10,fontWeight:700,color:recording?'white':'#0a1a00'}}>{recording?'STOP':'SPEAK'}</span>
          </button>
        </div>
      </div>

      {error && <Alert type="error" onClose={() => setError('')}>{error}</Alert>}

      {(transcript || aiReply) && (
        <div style={{maxWidth:640,margin:'0 auto',display:'flex',flexDirection:'column',gap:14}}>
          {transcript && (
            <div className="card fade-up" style={{borderColor:'rgba(170,255,68,.2)'}}>
              <div style={{fontSize:11,fontWeight:700,color:'var(--lime)',marginBottom:8,letterSpacing:'.08em'}}>🎤 YOU SAID</div>
              <div style={{fontSize:17,lineHeight:1.6}}>{transcript}</div>
            </div>
          )}
          {aiReply && (
            <div className="card fade-up" style={{borderColor:'rgba(0,212,170,.2)'}}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:8}}>
                <div style={{fontSize:11,fontWeight:700,color:'var(--teal)',letterSpacing:'.08em'}}>🌿 KRISHIAI SAYS</div>
                <button onClick={() => speakWithVoice(aiReply, activeLang)} className="btn btn-ghost btn-sm" style={{padding:'4px 8px'}}>
                  <Play size={12}/> Replay
                </button>
              </div>
              <div style={{fontSize:16,lineHeight:1.75}}>{aiReply}</div>
            </div>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div style={{maxWidth:640,margin:'28px auto 0'}}>
          <div className="divider"/>
          <div style={{fontSize:13,color:'var(--text3)',marginBottom:12,display:'flex',alignItems:'center',gap:6}}>
            <Clock size={13}/> Voice History
          </div>
          {history.map((item, i) => (
            <details key={i} style={{background:'rgba(255,255,255,.03)',border:'1px solid var(--border)',borderRadius:12,marginBottom:8,padding:'12px 16px'}}>
              <summary style={{cursor:'pointer',fontSize:14,color:'var(--text2)',listStyle:'none',display:'flex',justifyContent:'space-between'}}>
                <span>🎤 {item.q.slice(0,50)}…</span>
                <span style={{fontSize:11,color:'var(--text3)'}}>{item.time}</span>
              </summary>
              <div style={{marginTop:10,fontSize:14,lineHeight:1.6}}>{item.a}</div>
              <button onClick={() => speakWithVoice(item.a, item.lang)} className="btn btn-ghost btn-sm" style={{marginTop:8}}>
                <Play size={12}/> Replay
              </button>
            </details>
          ))}
        </div>
      )}
    </div>
  )
}
