import './AyudaRendimiento.css'

/** Círculo con "?" que explica, al pasar el mouse, cómo se lee esta vista. */
function AyudaRendimiento() {
  return (
    <span className="ayuda-rendimiento">
      <button type="button" className="boton-ayuda" aria-label="Cómo se lee esta vista">
        ?
      </button>
      <span className="panel-ayuda" role="tooltip">
        <span className="titulo-ayuda">Qué muestra</span>
        <p>
          La línea azul es la cartera completa, rueda por rueda, desde la primera operación
          registrada — no un papel en particular. Cada día toma las tenencias de ese día.
        </p>
        <p>
          Las tres líneas arrancan en <span className="clave-ayuda">100</span> en la misma rueda,
          de modo que la comparación cubre el mismo tramo de tiempo. Un valor de 168 equivale a
          +68%.
        </p>

        <span className="titulo-ayuda">Por qué una compra no mueve la línea</span>
        <p>
          El <span className="clave-ayuda">TWR</span> mide el rendimiento de las decisiones, no el
          tamaño de la cartera: antes de comparar contra la rueda anterior descuenta el dinero que
          entró o salió.
        </p>
        <p className="ejemplo-ayuda">
          Una cartera de $1.000.000 recibe un aporte de $500.000 y pasa a valer $1.500.000: la
          línea no se mueve, porque el aumento es dinero agregado y no ganancia. Si en cambio esa
          misma cartera llega a $1.100.000 sin aportes, la línea marca +10%.
        </p>

        <span className="titulo-ayuda">El período recorta, no simula</span>
        <p>
          Elegir 1A o 5A muestra un tramo de la historia real. No responde qué habría pasado
          comprando cinco años antes: eso corresponde al análisis what-if.
        </p>
      </span>
    </span>
  )
}

export default AyudaRendimiento
