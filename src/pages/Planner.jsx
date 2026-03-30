import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { Spinner } from '../components/UI.jsx'
import api from '../api.js'

export default function Planner({ lang }) {
  const [crop,    setCrop]    = useState('Wheat')
  const [stage,   setStage]   = useState('Tillering')
  const [area,    setArea]    = useState(1)
  const [unit,    setUnit]    = useState('acre')
  const [organic, setOrganic] = useState(false)
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)

  const get = async () => {
    setLoading(true)
    try { setResult(await api.fertilizer({ crop, stage, area, unit, organic_only: organic, language: lang })) } catch(e) {}
    setLoading(false)
  }

  return (
    <div className="page">
      <h1 className="page-head">🌱 Fertilizer Planner</h1>
      <p className="page-sub">Full fertilizer schedule with costs</p>
      <div className="grid-2">
        <div style={{display:'flex',flexDirection:'column',gap:14}}>
          <div className="grid-2">
            <div>
              <label className="input-label">Crop</label>
              <select className="input" value={crop} onChange={e => setCrop(e.target.value)}>
                {['Wheat','Rice','Tomato','Cotton','Maize','Onion'].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="input-label">Stage</label>
              <select className="input" value={stage} onChange={e => setStage(e.target.value)}>
                {['Seedling','Tillering','Vegetative','Flowering','Maturity'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="grid-2">
            <div>
              <label className="input-label">Area</label>
              <input className="input" type="number" value={area} min={0.1} step={0.1} onChange={e => setArea(Number(e.target.value))}/>
            </div>
            <div>
              <label className="input-label">Unit</label>
              <select className="input" value={unit} onChange={e => setUnit(e.target.value)}>
                <option value="acre">Acre</option>
                <option value="hectare">Hectare</option>
              </select>
            </div>
          </div>
          <label style={{display:'flex',alignItems:'center',gap:10,cursor:'pointer',fontSize:14}}>
            <input type="checkbox" checked={organic} onChange={e => setOrganic(e.target.checked)} style={{width:16,height:16,accentColor:'var(--lime)'}}/>
            🌿 Organic Only
          </label>
          <button onClick={get} disabled={loading} className="btn btn-primary btn-full">
            {loading ? <Spinner size={18}/> : '🌱 Generate Plan'}
          </button>
        </div>

        {result && (
          <div className="fade-up">
            <div className="card" style={{marginBottom:14,borderColor:'rgba(170,255,68,.2)'}}>
              <div style={{fontSize:12,color:'var(--text3)',marginBottom:4}}>💰 Total Cost</div>
              <div style={{fontFamily:'Syne,sans-serif',fontSize:28,fontWeight:700,color:'var(--lime)'}}>{result.total_cost_estimate}</div>
            </div>
            {result.schedule?.map((s, i) => (
              <details key={i} className="card" style={{marginBottom:10,padding:'14px 16px'}}>
                <summary style={{cursor:'pointer',fontWeight:600,fontSize:14,display:'flex',justifyContent:'space-between',listStyle:'none'}}>
                  <span>📅 {s.date} — {s.stage}</span>
                  <ChevronDown size={16} style={{color:'var(--text3)'}}/>
                </summary>
                <div style={{marginTop:10}}>
                  {s.items?.map((it, j) => (
                    <div key={j} style={{fontSize:13,padding:'5px 0',borderBottom:'1px solid rgba(255,255,255,.05)'}}>
                      • <strong>{it.name}</strong> · {it.dose} · <span style={{color:'var(--lime)'}}>{it.cost_estimate}</span>
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
