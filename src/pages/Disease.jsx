import { useState, useEffect, useRef } from 'react'
import { Upload, X } from 'lucide-react'
import { Alert, Spinner } from '../components/UI.jsx'
import api from '../api.js'

const CROPS = ['Wheat','Rice','Tomato','Onion','Cotton','Maize','Soybean','Potato','Sugarcane','Groundnut']

export default function Disease({ lang }) {
  const [crop,     setCrop]     = useState('Wheat')
  const [photo,    setPhoto]    = useState(null)
  const [preview,  setPreview]  = useState('')
  const [symptoms, setSymptoms] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState('')
  const [tab,      setTab]      = useState('scan')
  const [history,  setHistory]  = useState([])
  const [alerts,   setAlerts]   = useState([])
  const fileRef = useRef()

  useEffect(() => {
    api.diseaseHistory().then(d => setHistory(d.history || [])).catch(() => {})
    api.diseaseAlerts('Pune').then(d => setAlerts(d.alerts || [])).catch(() => {})
  }, [])

  const onFile = e => {
    const f = e.target.files[0]
    if (!f) return
    setPhoto(f)
    setPreview(URL.createObjectURL(f))
  }

  const analyse = async () => {
    if (!photo && !symptoms.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      let d
      if (photo) {
        const fd = new FormData()
        fd.append('crop_name', crop)
        fd.append('language', lang)
        fd.append('location', 'Maharashtra')
        fd.append('district', 'Pune')
        fd.append('photo', photo)
        d = await api.diseasePhoto(fd)
      } else {
        d = await api.diseaseText({ crop_name: crop, symptoms, language: lang, location: 'Maharashtra', district: 'Pune' })
      }
      setResult(d); setTab('result')
    } catch(err) { setError(err.message) }
    setLoading(false)
  }

  return (
    <div className="page">
      <h1 className="page-head">🔬 Disease Detector</h1>
      <p className="page-sub">Photo upload karo ya symptoms batao AI diagnosis ke liye</p>

      <div className="grid-2">
        {/* Left: Input */}
        <div style={{display:'flex',flexDirection:'column',gap:16}}>
          <div>
            <label className="input-label">Crop</label>
            <select className="input" value={crop} onChange={e => setCrop(e.target.value)}>
              {CROPS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="input-label">📷 Photo Upload</label>
            <div
              onClick={() => fileRef.current?.click()}
              style={{border:'2px dashed rgba(170,255,68,.25)',borderRadius:16,padding:24,textAlign:'center',cursor:'pointer',background:preview?'transparent':'rgba(255,255,255,.02)'}}
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) { setPhoto(f); setPreview(URL.createObjectURL(f)) } }}
            >
              {preview
                ? <img src={preview} alt="preview" style={{maxHeight:160,borderRadius:10,display:'block',margin:'0 auto'}}/>
                : <>
                    <Upload size={32} style={{color:'var(--lime)',margin:'0 auto 8px',display:'block'}}/>
                    <div style={{fontSize:14,color:'var(--text2)'}}>Click or drag photo here</div>
                    <div style={{fontSize:11,color:'var(--text3)',marginTop:4}}>JPG, PNG · max 10MB</div>
                  </>
              }
              <input ref={fileRef} type="file" accept="image/*" style={{display:'none'}} onChange={onFile}/>
            </div>
            {photo && (
              <button onClick={() => { setPhoto(null); setPreview('') }} className="btn btn-ghost btn-sm" style={{marginTop:6}}>
                <X size={12}/> Remove
              </button>
            )}
          </div>

          <div style={{textAlign:'center',color:'var(--text3)',fontSize:12}}>— ya symptoms describe karo —</div>

          <div>
            <label className="input-label">Symptoms</label>
            <textarea className="input" placeholder="e.g. yellow leaves, brown spots…" value={symptoms} onChange={e => setSymptoms(e.target.value)} style={{height:90}}/>
          </div>

          {error && <Alert type="error">{error}</Alert>}

          <button onClick={analyse} disabled={loading || (!photo && !symptoms.trim())} className="btn btn-primary btn-full btn-lg">
            {loading ? <><Spinner size={18}/> Analysing…</> : '🔬 Analyse'}
          </button>
        </div>

        {/* Right: Results */}
        <div>
          <div style={{display:'flex',gap:6,marginBottom:16}}>
            {[['result','📋 Result'],['history','📜 History'],['alerts','⚠️ Alerts']].map(([t,l]) => (
              <button key={t} onClick={() => setTab(t)} className={`btn btn-sm ${tab===t?'btn-primary':'btn-secondary'}`}>{l}</button>
            ))}
          </div>

          {tab === 'result' && result && (
            <div className="card fade-up" style={{borderColor:'rgba(255,181,71,.2)'}}>
              <div style={{fontFamily:'Syne,sans-serif',fontSize:20,fontWeight:700,color:'var(--amber)',marginBottom:12}}>🦠 {result.disease_name}</div>
              <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:14}}>
                <span className="chip chip-amber">Confidence: {result.confidence}</span>
                <span className="chip chip-rose">Severity: {result.severity}</span>
              </div>
              {result.treatment_steps?.map((s, i) => (
                <div key={i} style={{display:'flex',gap:10,marginBottom:6,fontSize:13}}>
                  <span style={{color:'var(--lime)',fontWeight:700,minWidth:20}}>{i+1}.</span>
                  <span>{s}</span>
                </div>
              ))}
              {result.organic_option && <Alert type="success" style={{marginTop:12}}>🌿 {result.organic_option}</Alert>}
              {result.prevention     && <Alert type="info"    style={{marginTop:8}} >💡 {result.prevention}</Alert>}
            </div>
          )}
          {tab === 'result' && !result && (
            <div style={{textAlign:'center',padding:60,color:'var(--text3)',fontSize:14}}>📸 Photo ya symptoms daalo</div>
          )}

          {tab === 'history' && (
            <div style={{display:'flex',flexDirection:'column',gap:8}}>
              {history.length === 0
                ? <div style={{color:'var(--text3)',textAlign:'center',padding:40}}>No scans yet.</div>
                : history.map((h, i) => (
                    <div key={i} className="card" style={{padding:'12px 16px'}}>
                      <div style={{display:'flex',gap:10}}>
                        <span style={{fontSize:22}}>{h.source==='photo'?'📷':'📝'}</span>
                        <div>
                          <div style={{fontWeight:600,color:'var(--amber)'}}>{h.disease_name}</div>
                          <div style={{fontSize:12,color:'var(--text2)',marginTop:3}}>🌾 {h.crop_name} · {h.severity}</div>
                        </div>
                      </div>
                    </div>
                  ))
              }
            </div>
          )}

          {tab === 'alerts' && (
            <div style={{display:'flex',flexDirection:'column',gap:8}}>
              {alerts.length === 0
                ? <div style={{color:'var(--text3)',textAlign:'center',padding:40}}>No alerts.</div>
                : alerts.map((a, i) => (
                    <div key={i} style={{background:'rgba(255,107,107,.04)',border:'1px solid rgba(255,107,107,.15)',borderRadius:12,padding:'12px 16px'}}>
                      <div style={{fontWeight:600,color:'var(--rose)'}}>⚠️ {a.disease_name}</div>
                      <div style={{fontSize:12,color:'var(--text2)',marginTop:4}}>🌾 {a.crop_name} · {a.severity}</div>
                    </div>
                  ))
              }
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
