// Market.jsx
import { useState, useEffect } from 'react'
import { ArrowUp, ArrowDown } from 'lucide-react'
import api from '../api.js'

export default function Market() {
  const [prices, setPrices] = useState([])
  useEffect(() => { api.market().then(d => setPrices(d.prices || [])).catch(() => {}) }, [])
  return (
    <div className="page">
      <h1 className="page-head">📈 Mandi Prices</h1>
      <p className="page-sub">Live market rates</p>
      <div style={{display:'flex',flexDirection:'column',gap:12,maxWidth:600}}>
        {prices.map(p => (
          <div key={p.crop} className="card" style={{display:'flex',alignItems:'center',gap:16,padding:'18px 22px'}}>
            <span style={{fontSize:40}}>{p.emoji}</span>
            <div style={{flex:1}}>
              <div style={{fontFamily:'Syne,sans-serif',fontSize:16,fontWeight:700}}>{p.crop}</div>
              <div style={{fontSize:12,color:'var(--text3)',marginTop:3}}>📍 {p.mandi}</div>
            </div>
            <div style={{textAlign:'right'}}>
              <div style={{fontSize:22,fontWeight:800}}>{p.price}<span style={{fontSize:12,color:'var(--text3)'}}>/q</span></div>
              <div style={{fontSize:13,fontWeight:600,color:p.direction==='up'?'var(--lime)':'var(--rose)',display:'flex',alignItems:'center',gap:3,justifyContent:'flex-end',marginTop:3}}>
                {p.direction==='up' ? <ArrowUp size={13}/> : <ArrowDown size={13}/>}{p.change}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
