import type { Location } from '../types'

export class GeolocationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'GeolocationError'
  }
}

export function getDeviceLocation(timeoutMs = 15000): Promise<Location> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new GeolocationError('Geolocation not supported'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          lat: Math.round(pos.coords.latitude * 1000) / 1000,
          lon: Math.round(pos.coords.longitude * 1000) / 1000,
        }),
      (err) => reject(new GeolocationError(err.message)),
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 60000 },
    )
  })
}
