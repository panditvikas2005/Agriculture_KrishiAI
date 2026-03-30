import { useState } from 'react'
import { Spinner, Alert } from '../components/UI.jsx'
import api from '../api.js'

export default function Irrigation({ lang }) {
  const [crop,    setCrop]    = useState('Wheat')
  const [soil,    setSoil]    = useState(45)
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)

  const get = async () => {
    setLoading(true)
    try { setResult(await api.irrigation({ crop, soil_moisture: soil, language: lang })) } catch(e) {}
    setLoading(false)
  }

  return (
    <div className="page">
      <h1 className="page-head">💧 Irrigation Advisor</h1>
      <p className="page-sub">Smart irrigation plan</p>
      <div className="grid-2">
        <div style={{display:'flex',flexDirection:'column',gap:18}}>
          <div>
            <label className="input-label">Crop</label>
            <select className="input" value={crop} onChange={e => setCrop(e.target.value)}>
              {['Wheat','Rice','Tomato','Onion','Cotton','Maize','Sugarcane'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
              <label className="input-label" style={{margin:0}}>Soil Moisture (%)</label>
              <span style={{fontSize:13,fontWeight:700,color:soil>=60?'var(--lime)':soil>=40?'var(--amber)':'var(--rose)'}}>{soil}%</span>
            </div>
            <input type="range" min={10} max={90} value={soil} onChange={e => setSoil(Number(e.target.value))}/>
          </div>
          <button onClick={get} disabled={loading} className="btn btn-primary btn-full">
            {loading ? <Spinner size={18}/> : '💧 Get Plan'}
          </button>
        </div>

        {result && (
          <div className="card fade-up">
            <Alert type="info">{result.why}</Alert>
            {result.schedule?.map((d, i) => (
              <div key={i} style={{fontSize:13,padding:'5px 0',color:'var(--text2)',borderBottom:'1px solid rgba(255,255,255,.05)'}}>📅 {d}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
