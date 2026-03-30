import { useState, useEffect } from 'react'
import api from '../api.js'

export default function Schemes({ lang }) {
  const [schemes, setSchemes] = useState([])
  useEffect(() => { api.schemes(lang).then(d => setSchemes(d.schemes || [])).catch(() => {}) }, [lang])
  return (
    <div className="page">
      <h1 className="page-head">🏛 Government Schemes</h1>
      <p className="page-sub">Indian farmers ke liye schemes</p>
      <div style={{display:'flex',flexDirection:'column',gap:14,maxWidth:700}}>
        {schemes.map(s => (
          <div key={s.name} className="card">
            <div style={{display:'flex',alignItems:'flex-start',gap:14}}>
              <span style={{fontSize:32,flexShrink:0}}>{s.icon}</span>
              <div style={{flex:1}}>
                <div style={{fontFamily:'Syne,sans-serif',fontSize:17,fontWeight:700,marginBottom:4}}>{s.name}</div>
                <div style={{fontSize:14,color:'var(--text2)',lineHeight:1.6,marginBottom:10}}>{s.description}</div>
                <div style={{display:'flex',alignItems:'center',gap:10,flexWrap:'wrap'}}>
                  <span className="chip chip-lime">💰 {s.benefit}</span>
                  <a href={s.apply_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">Apply →</a>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
