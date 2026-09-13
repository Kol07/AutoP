import { useState, useEffect } from 'react'
import { fetchHealth } from './api/health'

function App() {

  const [healthStatus, setHealthStatus] = useState("")

  useEffect(() => {
    async function loadHealth(){
      const response = await fetchHealth();
      setHealthStatus(response.status)
    }

    loadHealth();
  }, [])

  return (
    <>
      <p>Backend Status: {healthStatus}</p>

      <p></p>
    </>
  )
}

export default App
