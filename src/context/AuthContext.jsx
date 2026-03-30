import { useState, useEffect, createContext, useContext } from 'react'
import api from '../api.js'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null)
  const [jwt,  setJwt]    = useState(() => localStorage.getItem('krishi_jwt') || '')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (jwt) {
      api.me().then(u => { setUser(u); setReady(true) })
             .catch(() => { setJwt(''); localStorage.removeItem('krishi_jwt'); setReady(true) })
    } else setReady(true)
  }, [jwt])

  const login = async (p) => {
    const d = await api.login(p)
    localStorage.setItem('krishi_jwt', d.access_token)
    setJwt(d.access_token)
    const u = await api.me()
    setUser(u)
    return u
  }

  const register = async (p) => {
    const d = await api.register(p)
    localStorage.setItem('krishi_jwt', d.access_token)
    setJwt(d.access_token)
    const u = await api.me().catch(() => ({ name: p.name }))
    setUser(u)
    return u
  }

  const logout = () => {
    localStorage.removeItem('krishi_jwt')
    setJwt('')
    setUser(null)
  }

  if (!ready) return (
    <div style={{height:'100vh',display:'flex',alignItems:'center',justifyContent:'center',background:'#070b0e'}}>
      <div style={{textAlign:'center'}}>
        <div style={{fontSize:48,marginBottom:16}}>🌿</div>
        <div className="spinner" style={{margin:'0 auto'}}/>
      </div>
    </div>
  )

  return (
    <AuthCtx.Provider value={{ user, jwt, login, register, logout }}>
      {children}
    </AuthCtx.Provider>
  )
}
