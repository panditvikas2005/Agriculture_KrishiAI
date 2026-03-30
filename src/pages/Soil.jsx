import { useState } from 'react'
import { Spinner, Alert } from '../components/UI.jsx'
import api from '../api.js'

export default function Soil({ lang }) {
  const [ph,   setPh]   = useState(6.9)
  const [n,    setN]    = useState(45)
  const [p,    setP]    = useState(30)
  const [k,    setK]    = useState(180)
  const [crop, setCrop] = useState('Wheat')
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)

  const analyse = async () => {
    setLoading(true)
    try { setResult(await api.soil({ ph, nitrogen: n, phosphorus: p, potassium: k, crop, language: lang })) } catch(e) {}
    setLoading(false)
  }

  const sc  = result?.health_score || 0
  const clr = sc >= 80 ? 'var(--lime)' : sc >= 60 ? 'var(--amber)' : 'var(--rose)'

  return (
    <div className="page">
      <h1 className="page-head">🧪 Soil Health</h1>
      <p className="page-sub">Soil test values daalo AI recommendations ke liye</p>
      <div className="grid-2">
        <div style={{display:'flex',flexDirection:'column',gap:18}}>
          {[['pH Level',ph,setPh,5,9,0.1],['Nitrogen (mg/kg)',n,setN,10,100,1],['Phosphorus (mg/kg)',p,setP,5,80,1],['Potassium (mg/kg)',k,setK,50,300,1]].map(([label,val,setter,min,max,step]) => (
            <div key={label}>
              <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
                <label className="input-label" style={{margin:0}}>{label}</label>
                <span style={{fontSize:13,fontWeight:700,color:'var(--lime)'}}>{val}</span>
              </div>
              <input type="range" min={min} max={max} step={step} value={val} onChange={e => setter(Number(e.target.value))}/>
            </div>
          ))}
          <div>
            <label className="input-label">Crop</label>
            <select className="input" value={crop} onChange={e => setCrop(e.target.value)}>
              {['Wheat','Rice','Tomato','Cotton','Maize'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <button onClick={analyse} disabled={loading} className="btn btn-primary btn-full">
            {loading ? <Spinner size={18}/> : '🧪 Analyse Soil'}
          </button>
        </div>

        {result && (
          <div className="card fade-up">
            <div style={{textAlign:'center',padding:'16px 0 24px'}}>
              <div style={{fontFamily:'Syne,sans-serif',fontSize:72,fontWeight:800,color:clr,lineHeight:1}}>{sc}</div>
              <div style={{fontSize:14,color:'var(--text2)',marginTop:6}}>/ 100 — {result.status}</div>
            </div>
            {[['Nitrogen',n,100],['Phosphorus',p,80],['Potassium',k,300]].map(([nm,val,mx]) => (
              <div key={nm} style={{marginBottom:14}}>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:13,marginBottom:6}}>
                  <span>{nm}</span><span style={{color:'var(--lime)',fontWeight:600}}>{val}</span>
                </div>
                <div style={{background:'rgba(255,255,255,.06)',borderRadius:4,height:8}}>
                  <div style={{height:8,borderRadius:4,width:`${Math.min(100,(val/mx)*100)}%`,background:'linear-gradient(90deg,var(--teal),var(--lime))',transition:'width .6s'}}/>
                </div>
              </div>
            ))}
            {result.fertilizer_advice && <Alert type="success" style={{marginTop:14}}>💊 {result.fertilizer_advice}</Alert>}
          </div>
        )}
      </div>
    </div>
  )
}
