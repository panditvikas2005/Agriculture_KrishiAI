import { useEffect } from 'react'

export function Spinner({ size = 20 }) {
  return <div className="spinner" style={{ width: size, height: size }} />
}

export function Alert({ type = 'info', children, onClose, style: s }) {
  return (
    <div className={`alert alert-${type}`} style={{ marginBottom: 12, ...s }}>
      <span style={{ flex: 1 }}>{children}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{background:'none',border:'none',cursor:'pointer',color:'inherit',padding:0,flexShrink:0}}
        >✕</button>
      )}
    </div>
  )
}

export function Metric({ label, value, delta, deltaType = 'up' }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {delta && (
        <div className={`metric-delta ${deltaType}`}>
          {deltaType === 'up' ? '↑' : '↓'} {delta}
        </div>
      )}
    </div>
  )
}

export function Aurora() {
  return (
    <>
      <div style={{position:'fixed',width:700,height:700,background:'radial-gradient(circle,rgba(170,255,68,.09) 0%,transparent 70%)',borderRadius:'50%',top:-250,left:-150,animation:'aurora1 14s ease-in-out infinite',pointerEvents:'none',zIndex:0}}/>
      <div style={{position:'fixed',width:600,height:600,background:'radial-gradient(circle,rgba(0,212,170,.07) 0%,transparent 70%)',borderRadius:'50%',bottom:-180,right:-120,animation:'aurora2 18s ease-in-out infinite',pointerEvents:'none',zIndex:0}}/>
    </>
  )
}

export function WelcomeBanner({ name, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3500)
    return () => clearTimeout(t)
  }, [onDone])

  return (
    <div style={{position:'fixed',inset:0,background:'rgba(7,11,14,.92)',backdropFilter:'blur(12px)',zIndex:999,display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div className="fade-up" style={{textAlign:'center',padding:40}}>
        <div style={{fontSize:80,marginBottom:8}}>🌾</div>
        <div style={{fontFamily:'Syne,sans-serif',fontSize:36,fontWeight:800,color:'#aaff44',marginBottom:12}}>KrishiAI में आपका</div>
        <div style={{fontFamily:'Syne,sans-serif',fontSize:48,fontWeight:800,background:'linear-gradient(135deg,#aaff44,#00d4aa)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',lineHeight:1}}>स्वागत है! 🎉</div>
        <div style={{marginTop:20,fontSize:18,color:'#8fa3b1'}}>नमस्ते <strong style={{color:'#e4edf4'}}>{name}</strong> जी!</div>
        <div style={{marginTop:28}}><div className="spinner" style={{margin:'0 auto'}}/></div>
      </div>
    </div>
  )
}
