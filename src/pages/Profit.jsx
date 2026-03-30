import { useState } from 'react'
import { Spinner, Alert, Metric } from '../components/UI.jsx'
import api from '../api.js'

export default function Profit({ lang }) {
  const [crop,  setCrop]  = useState('Wheat')
  const [area,  setArea]  = useState(1)
  const [unit,  setUnit]  = useState('acre')
  const [seed,  setSeed]  = useState(1200)
  const [fert,  setFert]  = useState(1800)
  const [pest,  setPest]  = useState(600)
  const [labor, setLabor] = useState(2000)
  const [irrig, setIrrig] = useState(500)
  const [misc,  setMisc]  = useState(400)
  const [yld,   setYld]   = useState(10)
  const [price, setPrice] = useState(2300)
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)

  const calc = async () => {
    setLoading(true)
    try {
      setResult(await api.profit({
        crop, area, unit,
        seed_cost: seed, fertilizer_cost: fert, pesticide_cost: pest,
        labor_cost: labor, irrigation_cost: irrig, misc_cost: misc,
        expected_yield_q: yld, expected_price_per_q: price, language: lang
      }))
    } catch(e) {}
    setLoading(false)
  }

  const profitPos = parseFloat(String(result?.profit || '').replace(/[₹,]/g, '')) > 0

  return (
    <div className="page">
      <h1 className="page-head">💰 Profit Calculator</h1>
      <p className="page-sub">Net profit aur ROI calculate karo</p>
      <div className="grid-2">
        <div style={{display:'flex',flexDirection:'column',gap:12}}>
          <div className="grid-2">
            <div>
              <label className="input-label">Crop</label>
              <input className="input" value={crop} onChange={e => setCrop(e.target.value)}/>
            </div>
            <div>
              <label className="input-label">Area</label>
              <input className="input" type="number" value={area} min={0.1} step={0.1} onChange={e => setArea(Number(e.target.value))}/>
            </div>
          </div>

          <div style={{fontWeight:600,fontSize:13,color:'var(--text2)'}}>Costs (₹/acre)</div>
          <div className="grid-2">
            {[['Seed',seed,setSeed],['Fertilizer',fert,setFert],['Pesticide',pest,setPest],['Labor',labor,setLabor],['Irrigation',irrig,setIrrig],['Misc',misc,setMisc]].map(([l,v,s]) => (
              <div key={l}>
                <label className="input-label">{l}</label>
                <input className="input" type="number" value={v} step={50} onChange={e => s(Number(e.target.value))}/>
              </div>
            ))}
          </div>

          <div style={{fontWeight:600,fontSize:13,color:'var(--text2)'}}>Revenue</div>
          <div className="grid-2">
            <div>
              <label className="input-label">Yield (q/acre)</label>
              <input className="input" type="number" value={yld} step={0.5} onChange={e => setYld(Number(e.target.value))}/>
            </div>
            <div>
              <label className="input-label">Price (₹/q)</label>
              <input className="input" type="number" value={price} step={50} onChange={e => setPrice(Number(e.target.value))}/>
            </div>
          </div>

          <button onClick={calc} disabled={loading} className="btn btn-primary btn-full btn-lg">
            {loading ? <Spinner size={18}/> : '💰 Calculate'}
          </button>
        </div>

        {result && (
          <div className="fade-up">
            <div className="grid-2" style={{marginBottom:14}}>
              <Metric label="Total Cost"   value={result.total_cost}/>
              <Metric label="Revenue"      value={result.revenue}/>
              <Metric label="Net Profit"   value={result.profit} delta={`${result.roi_percent}% ROI`} deltaType={profitPos?'up':'down'}/>
              <Metric label="Break-even"   value={result.break_even_price_per_q}/>
            </div>
            <Alert type={profitPos ? 'success' : 'warn'}>
              {profitPos ? `✅ Profitable! ${result.profit}` : '⚠️ Is price pe loss ho sakta hai.'}
            </Alert>
          </div>
        )}
      </div>
    </div>
  )
}
