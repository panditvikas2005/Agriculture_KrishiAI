import { useState, useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, Microscope, Mic, TrendingUp, Building2,
  FlaskConical, Droplets, Leaf, BarChart2, Calendar, DollarSign,
  LogOut, ChevronRight, TrendingDown, Menu, X
} from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import api from '../api.js'

const NAV = [
  { path:'/dashboard',  icon:LayoutDashboard, label:'Dashboard'      },
  { path:'/chat',       icon:MessageSquare,   label:'AI Advisor'     },
  { path:'/disease',    icon:Microscope,      label:'Disease Detect' },
  { path:'/voice',      icon:Mic,             label:'Voice AI'       },
  { path:'/market',     icon:TrendingUp,      label:'Mandi Prices'   },
  { path:'/schemes',    icon:Building2,       label:'Gov Schemes'    },
  { path:'/soil',       icon:FlaskConical,    label:'Soil Health'    },
  { path:'/irrigation', icon:Droplets,        label:'Irrigation'     },
  { path:'/planner',    icon:Leaf,            label:'Fertilizer'     },
  { path:'/predict',    icon:TrendingDown,    label:'Price Forecast' },
  { path:'/profit',     icon:DollarSign,      label:'Profit Calc'    },
  { path:'/analytics',  icon:BarChart2,       label:'Analytics'      },
  { path:'/calendar',   icon:Calendar,        label:'Farm Calendar'  },
]

export default function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [online, setOnline] = useState(false)

  useEffect(() => {
    api.health().then(() => setOnline(true)).catch(() => setOnline(false))
    const id = setInterval(() => {
      api.health().then(() => setOnline(true)).catch(() => setOnline(false))
    }, 15000)
    return () => clearInterval(id)
  }, [])

  return (
    <>
      {open && <div onClick={onClose} style={{position:'fixed',inset:0,background:'rgba(0,0,0,.5)',zIndex:40}}/>}
      <aside
        className={`sidebar ${open ? 'open' : ''}`}
        style={{position:'fixed',top:0,left:0,height:'100vh',width:240,background:'rgba(7,11,14,.97)',borderRight:'1px solid rgba(255,255,255,.06)',backdropFilter:'blur(24px)',display:'flex',flexDirection:'column',padding:'20px 12px',zIndex:45,overflowY:'auto'}}
      >
        <div style={{display:'flex',alignItems:'center',gap:12,padding:'4px 8px 24px'}}>
          <div style={{width:42,height:42,borderRadius:13,flexShrink:0,background:'linear-gradient(135deg,#aaff44,#55aa00)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:22,boxShadow:'0 4px 18px rgba(170,255,68,.3)'}}>🌿</div>
          <div>
            <div style={{fontFamily:'Syne,sans-serif',fontSize:17,fontWeight:800,color:'#aaff44'}}>KrishiAI</div>
            <div style={{fontSize:10,color:'#4a6070',letterSpacing:'.06em'}}>v4.1 · GROQ AI</div>
          </div>
        </div>

        {user && (
          <div style={{background:'rgba(170,255,68,.05)',border:'1px solid rgba(170,255,68,.12)',borderRadius:10,padding:'8px 12px',marginBottom:12,fontSize:13,color:'#aaff44',display:'flex',alignItems:'center',gap:8}}>
            <span style={{fontSize:18}}>👨‍🌾</span>
            <span style={{fontWeight:600,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{user.name}</span>
          </div>
        )}

        <div style={{background:online?'rgba(170,255,68,.05)':'rgba(255,107,107,.05)',border:`1px solid ${online?'rgba(170,255,68,.15)':'rgba(255,107,107,.15)'}`,borderRadius:8,padding:'6px 10px',marginBottom:16,fontSize:11,color:online?'#aaff44':'#ff6b6b',display:'flex',alignItems:'center',gap:6}}>
          <div style={{width:6,height:6,borderRadius:'50%',background:'currentColor',flexShrink:0}}/>
          {online ? 'Backend Online' : 'Backend Offline'}
        </div>

        <nav style={{flex:1,display:'flex',flexDirection:'column',gap:2}}>
          {NAV.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onClose}
              style={({ isActive }) => ({display:'flex',alignItems:'center',gap:10,padding:'9px 12px',borderRadius:10,fontSize:13,fontWeight:isActive?600:400,textDecoration:'none',transition:'all .15s',color:isActive?'#0a1a00':'#8fa3b1',background:isActive?'linear-gradient(135deg,#aaff44,#66cc00)':'transparent',boxShadow:isActive?'0 3px 12px rgba(170,255,68,.25)':'none'})}
            >
              {({ isActive }) => (
                <>
                  <Icon size={15} strokeWidth={isActive ? 2.2 : 1.8}/>
                  <span>{label}</span>
                  {isActive && <ChevronRight size={13} style={{marginLeft:'auto'}}/>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div style={{marginTop:16,paddingTop:16,borderTop:'1px solid rgba(255,255,255,.06)'}}>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="btn btn-ghost btn-full btn-sm"
            style={{justifyContent:'flex-start',gap:8}}
          >
            <LogOut size={14}/> Logout
          </button>
        </div>
      </aside>
    </>
  )
}
