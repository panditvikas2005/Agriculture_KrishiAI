import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CloudRain, Wind, TrendingUp, ArrowUp, ArrowDown, Zap } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { Metric } from '../components/UI.jsx'
import api from '../api.js'

export default function Dashboard({ lang }) {
  const { user } = useAuth()
  const [weather, setWeather] = useState(null)
  const [market,  setMarket]  = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.weather().then(setWeather).catch(() => {})
    api.market().then(setMarket).catch(() => {})
  }, [])

  const qa = [
    {icon:'🔬',label:'Disease Scan',  path:'/disease',    color:'rgba(255,181,71,.1)'},
    {icon:'💬',label:'Ask AI',        path:'/chat',       color:'rgba(170,255,68,.1)'},
    {icon:'🎙️',label:'Voice AI',      path:'/voice',      color:'rgba(0,212,170,.1)'},
    {icon:'💰',label:'Profit Calc',   path:'/profit',     color:'rgba(96,184,255,.1)'},
    {icon:'💧',label:'Irrigation',    path:'/irrigation', color:'rgba(96,184,255,.08)'},
    {icon:'🌱',label:'Fertilizer',    path:'/planner',    color:'rgba(170,255,68,.08)'},
    {icon:'📊',label:'Price Forecast',path:'/predict',    color:'rgba(255,181,71,.08)'},
    {icon:'🏛', label:'Gov Schemes',  path:'/schemes',    color:'rgba(0,212,170,.08)'},
  ]

  return (
    <div className="page">
      <h1 className="page-head">⊞ Good day, {user?.name}! 🌿</h1>
      <p className="page-sub">Your farm overview for today</p>

      <div className="grid-4" style={{marginBottom:24}}>
        <Metric label="Active Crops"  value="4"    delta="+1"   deltaType="up"/>
        <Metric label="Field Temp"    value={weather ? `${weather.temp_c?.toFixed(0)}°C` : '—'}/>
        <Metric label="Soil Moisture" value="62%"  delta="+4%"  deltaType="up"/>
        <Metric label="Est. Revenue"  value="₹84k" delta="+₹6k" deltaType="up"/>
      </div>

      <div className="grid-2" style={{marginBottom:24}}>
        {weather && (
          <div className="card">
            <div style={{fontSize:12,color:'var(--text3)',marginBottom:12,display:'flex',alignItems:'center',gap:6}}>
              <CloudRain size={14}/> Weather · {weather.district}
            </div>
            <div style={{fontFamily:'Syne,sans-serif',fontSize:56,fontWeight:800,color:'var(--sky)',lineHeight:1}}>
              {weather.temp_c?.toFixed(0)}°C
            </div>
            <div style={{fontSize:14,color:'var(--text2)',marginTop:8,display:'flex',gap:16}}>
              <span>{weather.emoji} {weather.condition}</span>
              <span style={{display:'flex',alignItems:'center',gap:4}}><Wind size={12}/>{weather.wind_kmh} km/h</span>
            </div>
            {weather.tip && (
              <div style={{background:'rgba(170,255,68,.06)',border:'1px solid rgba(170,255,68,.12)',borderRadius:10,padding:'10px 14px',fontSize:13,color:'var(--lime)',marginTop:14}}>
                💡 {weather.tip}
              </div>
            )}
          </div>
        )}

        {market && (
          <div className="card">
            <div style={{fontSize:12,color:'var(--text3)',marginBottom:14,display:'flex',alignItems:'center',gap:6}}>
              <TrendingUp size={14}/> Live Mandi Prices
            </div>
            {market.prices?.map(p => (
              <div key={p.crop} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'9px 0',borderBottom:'1px solid rgba(255,255,255,.05)'}}>
                <span style={{fontSize:14}}>{p.emoji} {p.crop}</span>
                <span style={{fontWeight:700,fontSize:15}}>{p.price}/q</span>
                <span style={{fontSize:12,fontWeight:600,color:p.direction==='up'?'var(--lime)':'var(--rose)',display:'flex',alignItems:'center',gap:3}}>
                  {p.direction==='up' ? <ArrowUp size={11}/> : <ArrowDown size={11}/>}{p.change}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <div style={{fontSize:13,color:'var(--text3)',marginBottom:12,display:'flex',alignItems:'center',gap:6}}>
          <Zap size={13}/> Quick Actions
        </div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
          {qa.map(({ icon, label, path, color }) => (
            <button key={path} onClick={() => navigate(path)}
              style={{background:color,border:'1px solid rgba(255,255,255,.07)',borderRadius:16,padding:'16px 12px',cursor:'pointer',transition:'all .2s',textAlign:'center',display:'flex',flexDirection:'column',alignItems:'center',gap:8}}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <span style={{fontSize:26}}>{icon}</span>
              <span style={{fontSize:12,fontWeight:600,color:'var(--text)'}}>{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
