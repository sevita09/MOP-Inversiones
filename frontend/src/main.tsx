import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { ProveedorMoneda } from './contextos/MonedaContext.tsx'
import { ProveedorTicker } from './contextos/TickerContext.tsx'
import { ProveedorFavoritos } from './contextos/FavoritosContext.tsx'
import { ProveedorCategorias } from './contextos/CategoriasContext.tsx'
import { ProveedorEstilos } from './contextos/EstilosContext.tsx'
import { ProveedorEmasExtra } from './contextos/EmasExtraContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ProveedorMoneda>
        <ProveedorTicker>
          <ProveedorFavoritos>
            <ProveedorCategorias>
              <ProveedorEstilos>
                <ProveedorEmasExtra>
                  <App />
                </ProveedorEmasExtra>
              </ProveedorEstilos>
            </ProveedorCategorias>
          </ProveedorFavoritos>
        </ProveedorTicker>
      </ProveedorMoneda>
    </BrowserRouter>
  </StrictMode>,
)
