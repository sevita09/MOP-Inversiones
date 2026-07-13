import {
  Fragment,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'

// Una unidad de la barra que puede pasar al overflow. `grupoInicio` marca el
// primer ítem de un grupo → lleva un divisor (obligatorio) antes cuando está en línea.
export interface UnidadBarra {
  clave: string
  nodo: ReactNode
  grupoInicio?: boolean
}

interface Props {
  izquierda: ReactNode // fijo a la izquierda, siempre visible (ticker)
  derecha: ReactNode[] // fijos a la derecha, siempre visibles (CCL, toggle) — cada uno con su divisor
  unidades: UnidadBarra[]
}

const GAP_MIN = 10 // distancia mínima entre elementos del medio antes de ocultar
const FLECHA = 44 // ancho reservado para la flecha de overflow (botón + margen)

/** Barra responsive. Bordes fijos y compactos (ticker | … | CCL | ARS/USD) y el
 *  medio repartido PAREJO en el ancho restante (space-evenly). La medición es en
 *  dos pasadas sobre los ítems REALES: se renderiza todo, se mide antes del paint
 *  (useLayoutEffect) y lo que no entra con la distancia mínima pasa a la flecha. */
function BarraOverflow({ izquierda, derecha, unidades }: Props) {
  const contRef = useRef<HTMLDivElement>(null)
  const izqRef = useRef<HTMLDivElement>(null)
  const derRef = useRef<HTMLDivElement>(null)
  const medioRef = useRef<HTMLDivElement>(null)
  const [nVisibles, setNVisibles] = useState(unidades.length)
  const [midiendo, setMidiendo] = useState(true)
  const [abierto, setAbierto] = useState(false)

  // Re-medir cuando cambia el set de unidades (p.ej. otro ticker con menos toggles):
  // reset derivado durante el render, sin pasar por un effect.
  const claves = unidades.map((u) => u.clave).join('|')
  const [clavesPrevias, setClavesPrevias] = useState(claves)
  if (claves !== clavesPrevias) {
    setClavesPrevias(claves)
    setMidiendo(true)
  }

  // Re-medir cuando cambia el ancho del contenedor o de los bordes (CCL que carga)
  useLayoutEffect(() => {
    const ro = new ResizeObserver(() => setMidiendo(true))
    if (contRef.current) ro.observe(contRef.current)
    if (izqRef.current) ro.observe(izqRef.current)
    if (derRef.current) ro.observe(derRef.current)
    return () => ro.disconnect()
  }, [])

  // Pasada de medición: con TODO renderizado (midiendo=true), medir los anchos
  // reales y decidir cuántos entran. Corre antes del paint: no se ve el parpadeo.
  useLayoutEffect(() => {
    if (!midiendo) return
    const cont = contRef.current
    const izq = izqRef.current
    const der = derRef.current
    const medio = medioRef.current
    if (!cont || !izq || !der || !medio) return

    const disponible = cont.clientWidth - izq.offsetWidth - der.offsetWidth
    const hijos = Array.from(medio.children) as HTMLElement[]

    // Reconstruir el ancho real de cada unidad y de su divisor previo (si tiene)
    const anchoUnidad: number[] = []
    const anchoDivisor: number[] = []
    let k = 0
    unidades.forEach((u, i) => {
      if (u.grupoInicio && i > 0) {
        anchoDivisor.push(hijos[k]?.offsetWidth ?? 1)
        k++
      } else {
        anchoDivisor.push(0)
      }
      anchoUnidad.push(hijos[k]?.offsetWidth ?? 0)
      k++
    })

    // Ancho necesario para los primeros n con la distancia mínima en cada hueco.
    // Con space-evenly los huecos son (piezas + 1): hay aire también en los bordes.
    const necesita = (n: number, conFlecha: boolean) => {
      let suma = 0
      let piezas = conFlecha ? 1 : 0
      for (let i = 0; i < n; i++) {
        suma += anchoUnidad[i] + anchoDivisor[i]
        piezas += anchoDivisor[i] > 0 ? 2 : 1
      }
      return suma + (conFlecha ? FLECHA : 0) + GAP_MIN * (piezas + 1)
    }

    let n = unidades.length
    while (n > 0 && necesita(n, false) > disponible) n--
    if (n < unidades.length) while (n > 0 && necesita(n, true) > disponible) n--
    setNVisibles(n)
    setMidiendo(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [midiendo, claves])

  // Cerrar el menú al clickear afuera
  useEffect(() => {
    if (!abierto) return
    const cerrar = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.mas-contenedor')) setAbierto(false)
    }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [abierto])

  // Mientras se mide, se renderiza todo (oculto tras overflow:hidden del medio)
  const visibles = midiendo ? unidades : unidades.slice(0, nVisibles)
  const ocultas = midiendo ? [] : unidades.slice(nVisibles)

  return (
    <div className="barra-grafico" ref={contRef}>
      <div className="barra-borde barra-izq" ref={izqRef}>
        {izquierda}
        <span className="separador-barra" />
      </div>
      <div className="barra-medio" ref={medioRef}>
        {visibles.map((u, i) => (
          <Fragment key={u.clave}>
            {u.grupoInicio && i > 0 && <span className="separador-barra" />}
            {u.nodo}
          </Fragment>
        ))}
      </div>
      {ocultas.length > 0 && (
        // Fuera de .barra-medio: su overflow:hidden recortaría el menú desplegable
        <div className="mas-contenedor">
          <button
            type="button"
            className="boton-mas"
            title="Más herramientas"
            onClick={() => setAbierto((v) => !v)}
          >
            »
          </button>
          {abierto && (
            <div className="menu-mas">
              {ocultas.map((u) => (
                <div className="menu-mas-fila" key={u.clave}>
                  {u.nodo}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      <div className="barra-borde barra-der" ref={derRef}>
        {derecha.map((d, i) => (
          <Fragment key={i}>
            <span className="separador-barra" />
            {d}
          </Fragment>
        ))}
      </div>
    </div>
  )
}

export default BarraOverflow
