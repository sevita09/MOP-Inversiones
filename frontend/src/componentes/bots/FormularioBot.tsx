import { useMemo, useState } from 'react'
import type {
  Bot,
  BotNuevo,
  Moneda,
  Plantilla,
  ReglasBot,
  RiesgoBot,
  TemporalidadBot,
} from '../../api/tipos'
import LogoTicker from '../LogoTicker'
import BacktestRapido from './BacktestRapido'
import ConstructorReglas from './ConstructorReglas'
import ControlesRiesgo, { RIESGO_VACIO } from './ControlesRiesgo'
import InputNumero from './InputNumero'
import GraficoPreviewBot from './GraficoPreviewBot'
import GuardarComoPlantilla from './GuardarComoPlantilla'
import SelectorPlantilla from './SelectorPlantilla'
import { REGLAS_VACIAS } from './configReglas'
import { resumirReglas } from './resumenReglas'
import { usarPlantillas } from '../../hooks/usarPlantillas'
import { usarTickers } from '../../hooks/usarTickers'
import './FormularioBot.css'

interface Props {
  bot: Bot | null // null = alta
  alGuardar: (datos: BotNuevo) => Promise<void>
  alCerrar: () => void
}

const TEMPORALIDADES: { valor: TemporalidadBot; etiqueta: string }[] = [
  { valor: 'D', etiqueta: 'Diario' },
  { valor: 'S', etiqueta: 'Semanal' },
  { valor: 'M', etiqueta: 'Mensual' },
]

const MONEDAS: Moneda[] = ['ARS', 'USD']

