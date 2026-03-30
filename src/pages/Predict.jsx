import { useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { Spinner, Alert } from '../components/UI.jsx'
import api from '../api.js'

export default function Predict({ lang }) {
  const [crop,   setCrop]   = useState('Tomato')
  const [state,  setState]  = useState('Maharashtra')
  const [days,   setDays]   = useState(7)
  const [result, setResult] = useState(null)
  const [loading,setLoading]= useState(false)

  const get = async () => {
    setLoading(true)
    try { setResult(await api.marketPred({ crop, state, days, language: lang })) } catch(e) {}
    setLoading(false)
  }

  const chartData = result?.prices?.map(p => ({ date: p.date.slice(5), price: p.price })) || []

  return (
    <div className="page">
      <h1 className="page-head">📉 Price Forecast</h1>
      <p className="page-sub">Indicative mandi price prediction</p>
      <div className="grid-2">
        <div style={{display:'flex',flexDirection:'column',gap:14}}>
          <div>
            <label className="input-label">Crop</label>
            <select className="input" value={crop} onChange={e => setCrop(e.target.value)}>
              {['Wheat','Tomato','Onion','Cotton','Soybean','Maize'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="input-label">State</label>
            <input className="input" value={state} onChange={e => setState(e.target.value)}/>
          </div>
          <div>
            <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
              <label className="input-label" style={{margin:0}}>Days Ahead</label>
              <span style={{fontWeight:700,color:'var(--lime)',fontSize:13}}>{days}</span>
            </div>
            <input type="range" min={1} max={15} value={days} onChange={e => setDays(Number(e.target.value))}/>
          </div>
          <button onClick={get} disabled={loading} className="btn btn-primary btn-full">
            {loading ? <Spinner size={18}/> : '📊 Predict'}
          </button>
        </div>

        {result && (
          <div className="card fade-up">
            {result.best_selling_window && (
              <Alert type="success" style={{marginBottom:14}}>🏆 Best window: <strong>{result.best_selling_window}</strong></Alert>
            )}
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="pg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#aaff44" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#aaff44" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.06)"/>
                <XAxis dataKey="date" tick={{fill:'#4a6070',fontSize:11}} axisLine={false} tickLine={false}/>
                <YAxis tick={{fill:'#4a6070',fontSize:11}} axisLine={false} tickLine={false}/>
                <Tooltip contentStyle={{background:'#0d1419',border:'1px solid rgba(255,255,255,.1)',borderRadius:10,color:'#e4edf4'}}/>
                <Area type="monotone" dataKey="price" stroke="#aaff44" strokeWidth={2} fill="url(#pg)"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
