import { useCallback, useEffect, useState } from 'react'
import {
  obtenerCaptura,
  obtenerEscenariosDeVenta,
  obtenerVentasCerradas,
  obtenerWhatIf,
} from '../api/cliente'
import type { Captura, EscenariosDeVenta, VentaCerrada, WhatIf } from '../api/tipos'

/** Listado de ventas cerradas y la métrica de captura.
 *
 *  El listado es liviano a propósito: los escenarios de cada venta se piden al
 *  elegirla. Con cientos de operaciones, traerlos todos de entrada serían ocho
 *  consultas por venta para una tabla que nadie lee completa. */
export function usarVentasCerradas() {
  const [ventas, setVentas] = useState<VentaCerrada[]>([])
  const [captura, setCaptura] = useState<Captura | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    let vigente = true
    void Promise.all([obtenerVentasCerradas(), obtenerCaptura()])
      .then(([listado, medida]) => {
        if (!vigente) return
        setVentas(listado.ventas)
        setCaptura(medida)
      })
      .catch(() => {
        if (!vigente) return
        setVentas([])
        setCaptura(null)
      })
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [])

  return { ventas, captura, cargando }
}

/** Escenarios de la venta elegida, pedidos cuando se la selecciona. */
export function usarEscenariosDeVenta(idVenta: number | null) {
  const [datos, setDatos] = useState<EscenariosDeVenta | null>(null)

  useEffect(() => {
    if (idVenta === null) {
      setDatos(null)
      return
    }
    let vigente = true
    setDatos(null)
    obtenerEscenariosDeVenta(idVenta)
      .then((escenarios) => vigente && setDatos(escenarios))
      .catch(() => vigente && setDatos(null))
    return () => {
      vigente = false
    }
  }, [idVenta])

  return datos
}

/** P&L de una venta movida a otra fecha, para el slider.
 *
 *  Va con debounce: arrastrarlo dispararía una consulta por píxel. */
export function usarWhatIf(idVenta: number | null) {
  const [resultado, setResultado] = useState<WhatIf | null>(null)
  const [fecha, setFecha] = useState<string | null>(null)

  const consultar = useCallback((nueva: string) => {
    setFecha(nueva)
  }, [])

  useEffect(() => {
    if (idVenta === null || fecha === null) {
      setResultado(null)
      return
    }
    let vigente = true
    const temporizador = setTimeout(() => {
      obtenerWhatIf(idVenta, fecha)
        .then((datos) => vigente && setResultado(datos))
        .catch(() => vigente && setResultado(null))
    }, 120)
    return () => {
      vigente = false
      clearTimeout(temporizador)
    }
  }, [idVenta, fecha])

  return { resultado, fecha, consultar }
}