/** Alta y edición de un bot: nombre, ticker, temporalidad, moneda y capital. */
function FormularioBot({ bot, alGuardar, alCerrar }: Props) {
  const paneles = usarTickers()
  const { plantillas, crear: crearPlantilla, eliminar: eliminarPlantilla } = usarPlantillas()
  const [nombre, setNombre] = useState(bot?.nombre ?? '')
  const [ticker, setTicker] = useState(bot?.ticker ?? '')
  const [busqueda, setBusqueda] = useState('')
  const [temporalidad, setTemporalidad] = useState<TemporalidadBot>(bot?.temporalidad ?? 'D')
  const [moneda, setMoneda] = useState<Moneda>(bot?.moneda ?? 'ARS')
  const [inicial, setInicial] = useState<number | null>(bot?.capital.inicial ?? 1000000)
  const [porcentaje, setPorcentaje] = useState<number | null>(
    bot?.capital.porcentaje_por_posicion ?? 100,
  )
  const [reglas, setReglas] = useState<ReglasBot>(bot?.reglas ?? REGLAS_VACIAS)
  const [riesgo, setRiesgo] = useState<RiesgoBot>(bot?.riesgo ?? RIESGO_VACIO)

  // Al subir la temporalidad del bot, las condiciones que quedaron por debajo
  // (p.ej. una diaria en un bot ahora semanal) vuelven a "la del bot"
  const ORDEN: Record<TemporalidadBot, number> = { D: 0, S: 1, M: 2 }
  const cambiarTemporalidad = (nueva: TemporalidadBot) => {
    setTemporalidad(nueva)
    const sanear = (condiciones: typeof reglas.entrada) =>
      condiciones.map((c) => {
        if (c.temporalidad && ORDEN[c.temporalidad] < ORDEN[nueva]) {
          const { temporalidad: _, ...resto } = c
          return resto
        }
        return c
      })
    setReglas((previas) => ({
      ...previas,
      entrada: sanear(previas.entrada),
      salida: sanear(previas.salida),
      filtros: sanear(previas.filtros),
    }))
  }
  const [mensaje, setMensaje] = useState('')
  const [guardando, setGuardando] = useState(false)

  // Los bots operan cualquier ticker con datos, menos los de dólar
  const candidatos = useMemo(() => {
    if (!paneles) return []
    const todos = [
      ...paneles.panel_lider,
      ...paneles.panel_general,
      ...paneles.cedears,
      ...paneles.indices,
      ...paneles.cripto,
    ]
    const consulta = busqueda.trim().toUpperCase()
    if (!consulta) return []
    return todos.filter((simbolo) => simbolo.includes(consulta)).slice(0, 8)
  }, [paneles, busqueda])

  const guardar = async () => {
    const limpio = nombre.trim()
    if (!limpio) return setMensaje('Poné un nombre al bot')
    if (!ticker) return setMensaje('Elegí un ticker')
    const capitalInicial = inicial ?? 0
    const capitalPorcentaje = porcentaje ?? 0
    if (!(capitalInicial > 0)) return setMensaje('El capital inicial debe ser mayor a 0')
    if (!(capitalPorcentaje > 0 && capitalPorcentaje <= 100))
      return setMensaje('La entrada por posición va de 1 a 100%')

    setGuardando(true)
    setMensaje('')
    try {
      await alGuardar({
        nombre: limpio,
        ticker,
        temporalidad,
        moneda,
        capital: { inicial: capitalInicial, porcentaje_por_posicion: capitalPorcentaje },
        riesgo,
        reglas,
      })
    } catch (error) {
      const texto = error instanceof Error ? error.message : ''
      setMensaje(
        texto.includes('409')
          ? `Ya existe un bot llamado ${limpio}`
          : 'No se pudo guardar el bot',
      )
      setGuardando(false)
    }
  }

  return (
    <div className="fondo-formulario-bot" onClick={alCerrar}>
      <div className="formulario-bot" onClick={(evento) => evento.stopPropagation()}>
        <div className="cabecera-formulario-bot">
          <span>{bot ? `Editar ${bot.nombre}` : 'Nuevo bot'}</span>
          <button type="button" className="cerrar-formulario" onClick={alCerrar}>
            ×
          </button>
        </div>

        <div className="cuerpo-formulario-bot">
        <div className="columna-datos-bot">
        <SelectorPlantilla
          plantillas={plantillas}
          alEliminar={(id) => void eliminarPlantilla(id)}
          alLimpiar={() => setReglas(REGLAS_VACIAS)}
          alElegir={(plantilla: Plantilla) => {
            setNombre(plantilla.nombre)
            setTemporalidad(plantilla.temporalidad)
            setMoneda(plantilla.moneda)
            setReglas(plantilla.reglas)
          }}
        />
        <label className="campo-bot">
          Nombre
          <input
            autoFocus
            value={nombre}
            placeholder="Ej: Reversión GGAL semanal"
            onChange={(evento) => setNombre(evento.target.value)}
          />
        </label>

        <label className="campo-bot">
          Ticker
          {ticker ? (
            <span className="ticker-elegido">
              <LogoTicker ticker={ticker} tamano={20} />
              {ticker}
              <button type="button" onClick={() => setTicker('')} title="Cambiar">
                ×
              </button>
            </span>
          ) : (
            <span className="buscador-ticker-bot">
              <input
                value={busqueda}
                placeholder="Buscar ticker…"
                onChange={(evento) => setBusqueda(evento.target.value.toUpperCase())}
              />
              {candidatos.length > 0 && (
                <ul className="sugerencias-ticker">
                  {candidatos.map((simbolo) => (
                    <li key={simbolo}>
                      <button
                        type="button"
                        onClick={() => {
                          setTicker(simbolo)
                          setBusqueda('')
                        }}
                      >
                        <LogoTicker ticker={simbolo} tamano={18} />
                        {simbolo}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </span>
          )}
        </label>

        <div className="campo-bot">
          Temporalidad
          <div className="chips-bot">
            {TEMPORALIDADES.map(({ valor, etiqueta }) => (
              <button
                key={valor}
                type="button"
                className={valor === temporalidad ? 'chip-bot activo' : 'chip-bot'}
                onClick={() => cambiarTemporalidad(valor)}
              >
                {etiqueta}
              </button>
            ))}
          </div>
        </div>

        <div className="campo-bot">
          Moneda
          <div className="chips-bot">
            {MONEDAS.map((valor) => (
              <button
                key={valor}
                type="button"
                className={valor === moneda ? 'chip-bot activo' : 'chip-bot'}
                onClick={() => setMoneda(valor)}
              >
                {valor}
              </button>
            ))}
          </div>
        </div>

        <div className="fila-capital">
          <label className="campo-bot">
            Capital inicial
            <InputNumero valor={inicial} prefijo="$" miles placeholder="0" alCambiar={setInicial} />
          </label>
          <label className="campo-bot">
            Entrada por posición
            <InputNumero valor={porcentaje} sufijo="%" placeholder="100" alCambiar={setPorcentaje} />
          </label>
        </div>

        <ControlesRiesgo riesgo={riesgo} alCambiar={setRiesgo} />
        </div>

        <div className="columna-reglas-bot">
          <ConstructorReglas
            reglas={reglas}
            temporalidadBot={temporalidad}
            alCambiar={setReglas}
          />
          {resumirReglas(reglas, temporalidad) && (
            <p className="resumen-reglas">{resumirReglas(reglas, temporalidad)}</p>
          )}
          <BacktestRapido
            ticker={ticker}
            temporalidad={temporalidad}
            moneda={moneda}
            capital={{
              inicial: inicial ?? 1000000,
              porcentaje_por_posicion: porcentaje ?? 100,
            }}
            riesgo={riesgo}
            reglas={reglas}
          />
          <GuardarComoPlantilla
            reglas={reglas}
            temporalidad={temporalidad}
            moneda={moneda}
            nombreSugerido={nombre.trim()}
            alCrear={crearPlantilla}
          />
          {ticker ? (
            <GraficoPreviewBot
              ticker={ticker}
              temporalidad={temporalidad}
              moneda={moneda}
              reglas={reglas}
            />
          ) : (
            <p className="preview-sin-ticker">Elegí un ticker para ver la vista previa.</p>
          )}
        </div>
        </div>

        {mensaje && <div className="mensaje-formulario-bot">{mensaje}</div>}

        <div className="acciones-formulario-bot">
          <button type="button" className="boton-guardar-bot" disabled={guardando} onClick={() => void guardar()}>
            {guardando ? 'Guardando…' : bot ? 'Guardar cambios' : 'Crear bot'}
          </button>
          <button type="button" className="boton-cancelar" onClick={alCerrar}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}

export default FormularioBot
